import asyncio
import json
from datetime import date, datetime, timedelta

import pytest

from app.nh.account import Deposit, OrderableQuantity, OrderRecord, OrderStatus, Position
from app.nh.errors import BusinessError, TransportError
from app.nh.orders import OrderBlocked
from app.nh.quotes import Quote
from app.nh.realtime_data import OrderEvent, Reconnected, SubscriptionFailed, Trade
from app.records.store import KST, RunStore
from app.runners import paper
from app.runners.paper import PaperConfig, PaperSession, StateChange
from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Bar,
    CancelRequest,
    IntentKind,
    OrderIntent,
    Side,
    StrategyOutput,
)

CODE = "A116B000"
START = datetime(2026, 10, 28, 10, 0, 0)
CONFIG = PaperConfig(code=CODE, name="스텁", multiplier=10, minutes=3, fee_rate=0.001)


def at(seconds=0, minutes=0):
    return START + timedelta(minutes=minutes, seconds=seconds)


def bar(minute, close=243000, volume=100):
    start = datetime(2026, 10, 28, 10, 0) + timedelta(minutes=minute)
    return Bar(start, close + 500, close - 500, close, volume, close)


def intent(side, quantity, kind, entry_id, valid_bars=None):
    return OrderIntent(side, quantity, kind, entry_id, "테스트", valid_bars=valid_bars)


def trade_event(price, code=CODE, tick="1"):
    return Trade(code, "100000", price, 1, 100, price, price, price, price, price, tick)


def order_event(order_no, status, filled=None, price=None, quantity=5, execution=None, original=""):
    return OrderEvent(order_no, original, CODE, Side.BUY, status, quantity, filled, 0, price, execution, None, "", "", "")


class Script(BaseStrategy):
    def __init__(self, on_bar=None, on_price=None):
        super().__init__({})
        self.bar_hook, self.price_hook = on_bar, on_price
        self.bar_calls, self.price_calls = [], []

    def on_bar(self, ctx):
        self.bar_calls.append(ctx)
        return self.bar_hook(ctx) if self.bar_hook else StrategyOutput()

    def on_price(self, ctx):
        self.price_calls.append(ctx)
        return self.price_hook(ctx) if self.price_hook else StrategyOutput()


def record(side, order_no, status, quantity=5, filled=0, price=None, kind="new", received="100010"):
    return OrderRecord(order_no, "", CODE, side, status, kind, quantity, 0, filled, price,
                       quantity - filled, received, "")


def account_position(side, quantity):
    return Position(CODE, "삼성전자선물", side, quantity, quantity, 243000, 243000, 0, 0)


class FakeBroker:
    environment = "mock"

    def __init__(self):
        self.bars: list[Bar] = []
        self.quote = Quote(CODE, 243000.0, date(2026, 11, 12))
        self.positions_list: list[Position] = []
        self.open_list: list[OrderRecord] = []
        self.history: list[OrderRecord] = []
        self.orderable_quantity = 100
        self.place_results: list = []
        self.place_calls: list = []
        self.cancel_calls: list = []
        self.failing: set[str] = set()
        self.deposit_now = Deposit(1e8, 1e8, 1e8, 1e8, 0, 0, 5000, 5000, 350.0)
        self.next_no = 1

    def _check(self, name):
        if name in self.failing:
            raise TransportError(f"{name} 실패")

    def fetch_bars(self, day):
        self._check("fetch_bars")
        return list(self.bars)

    def fetch_quote(self):
        self._check("fetch_quote")
        return self.quote

    def positions(self):
        self._check("positions")
        return list(self.positions_list)

    def open_orders(self):
        self._check("open_orders")
        return list(self.open_list)

    def orders(self):
        self._check("orders")
        return list(self.history)

    def deposit(self):
        self._check("deposit")
        return self.deposit_now

    def orderable(self, side, price):
        self._check("orderable")
        return OrderableQuantity(self.orderable_quantity, 0, self.orderable_quantity, 1e8)

    def place(self, side, quantity):
        self.place_calls.append((side, quantity))
        if self.place_results:
            result = self.place_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        number = f"{self.next_no:010d}"
        self.next_no += 1
        return number

    def cancel(self, side, quantity, order_no):
        self.cancel_calls.append((side, quantity, order_no))
        return "C" + order_no


class Harness:
    def __init__(self, tmp_path, strategy=None, config=CONFIG):
        self.broker = FakeBroker()
        self.strategy = strategy or Script()
        self.now = START
        self.recorder = RunStore(tmp_path).start_run(
            strategy_id="stub", strategy_name="스텁", mode="paper",
            instrument={"name": "삼성전자선물", "code": CODE}, params={},
            started_at=datetime(2026, 10, 28, 10, 0, tzinfo=KST),
        )
        self.session = PaperSession(
            self.strategy, config, self.broker, self.recorder,
            started_at=START, last_trading_day=date(2026, 11, 12),
            deposit_before={"cash": 1e8, "total_assets": 1e8, "fee": 100.0, "futures_realized_pnl": 0, "total_pnl": 0},
            clock=lambda: self.now,
        )
        self.session.feed_state = "live"

    async def at(self, seconds=0, minutes=0):
        self.now = at(seconds, minutes)
        await self.session.tick(self.now)

    async def send(self, item):
        await self.session.handle(item)

    def journal(self, kind=None):
        lines = []
        for path in sorted((self.recorder.folder / "journal").glob("*.jsonl")):
            lines += [json.loads(text) for text in path.read_text(encoding="utf-8").splitlines()]
        return [line for line in lines if kind is None or line["kind"] == kind]

    def orders(self, status):
        return [o for o in self.journal("order") if o["status"] == status]


def run(scenario):
    asyncio.run(scenario())


def buy_once(entry_id="e1", quantity=5, valid_bars=None):
    state = {"done": False}

    def hook(ctx):
        if state["done"]:
            return StrategyOutput()
        state["done"] = True
        return StrategyOutput(orders=[intent(Side.BUY, quantity, IntentKind.ENTRY, entry_id, valid_bars)])

    return hook


async def fill_entry(h, quantity=5, price=243000.0, order_no="0000000001"):
    """진입 주문을 내고 전량 체결시킨다."""
    h.broker.bars = [bar(0)]
    await h.at(minutes=3, seconds=10)
    await h.send(order_event(order_no, OrderStatus.FILLED, filled=quantity, price=price, quantity=quantity))
    h.broker.positions_list = [account_position(Side.BUY, quantity)]


# ---- 분봉 ----


def test_마감된_분봉을_시작_뒤의_것만_한_번씩_순서대로_전달한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        h.broker.bars = [bar(-3), bar(0), bar(3)]  # 09:57은 시작 전, 10:03은 아직 마감 전

        await h.at(minutes=3, seconds=10)
        await h.at(minutes=3, seconds=20)
        assert [c.bars[-1].time for c in h.strategy.bar_calls] == [datetime(2026, 10, 28, 10, 0)]
        assert h.strategy.bar_calls[0].now == datetime(2026, 10, 28, 10, 3)

        await h.at(minutes=6, seconds=10)
        await h.at(minutes=6, seconds=20)
        assert [c.bars[-1].time.minute for c in h.strategy.bar_calls] == [0, 3]
        assert [len(c.bars) for c in h.strategy.bar_calls] == [1, 2]

    run(scenario)


def test_전일_봉은_전달하지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        yesterday = Bar(datetime(2026, 10, 27, 15, 0), 1, 1, 1, 1, 1)
        h.broker.bars = [yesterday, bar(0)]

        await h.at(minutes=3, seconds=10)

        assert [c.bars[-1].time for c in h.strategy.bar_calls] == [bar(0).time]
        assert yesterday not in h.strategy.bar_calls[0].bars

    run(scenario)


def test_전략에는_최종거래일과_진입분_정보가_전달된다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        await fill_entry(h)
        h.broker.bars = [bar(0), bar(3)]
        await h.at(minutes=6, seconds=10)

        ctx = h.strategy.bar_calls[-1]
        assert ctx.last_trading_day == date(2026, 11, 12)
        assert [(l.entry_id, l.side, l.quantity, l.entry_price) for l in ctx.lots] == [("e1", Side.BUY, 5, 243000.0)]
        assert ctx.open_orders == []

    run(scenario)


# ---- 가격 ----


def test_실시간_체결_가격을_전략에_전달하고_틱이_아닌_것은_무시한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(trade_event(243500.0))
        await h.send(trade_event(243600.0, tick="0"))
        await h.send(trade_event(243700.0, code="OTHER"))

        assert [c.price for c in h.strategy.price_calls] == [243500.0]
        assert h.session.last_price == 243500.0

    run(scenario)


def test_같은_가격이_1초_안에_반복되면_한_번만_전달한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(trade_event(243500.0))
        await h.send(trade_event(243500.0))
        h.now = at(seconds=2)
        await h.send(trade_event(243500.0))
        await h.send(trade_event(243000.0))

        assert [c.price for c in h.strategy.price_calls] == [243500.0, 243500.0, 243000.0]

    run(scenario)


def test_실시간이_끊기면_현재가_조회로_가격을_전달한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(StateChange("live"))
        await h.at(seconds=6)
        assert h.strategy.price_calls == []

        await h.send(StateChange("reconnecting", "5초 뒤"))
        h.broker.quote = Quote(CODE, 244000.0, date(2026, 11, 12))
        await h.at(seconds=12)

        assert [c.price for c in h.strategy.price_calls] == [244000.0]

    run(scenario)


# ---- 주문 ----


def test_전략의_진입_의도가_시장가_주문으로_나가고_체결로_원장이_갱신된다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once(valid_bars=2)))
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)

        assert h.broker.place_calls == [(Side.BUY, 5)]
        [submitted] = h.orders("submitted")
        assert (submitted["order_no"], submitted["quantity"], submitted["planned_quantity"]) == ("0000000001", 5, 5)

        await h.send(order_event("0000000001", OrderStatus.PARTIAL, filled=2, price=243000.0))
        assert [(l.quantity) for l in h.session.ledger.lots()] == [2]
        await h.send(order_event("0000000001", OrderStatus.FILLED, filled=5, price=243500.0))
        assert [l.quantity for l in h.session.ledger.lots()] == [5]

        fills = h.journal("fill")
        assert [(f["quantity"], f["price"]) for f in fills] == [(2, 243000.0), (3, 243500.0)]
        assert fills[0]["fee"] == pytest.approx(243000 * 10 * 2 * 0.001)
        assert fills[0]["fee_estimated"] is True and fills[0]["source"] == "notification"
        assert h.session.tracked["0000000001"].status == "filled"

    run(scenario)


def test_진행_중인_주문은_전략에_미체결_주문으로_전달된다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0), bar(3)]
        await h.at(minutes=3, seconds=10)
        await h.send(order_event("0000000001", OrderStatus.PARTIAL, filled=2, price=243000.0))
        await h.at(minutes=6, seconds=10)

        [pending] = h.strategy.bar_calls[-1].open_orders
        assert (pending.order_id, pending.quantity, pending.filled_quantity, pending.kind) == (
            "0000000001", 5, 2, IntentKind.ENTRY)

    run(scenario)


def test_같은_체결_알림이_다시_와도_두_번_반영하지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)

        for _ in range(3):
            await h.send(order_event("0000000001", OrderStatus.PARTIAL, filled=2, price=243000.0))

        assert [l.quantity for l in h.session.ledger.lots()] == [2]
        assert len(h.journal("fill")) == 1

    run(scenario)


def test_주문가능수량보다_많으면_가능한_수량만_주문하고_둘_다_기록한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once(quantity=5)))
        h.broker.orderable_quantity = 3
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)

        assert h.broker.place_calls == [(Side.BUY, 3)]
        [submitted] = h.orders("submitted")
        assert (submitted["quantity"], submitted["planned_quantity"]) == (3, 5)

    run(scenario)


def test_주문가능수량이_0이면_주문하지_않고_사유를_기록한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        h.broker.orderable_quantity = 0
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)

        assert h.broker.place_calls == []
        [skipped] = h.orders("skipped")
        assert skipped["reason"] == "주문가능수량이 0"

    run(scenario)


def test_주문이_거부되면_사유를_기록하고_다시_보내지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        h.broker.place_results = [BusinessError("/order", "40123", "증거금 부족", {})]
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)
        await h.at(minutes=3, seconds=30)
        await h.at(minutes=4)

        assert len(h.broker.place_calls) == 1
        [rejected] = h.orders("rejected")
        assert (rejected["code"], rejected["message"]) == ("40123", "증거금 부족")
        assert h.session.tracked == {} and h.session.unknown == []

    run(scenario)


def test_시간_초과된_주문은_다시_보내지_않고_확인될_때까지_신규_진입을_막는다(tmp_path):
    async def scenario():
        strategy = Script(
            on_bar=lambda ctx: StrategyOutput(orders=[intent(Side.BUY, 5, IntentKind.ENTRY, f"e{len(ctx.bars)}")])
        )
        h = Harness(tmp_path, strategy)
        h.broker.place_results = [TransportError("시간 초과")]
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0), bar(3)]
        await h.at(minutes=3, seconds=10)
        assert len(h.session.unknown) == 1
        assert h.orders("unknown")

        await h.at(minutes=6, seconds=10)  # 두 번째 봉의 진입 의도는 차단된다

        assert len(h.broker.place_calls) == 1
        assert h.orders("blocked") and "확인하지 못함" in h.orders("blocked")[0]["reason"]
        assert [o.order_id for o in h.strategy.bar_calls[-1].open_orders] == ["unknown-1"]

    run(scenario)


def test_처리_여부를_몰랐던_주문이_주문_내역에_있으면_이어받는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        h.broker.place_results = [TransportError("시간 초과")]
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)
        h.broker.history = [record(Side.BUY, "0000000077", 6, filled=5, price=243000.0, received="100315")]
        h.broker.positions_list = [account_position(Side.BUY, 5)]

        await h.at(minutes=3, seconds=25)  # 대조 시각

        assert h.session.unknown == []
        assert "0000000077" in h.session.tracked
        assert [l.quantity for l in h.session.ledger.lots()] == [5]
        assert h.session.entry_blocks(h.now) == []

    run(scenario)


def test_주문_내역에서_끝내_못_찾으면_접수되지_않은_것으로_보고_차단을_푼다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        h.broker.place_results = [TransportError("시간 초과")]
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)

        for seconds in (14, 18, 22):
            await h.at(minutes=3, seconds=seconds)

        assert h.session.unknown == []
        assert h.session.entry_blocks(h.now) == []

    run(scenario)


def test_이미_청산_주문이_나간_수량은_다시_청산하지_않는다(tmp_path):
    async def scenario():
        exits = {"n": 0}

        def hook(ctx):
            if ctx.lots and exits["n"] < 2:
                exits["n"] += 1
                return StrategyOutput(orders=[intent(Side.SELL, 5, IntentKind.EXIT, "e1")])
            return StrategyOutput()

        h = Harness(tmp_path, Script(on_bar=buy_once(), on_price=hook))
        await h.send(trade_event(243000.0))
        await fill_entry(h)
        h.broker.place_calls.clear()

        await h.send(trade_event(243500.0))
        h.now = at(minutes=3, seconds=20)
        await h.send(trade_event(244000.0))

        assert h.broker.place_calls == [(Side.SELL, 5)]
        assert h.orders("skipped")[-1]["reason"] == "이미 청산 주문이 나간 수량"

    run(scenario)


def test_없는_진입분을_청산하려_하면_무시하고_경고한다(tmp_path):
    async def scenario():
        h = Harness(
            tmp_path,
            Script(on_price=lambda ctx: StrategyOutput(orders=[intent(Side.SELL, 1, IntentKind.EXIT, "ghost")])),
        )
        await h.send(trade_event(243000.0))

        assert h.broker.place_calls == []
        assert any(e["level"] == "warning" for e in h.journal("event"))

    run(scenario)


def test_전략이_취소를_요청하면_주문을_취소한다(tmp_path):
    async def scenario():
        state = {"n": 0}

        def hook(ctx):
            state["n"] += 1
            if state["n"] == 1:
                return StrategyOutput(orders=[intent(Side.BUY, 5, IntentKind.ENTRY, "e1")])
            return StrategyOutput(cancels=[CancelRequest("0000000001", "전략 요청")])

        h = Harness(tmp_path, Script(on_bar=hook))
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0), bar(3)]
        await h.at(minutes=3, seconds=10)
        await h.at(minutes=6, seconds=10)

        assert h.broker.cancel_calls == [(Side.BUY, 5, "0000000001")]
        assert h.orders("cancel_requested")

    run(scenario)


def test_주문_유효_시한이_지나면_남은_수량을_한_번만_취소한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once(valid_bars=1)))
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)
        await h.send(order_event("0000000001", OrderStatus.PARTIAL, filled=2, price=243000.0))
        h.broker.open_list = [record(Side.BUY, "0000000001", 4, quantity=5, filled=2)]
        h.broker.positions_list = [account_position(Side.BUY, 2)]

        await h.at(minutes=5, seconds=59)
        assert h.broker.cancel_calls == []
        await h.at(minutes=6, seconds=1)
        await h.at(minutes=6, seconds=5)

        assert h.broker.cancel_calls == [(Side.BUY, 3, "0000000001")]

    run(scenario)


def test_체결_알림을_놓쳐도_주문_내역으로_원장을_맞춘다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)
        h.broker.history = [record(Side.BUY, "0000000001", 6, filled=5, price=243000.0)]
        h.broker.positions_list = [account_position(Side.BUY, 5)]

        await h.at(minutes=3, seconds=20)

        assert [l.quantity for l in h.session.ledger.lots()] == [5]
        assert h.journal("fill")[0]["source"] == "history"
        assert h.session.tracked["0000000001"].status == "filled"

    run(scenario)


def test_다른_주문의_알림은_경고만_남긴다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(order_event("9999", OrderStatus.FILLED, filled=1, price=243000.0))

        assert [e for e in h.journal("event") if e["level"] == "warning"]
        assert h.session.ledger.lots() == []

    run(scenario)


# ---- 안전 규칙 ----


def test_계좌와_원장이_두_번_연속_어긋나면_신규_진입을_막고_청산은_허용한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        h.broker.positions_list = [account_position(Side.BUY, 2)]
        await h.send(trade_event(243000.0))
        await h.at(seconds=10)
        assert h.session.mismatch is None  # 한 번은 일시적일 수 있다
        await h.at(seconds=20)
        assert "어긋남" in (h.session.mismatch or "")
        assert any("어긋남" in reason for reason in h.session.entry_blocks(h.now))

        h.broker.positions_list = []
        await h.at(seconds=30)
        assert h.session.mismatch is None and h.session.entry_blocks(h.now) == []

    run(scenario)


def test_차단_중에도_청산_주문은_나간다(tmp_path):
    async def scenario():
        sell = {"on": False}

        def hook(ctx):
            if sell["on"] and ctx.lots:
                return StrategyOutput(orders=[intent(Side.SELL, 5, IntentKind.EXIT, "e1")])
            return StrategyOutput()

        h = Harness(tmp_path, Script(on_bar=buy_once(), on_price=hook))
        await h.send(trade_event(243000.0))
        await fill_entry(h)
        h.broker.positions_list = []  # 계좌와 원장이 어긋남
        await h.at(minutes=3, seconds=30)
        await h.at(minutes=3, seconds=40)
        assert h.session.entry_blocks(h.now)
        h.broker.place_calls.clear()

        sell["on"] = True
        h.now = at(minutes=4)
        await h.send(trade_event(244000.0))

        assert h.broker.place_calls == [(Side.SELL, 5)]

    run(scenario)


def test_계좌에_알_수_없는_미체결_주문이_있으면_차단한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        h.broker.open_list = [record(Side.BUY, "7777", 1)]
        await h.send(trade_event(243000.0))
        await h.at(seconds=10)
        await h.at(seconds=20)

        assert "알 수 없는 미체결" in (h.session.mismatch or "")

    run(scenario)


def test_분봉_조회가_30초_넘게_실패하면_신규_진입을_막고_회복하면_푼다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(trade_event(243000.0))
        h.broker.failing = {"fetch_bars"}
        await h.at(seconds=10)
        assert h.session.entry_blocks(h.now) == []
        await h.at(seconds=40)
        assert "분봉 조회가 계속 실패함" in h.session.entry_blocks(h.now)

        h.broker.failing = set()
        await h.at(seconds=46)
        assert h.session.entry_blocks(h.now) == []
        assert [e for e in h.journal("event") if e["level"] == "warning"]

    run(scenario)


def test_같은_조회_오류는_기록을_반복하지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        h.broker.failing = {"fetch_bars"}
        for seconds in (6, 12, 18, 24):
            await h.at(seconds=seconds)

        warnings = [e for e in h.journal("event") if e["text"] == "분봉 조회에 실패했습니다"]
        assert len(warnings) == 1

    run(scenario)


def test_실시간도_현재가_조회도_안_되면_시세를_받지_못한_것으로_막는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(StateChange("reconnecting"))
        h.broker.failing = {"fetch_quote"}
        await h.at(seconds=10)
        await h.at(seconds=40)

        assert "시세를 받지 못함" in h.session.entry_blocks(h.now)

    run(scenario)


def test_시세와_분봉이_없는_상태에서_진입_의도는_차단된다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(StateChange("reconnecting"))
        h.broker.failing = {"fetch_quote"}
        await h.at(seconds=40)  # 시세 끊긴 지 오래됨
        h.broker.failing = set()
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=40)

        assert h.broker.place_calls == []
        assert h.orders("blocked")

    run(scenario)


def test_실시간_재연결과_구독_거절은_기록한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(SubscriptionFailed(None, "RT_FAIL", "거절"))
        await h.send(Reconnected())

        texts = [e["text"] for e in h.journal("event")]
        assert any("구독이 거절" in t for t in texts) and any("다시 연결" in t for t in texts)

    run(scenario)


# ---- 종료 ----


def test_정상_종료는_미체결_취소_보유_청산_확인_순서로_진행한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        await fill_entry(h)
        # 미체결 주문 하나를 더 걸어 둔다
        h.strategy.bar_hook = lambda ctx: StrategyOutput(orders=[intent(Side.BUY, 2, IntentKind.ENTRY, "e2")])
        h.broker.bars = [bar(0), bar(3)]
        await h.at(minutes=6, seconds=10)
        assert h.session.tracked["0000000002"].status == "open"
        h.broker.open_list = [record(Side.BUY, "0000000002", 1, quantity=2)]
        h.broker.place_calls.clear()
        bar_calls = len(h.strategy.bar_calls)
        price_calls = len(h.strategy.price_calls)

        await h.send(paper.StopRequest())
        await h.at(minutes=6, seconds=12)
        assert h.session.phase == paper.STOPPING
        assert h.broker.cancel_calls == [(Side.BUY, 2, "0000000002")]
        assert h.broker.place_calls == []  # 취소가 확인되기 전에는 청산하지 않는다

        h.broker.open_list = []  # 취소됨
        await h.at(minutes=6, seconds=14)
        await h.at(minutes=6, seconds=16)
        assert h.broker.place_calls == [(Side.SELL, 5)]
        assert h.orders("submitted")[-1]["reason"] == "운용 종료 청산"

        await h.send(order_event("0000000003", OrderStatus.FILLED, filled=5, price=244000.0, quantity=5))
        h.broker.positions_list = []
        await h.at(minutes=6, seconds=20)
        await h.at(minutes=6, seconds=24)

        assert h.session.final_status == "completed" and h.session.done.is_set()
        meta = json.loads((h.recorder.folder / "meta.json").read_text(encoding="utf-8"))
        result = json.loads((h.recorder.folder / "result.json").read_text(encoding="utf-8"))
        assert meta["status"] == "completed"
        assert result["trade_count"] == 1 and result["fee_estimated"] is True
        assert result["gross_pnl"] == pytest.approx((244000 - 243000) * 5 * 10)
        assert result["account"]["fee_change"] == pytest.approx(250.0)
        assert result["account"]["realized_pnl_change"] == pytest.approx(5000)
        assert len(h.strategy.bar_calls) == bar_calls and len(h.strategy.price_calls) == price_calls

    run(scenario)


def test_종료를_시작하면_신규_진입_의도를_받지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_price=lambda ctx: StrategyOutput(orders=[intent(Side.BUY, 1, IntentKind.ENTRY, "x")])))
        await h.send(paper.StopRequest())

        await h.send(trade_event(243000.0))

        assert h.broker.place_calls == []
        assert h.strategy.price_calls == []

    run(scenario)


def test_보유도_미체결도_없으면_바로_종료한다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        await h.send(paper.StopRequest())
        await h.at(seconds=1)

        assert h.session.final_status == "completed"

    run(scenario)


def test_청산이_체결되지_않으면_시간이_지난_뒤_오류로_끝낸다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        await fill_entry(h)
        await h.send(paper.StopRequest())
        for seconds in range(0, 100, 5):
            await h.at(minutes=4, seconds=seconds)
            if h.session.done.is_set():
                break

        assert h.session.final_status == "error"
        result = json.loads((h.recorder.folder / "result.json").read_text(encoding="utf-8"))
        assert result["open_lots"] == [{"entry_id": "e1", "side": "buy", "quantity": 5}]
        meta = json.loads((h.recorder.folder / "meta.json").read_text(encoding="utf-8"))
        assert meta["status"] == "error"
        assert len(h.broker.place_calls) >= 2  # 청산을 되풀이해서 시도했다

    run(scenario)


def test_종료_뒤에도_계좌에_포지션이_남아_있으면_완료로_끝내지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        h.broker.positions_list = [account_position(Side.SELL, 1)]
        await h.send(paper.StopRequest())
        for seconds in range(0, 100, 5):
            await h.at(seconds=seconds)
            if h.session.done.is_set():
                break

        assert h.session.final_status == "error"

    run(scenario)


def test_전략이_예외를_내면_오류로_끝나고_보유가_남을_수_있다고_알린다(tmp_path):
    async def scenario():
        def boom(ctx):
            raise RuntimeError("전략 오류")

        h = Harness(tmp_path, Script(on_price=boom))
        h.session.post(trade_event(243000.0))
        task = asyncio.create_task(h.session.run())
        await asyncio.wait_for(h.session.done.wait(), 5)
        await task

        assert h.session.final_status == "error"
        events = h.journal("event")
        assert any("RuntimeError" in e["text"] and "계좌를 확인" in e["text"] for e in events)

    run(scenario)


def test_실전_환경에서_주문이_막히면_오류로_끝난다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_price=lambda ctx: StrategyOutput(orders=[intent(Side.BUY, 1, IntentKind.ENTRY, "x")])))
        h.broker.place_results = [OrderBlocked("모의 환경에서만")]
        h.session.post(trade_event(243000.0))
        task = asyncio.create_task(h.session.run())
        await asyncio.wait_for(h.session.done.wait(), 5)
        await task

        assert h.session.final_status == "error"

    run(scenario)


def test_실행_루프가_종료_요청을_처리하고_끝난다(tmp_path, monkeypatch):
    monkeypatch.setattr(paper, "TICK_SECONDS", 0.01)

    async def scenario():
        h = Harness(tmp_path)
        h.now = datetime.now()
        h.session.clock = lambda: datetime.now()
        h.session.started_at = datetime.now()
        h.session.next_poll = h.session.next_quote = h.session.started_at
        h.session.next_reconcile = h.session.started_at
        task = asyncio.create_task(h.session.run())
        h.session.begin_stop()
        await asyncio.wait_for(h.session.done.wait(), 5)
        await task

        assert h.session.final_status == "completed"
        assert h.session.snapshot["phase"] == paper.STOPPED

    run(scenario)


def test_상태_스냅샷에_단계_가격_손익_차단_사유가_있다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        await fill_entry(h, price=243000.0)
        await h.send(StateChange("live"))
        await h.send(trade_event(244000.0))
        h.session.publish()

        snap = h.session.snapshot
        assert snap["phase"] == "running" and snap["feed"] == "live"
        assert snap["last_price"] == 244000.0
        assert snap["pnl"]["unrealized_pnl"] == pytest.approx((244000 - 243000) * 5 * 10)
        assert snap["pnl"]["fee"] == pytest.approx(243000 * 10 * 5 * 0.001)
        assert snap["lots"] == [{"entry_id": "e1", "side": "buy", "quantity": 5, "entry_price": 243000.0}]
        assert snap["entry_blocks"] == []

    run(scenario)


# ---- 계좌 전체 정리 ----


def test_정리를_시작하면_전략_판단과_신규_주문을_멈춘다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        calls = len(h.strategy.price_calls)

        await h.send(paper.PauseRequest())
        await h.send(trade_event(243500.0))
        h.broker.bars = [bar(0)]
        await h.at(minutes=3, seconds=10)

        assert h.session.phase == paper.CLEARING
        assert len(h.strategy.price_calls) == calls and h.strategy.bar_calls == []
        assert h.broker.place_calls == []
        assert "계좌 전체 정리 중" in h.session.entry_blocks(h.now)
        assert h.session.snapshot == {} or h.session.snapshot["phase"] != "running"

    run(scenario)


def test_정리_중_종료하면_계좌_전체_확인_없이_자기_보유만_청산하고_끝낸다(tmp_path):
    async def scenario():
        h = Harness(tmp_path, Script(on_bar=buy_once()))
        await h.send(trade_event(243000.0))
        await fill_entry(h)
        h.broker.positions_list = [account_position(Side.BUY, 5), account_position(Side.SELL, 9)]  # 계좌에는 다른 보유도 있음
        await h.send(paper.PauseRequest())
        await h.send(paper.StopRequest(account_wide=True))
        h.broker.place_calls.clear()

        await h.at(minutes=4)
        assert h.broker.place_calls == [(Side.SELL, 5)]  # 자기 진입분만 청산
        await h.send(order_event("0000000002", OrderStatus.FILLED, filled=5, price=244000.0, quantity=5))
        await h.at(minutes=4, seconds=3)

        assert h.session.final_status == "completed"

    run(scenario)


def test_일반_종료는_계좌에_다른_보유가_남아_있으면_완료로_끝내지_않는다(tmp_path):
    async def scenario():
        h = Harness(tmp_path)
        h.broker.positions_list = [account_position(Side.BUY, 1)]
        await h.send(paper.StopRequest(account_wide=False))
        for seconds in range(0, 100, 5):
            await h.at(seconds=seconds)
            if h.session.done.is_set():
                break

        assert h.session.final_status == "error"

    run(scenario)
