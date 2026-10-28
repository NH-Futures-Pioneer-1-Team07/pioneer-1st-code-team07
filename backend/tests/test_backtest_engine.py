import json
from datetime import date, datetime, timedelta

import pytest

from app.records.store import KST, RunStore
from app.runners.backtest import (
    END_OF_PERIOD_REASON,
    Assumptions,
    BacktestEngine,
    daily_bars,
    infer_tick,
    price_path,
)
from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Bar,
    Context,
    Decision,
    DecisionResult,
    IntentKind,
    OrderIntent,
    Side,
    StrategyOutput,
)

DAY1 = date(2026, 10, 26)
DAY2 = date(2026, 10, 27)
NO_COST = Assumptions(fee_rate=0.0, slippage_ticks=0, multiplier=10, tick_size=500)
COSTLY = Assumptions(fee_rate=0.001, slippage_ticks=1, multiplier=10, tick_size=500)


def bar(day, hour, minute, open_, high, low, close, volume=100):
    return Bar(datetime(day.year, day.month, day.day, hour, minute), high, low, close, volume, open_)


def bars_of(day, rows, start=(9, 0)):
    """(시가, 고가, 저가, 종가) 목록으로 3분봉을 만든다."""
    first = datetime(day.year, day.month, day.day, *start)
    return [
        Bar(first + timedelta(minutes=3 * n), high, low, close, 100, open_)
        for n, (open_, high, low, close) in enumerate(rows)
    ]


def market(side, quantity, kind, entry_id, reason="테스트"):
    return OrderIntent(side=side, quantity=quantity, kind=kind, entry_id=entry_id, reason=reason)


class Script(BaseStrategy):
    """호출 기록을 남기고, 정해진 봉 마감에 주문을 낸다. `on_price`는 `price_rule`이 정한다."""

    def __init__(self, bar_orders=None, price_rule=None):
        super().__init__({})
        self.bar_orders = bar_orders or {}
        self.price_rule = price_rule
        self.bar_calls = []
        self.price_calls = []

    def on_bar(self, ctx):
        self.bar_calls.append((ctx.now, len(ctx.bars), ctx.bars[-1].time, ctx.price, list(ctx.lots)))
        orders = self.bar_orders.get(len(self.bar_calls), [])
        decisions = [Decision(ctx.now, DecisionResult.HOLD, "판단")] if orders else []
        return StrategyOutput(orders=orders, decisions=decisions)

    def on_price(self, ctx):
        self.price_calls.append((ctx.now, len(ctx.bars), ctx.price, list(ctx.lots)))
        if self.price_rule:
            return StrategyOutput(orders=self.price_rule(ctx))
        return StrategyOutput()


def engine_for(tmp_path, strategy, assumptions=NO_COST, capital=100_000_000, last_day=date(2026, 11, 12)):
    recorder = RunStore(tmp_path).start_run(
        strategy_id="stub",
        strategy_name="스텁",
        mode="backtest",
        instrument={"name": "삼성전자선물", "code": "A116B000"},
        params={},
        started_at=datetime(2026, 10, 28, 9, 0, tzinfo=KST),
    )
    engine = BacktestEngine(
        strategy, recorder, assumptions, initial_capital=capital, minutes=3, last_trading_day=last_day
    )
    return engine, recorder


def journal(recorder, kind=None):
    lines = []
    for path in sorted((recorder.folder / "journal").glob("*.jsonl")):
        lines += [json.loads(text) for text in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if kind is None or line["kind"] == kind]


# ---- 호가 단위와 가격 경로 ----


def test_분봉을_날짜별_일봉으로_합친다():
    first, second = date(2026, 10, 20), date(2026, 10, 21)
    days = {
        second: bars_of(second, [(200, 210, 190, 205)]),
        first: bars_of(first, [(100, 110, 95, 105), (105, 120, 100, 115), (115, 118, 90, 98)]),
    }

    assert daily_bars(days) == [
        {"date": "2026-10-20", "open": 100, "high": 120, "low": 90, "close": 98, "volume": 300},
        {"date": "2026-10-21", "open": 200, "high": 210, "low": 190, "close": 205, "volume": 100},
    ]


def test_일봉의_시가는_첫_봉에_시가가_없으면_종가로_대신한다():
    day = date(2026, 10, 20)
    bars = [Bar(datetime(2026, 10, 20, 9, 0), 110, 95, 105, 100)]

    assert daily_bars({day: bars})[0]["open"] == 105
    assert daily_bars({day: []}) == []


def test_호가_단위는_봉_가격_차이의_최대공약수다():
    days = {DAY1: bars_of(DAY1, [(100000, 101000, 99500, 100500), (100500, 102000, 100000, 101500)])}

    assert infer_tick(days) == 500


def test_호가_단위를_알_수_없으면_1이다():
    assert infer_tick({DAY1: bars_of(DAY1, [(100, 100, 100, 100)])}) == 1


def test_가격_경로는_보유_방향에_불리한_극단을_먼저_지난다():
    candle = bars_of(DAY1, [(100500, 101000, 100000, 100500)])[0]

    assert price_path(candle, 1, 500) == [100500, 100000, 100500, 101000, 100500]
    assert price_path(candle, -1, 500) == [100500, 101000, 100500, 100000, 100500]


def test_보유가_없으면_시가에서_가까운_극단을_먼저_지난다():
    near_high = bars_of(DAY1, [(100500, 101000, 99000, 100500)])[0]
    near_low = bars_of(DAY1, [(100500, 102000, 100000, 100500)])[0]

    assert price_path(near_high, 0, 500)[1] == 101000
    assert price_path(near_low, 0, 500)[1] == 100000


def test_가격_경로는_호가_단위씩_움직이고_시가와_종가로_끝난다():
    candle = bars_of(DAY1, [(100000, 101500, 100000, 101000)])[0]

    path = price_path(candle, 0, 500)

    assert path[0] == 100000 and path[-1] == 101000
    assert all((b - a) % 500 == 0 for a, b in zip(path, path[1:]))
    assert max(path) == 101500


# ---- 체결과 손익 ----

# 시가 체결 시나리오: 두 번째 봉 시가에 매수(체결 100500 + 슬리피지 500), 네 번째 봉 시가에 매도
ROUND_TRIP = [
    (100000, 100500, 99500, 100000),
    (100500, 101000, 100000, 100500),
    (100500, 102000, 100500, 101500),
    (102000, 102500, 101500, 102000),
    (102000, 102000, 102000, 102000),
]


def round_trip_strategy():
    return Script(
        bar_orders={
            1: [market(Side.BUY, 2, IntentKind.ENTRY, "e1")],
            3: [market(Side.SELL, 2, IntentKind.EXIT, "e1")],
        }
    )


def test_봉_마감_주문은_다음_봉_시가에_슬리피지와_수수료를_적용해_체결한다(tmp_path):
    engine, recorder = engine_for(tmp_path, round_trip_strategy(), COSTLY)

    result = engine.run({DAY1: bars_of(DAY1, ROUND_TRIP)})

    fills = journal(recorder, "fill")
    assert [(f["side"], f["quantity"], f["raw_price"], f["price"], f["source"]) for f in fills] == [
        ("buy", 2, 100500, 101000, "next_open"),
        ("sell", 2, 102000, 101500, "next_open"),
    ]
    assert fills[0]["fee"] == pytest.approx(101000 * 10 * 2 * 0.001)
    assert result["gross_pnl"] == pytest.approx((101500 - 101000) * 2 * 10)
    assert result["fee"] == pytest.approx(2020 + 2030)
    assert result["net_pnl"] == pytest.approx(10000 - 4050)
    assert result["final_equity"] == pytest.approx(100_000_000 + 5950)
    assert (result["trade_count"], result["win_count"], result["loss_count"]) == (1, 1, 0)


def test_진입에서_청산까지를_한_건의_거래로_기록한다(tmp_path):
    engine, recorder = engine_for(tmp_path, round_trip_strategy(), COSTLY)

    engine.run({DAY1: bars_of(DAY1, ROUND_TRIP)})

    [trade] = journal(recorder, "trade")
    assert (trade["entry_id"], trade["side"], trade["quantity"]) == ("e1", "buy", 2)
    assert (trade["entry_price"], trade["exit_price"]) == (101000, 101500)
    assert trade["gross_pnl"] == pytest.approx(10000)
    assert trade["fee"] == pytest.approx(4050)
    assert trade["net_pnl"] == pytest.approx(5950)


def test_최대_낙폭은_봉_종가_기준_자산의_고점에서_저점까지다(tmp_path):
    engine, _ = engine_for(tmp_path, round_trip_strategy(), COSTLY)

    result = engine.run({DAY1: bars_of(DAY1, ROUND_TRIP)})

    # 두 번째 봉 종가 100500: 평가손실 (100500 - 101000) × 2 × 10 = -10000, 진입 수수료 2020
    assert result["max_drawdown"] == pytest.approx(12020)
    assert result["max_drawdown_rate"] == pytest.approx(12020 / 100_000_000)


def test_매도_포지션의_손익은_부호가_반대다(tmp_path):
    strategy = Script(
        bar_orders={
            1: [market(Side.SELL, 1, IntentKind.ENTRY, "s1")],
            3: [market(Side.BUY, 1, IntentKind.EXIT, "s1")],
        }
    )
    engine, _ = engine_for(tmp_path, strategy)
    rows = [
        (100000, 100000, 100000, 100000),
        (100000, 100000, 100000, 100000),
        (100000, 100000, 100000, 100000),
        (99000, 99000, 99000, 99000),
        (99000, 99000, 99000, 99000),
    ]

    result = engine.run({DAY1: bars_of(DAY1, rows)})

    assert result["gross_pnl"] == pytest.approx((100000 - 99000) * 1 * 10)


def test_그날_마지막_봉에서_낸_주문은_그_봉_종가에_체결한다(tmp_path):
    strategy = Script(bar_orders={2: [market(Side.BUY, 1, IntentKind.ENTRY, "late")]})
    engine, recorder = engine_for(tmp_path, strategy)
    rows = [(100000, 100000, 100000, 100000), (100000, 100500, 100000, 100500)]

    engine.run({DAY1: bars_of(DAY1, rows)})

    [fill] = [f for f in journal(recorder, "fill") if f["source"] == "day_end"]
    assert (fill["entry_id"], fill["price"]) == ("late", 100500)


# ---- 장중 가격 판단 ----


def stop_target_rule(stop, target):
    """보유 중 가격이 손절 이하이면 매도, 목표 이상이면 매도한다."""

    def rule(ctx):
        orders = []
        for lot in ctx.lots:
            if ctx.price <= stop or ctx.price >= target:
                orders.append(market(Side.SELL, lot.quantity, IntentKind.EXIT, lot.entry_id, f"가격 {ctx.price:g}"))
        return orders

    return rule


def test_장중_가격_판단의_주문은_그_가격에_체결한다(tmp_path):
    strategy = Script(
        bar_orders={1: [market(Side.BUY, 1, IntentKind.ENTRY, "e1")]},
        price_rule=stop_target_rule(stop=100000, target=200000),
    )
    engine, recorder = engine_for(tmp_path, strategy, COSTLY)
    rows = [
        (100000, 100000, 100000, 100000),
        (100500, 101000, 100000, 100500),  # 시가 체결 뒤 저가 100000에서 손절
        (100500, 100500, 100500, 100500),
    ]

    result = engine.run({DAY1: bars_of(DAY1, rows)})

    fills = journal(recorder, "fill")
    assert (fills[0]["price"], fills[1]["source"], fills[1]["raw_price"], fills[1]["price"]) == (
        101000, "intrabar", 100000, 99500)
    assert result["gross_pnl"] == pytest.approx((99500 - 101000) * 10)
    assert result["win_count"] == 0 and result["loss_count"] == 1


def test_같은_봉에서_손절과_목표에_모두_닿으면_불리한_쪽이_먼저_적용된다(tmp_path):
    strategy = Script(
        bar_orders={1: [market(Side.BUY, 1, IntentKind.ENTRY, "e1")]},
        price_rule=stop_target_rule(stop=100000, target=101500),
    )
    engine, recorder = engine_for(tmp_path, strategy)
    rows = [
        (100000, 100000, 100000, 100000),
        (100500, 102000, 99500, 101000),  # 같은 봉 안에서 손절(100000 이하)과 목표(101500 이상)에 모두 닿음
        (101000, 101000, 101000, 101000),
    ]

    engine.run({DAY1: bars_of(DAY1, rows)})

    exits = [f for f in journal(recorder, "fill") if f["intent"] == "exit"]
    assert len(exits) == 1
    assert exits[0]["raw_price"] == 100000  # 손절


def test_숏_포지션은_가격이_올라_손절에_먼저_닿는다(tmp_path):
    def rule(ctx):
        return [
            market(Side.BUY, lot.quantity, IntentKind.EXIT, lot.entry_id)
            for lot in ctx.lots
            if ctx.price >= 101000 or ctx.price <= 99000
        ]

    strategy = Script(bar_orders={1: [market(Side.SELL, 1, IntentKind.ENTRY, "s1")]}, price_rule=rule)
    engine, recorder = engine_for(tmp_path, strategy)
    rows = [
        (100000, 100000, 100000, 100000),
        (100000, 101500, 98500, 100000),
        (100000, 100000, 100000, 100000),
    ]

    engine.run({DAY1: bars_of(DAY1, rows)})

    exits = [f for f in journal(recorder, "fill") if f["intent"] == "exit"]
    assert exits[0]["raw_price"] == 101000


# ---- 미래 봉과 호출 시각 ----


def test_전략에는_그_시점까지_마감된_당일_봉만_전달한다(tmp_path):
    strategy = Script()
    engine, _ = engine_for(tmp_path, strategy)
    day1 = bars_of(DAY1, [(1, 1, 1, 1)] * 3)
    day2 = bars_of(DAY2, [(1, 1, 1, 1)] * 2)

    engine.run({DAY1: day1, DAY2: day2})

    assert [(call[1], call[2]) for call in strategy.bar_calls] == [
        (1, day1[0].time), (2, day1[1].time), (3, day1[2].time),
        (1, day2[0].time), (2, day2[1].time),
    ]
    for _, count, price, _lots in [(c[0], c[1], c[3], c[4]) for c in strategy.bar_calls]:
        assert price is None
    # 장중 가격 호출에는 현재 봉을 뺀 마감된 봉만 간다
    assert strategy.price_calls[0][1] == 0
    assert max(call[1] for call in strategy.price_calls) == 2


def test_봉_마감_호출_시각은_봉이_끝나는_시각이고_장중_호출은_봉_안이다(tmp_path):
    strategy = Script()
    engine, _ = engine_for(tmp_path, strategy)
    candle = bars_of(DAY1, [(100000, 100500, 99500, 100000)], start=(15, 30))

    engine.run({DAY1: candle})

    assert strategy.bar_calls[0][0] == datetime(2026, 10, 26, 15, 33)
    times = [call[0] for call in strategy.price_calls]
    assert times[0] == datetime(2026, 10, 26, 15, 30)
    assert all(datetime(2026, 10, 26, 15, 30) <= t < datetime(2026, 10, 26, 15, 33) for t in times)


def test_전략_상태는_호출_사이에_이어_준다(tmp_path):
    class Counter(BaseStrategy):
        def __init__(self):
            super().__init__({})
            self.seen = []

        def on_bar(self, ctx):
            self.seen.append(ctx.state.get("n", 0))
            return StrategyOutput(state={"n": ctx.state.get("n", 0) + 1})

    strategy = Counter()
    engine, _ = engine_for(tmp_path, strategy)

    engine.run({DAY1: bars_of(DAY1, [(1, 1, 1, 1)] * 2), DAY2: bars_of(DAY2, [(1, 1, 1, 1)])})

    assert strategy.seen == [0, 1, 2]


def test_보유분은_전략의_진입분_정보로_전달한다(tmp_path):
    strategy = Script(bar_orders={1: [market(Side.BUY, 3, IntentKind.ENTRY, "e1")]})
    engine, _ = engine_for(tmp_path, strategy)

    engine.run({DAY1: bars_of(DAY1, [(100000, 100000, 100000, 100000)] * 3)})

    lots = strategy.bar_calls[2][4]
    assert [(l.entry_id, l.side, l.quantity, l.entry_price) for l in lots] == [("e1", Side.BUY, 3, 100000)]


# ---- 기간 종료와 기록 ----


def test_기간이_끝나면_남은_보유분을_마지막_봉_종가로_청산해_기록한다(tmp_path):
    strategy = Script(bar_orders={1: [market(Side.BUY, 2, IntentKind.ENTRY, "e1")]})
    engine, recorder = engine_for(tmp_path, strategy, COSTLY)
    rows = [(100000, 100000, 100000, 100000), (100000, 100000, 100000, 100000), (101000, 101500, 101000, 101500)]

    result = engine.run({DAY1: bars_of(DAY1, rows)})

    [closing] = [f for f in journal(recorder, "fill") if f["source"] == "backtest_end"]
    assert closing["reason"] == END_OF_PERIOD_REASON
    assert (closing["raw_price"], closing["price"]) == (101500, 101000)
    [trade] = journal(recorder, "trade")
    assert trade["exit_price"] == 101000
    assert engine.positions == {}
    assert result["trade_count"] == 1
    assert result["final_equity"] == pytest.approx(100_000_000 + result["net_pnl"])


def test_결과의_손익은_기록한_체결과_거래의_합과_같다(tmp_path):
    engine, recorder = engine_for(tmp_path, round_trip_strategy(), COSTLY)

    result = engine.run({DAY1: bars_of(DAY1, ROUND_TRIP)})

    trades = journal(recorder, "trade")
    fills = journal(recorder, "fill")
    assert result["net_pnl"] == pytest.approx(sum(t["net_pnl"] for t in trades))
    assert result["fee"] == pytest.approx(sum(f["fee"] for f in fills))


def test_판단_주문_체결_거래_이벤트가_기록된다(tmp_path):
    engine, recorder = engine_for(tmp_path, round_trip_strategy(), COSTLY)

    engine.run({DAY1: bars_of(DAY1, ROUND_TRIP)})

    lines = journal(recorder)
    assert {line["kind"] for line in lines} == {"decision", "order", "fill", "trade", "event"}
    assert [line["seq"] for line in lines] == sorted(line["seq"] for line in lines)
    decision = journal(recorder, "decision")[0]
    assert decision["orders"] == [{"side": "buy", "quantity": 2, "entry_id": "e1"}]
    assert journal(recorder, "order")[0]["status"] == "submitted"
    assert journal(recorder, "event")[0]["text"] == "일별 요약"


def test_자산_곡선은_하루마다_한_점이고_마지막은_최종자산이다(tmp_path):
    engine, _ = engine_for(tmp_path, round_trip_strategy(), COSTLY)

    result = engine.run({DAY1: bars_of(DAY1, ROUND_TRIP), DAY2: bars_of(DAY2, [(1, 1, 1, 1)])})

    assert len(result["equity_curve"]) == 2
    assert result["equity_curve"][-1]["equity"] == pytest.approx(result["final_equity"])


def test_진행_알림은_하루마다_간다(tmp_path):
    engine, _ = engine_for(tmp_path, Script())
    progress = []

    engine.run({DAY1: bars_of(DAY1, [(1, 1, 1, 1)]), DAY2: bars_of(DAY2, [(1, 1, 1, 1)])},
               lambda done, total: progress.append((done, total)))

    assert progress == [(1, 2), (2, 2)]


def test_없는_진입분을_청산하려_하면_무시하고_경고를_남긴다(tmp_path):
    strategy = Script(bar_orders={1: [market(Side.SELL, 1, IntentKind.EXIT, "ghost")]})
    engine, recorder = engine_for(tmp_path, strategy)

    result = engine.run({DAY1: bars_of(DAY1, [(1, 1, 1, 1)] * 3)})

    assert result["trade_count"] == 0
    assert any(e.get("level") == "warning" for e in journal(recorder, "event"))


def test_시가가_없는_봉은_거부한다(tmp_path):
    engine, _ = engine_for(tmp_path, Script())
    candle = Bar(datetime(2026, 10, 26, 9, 0), 1, 1, 1, 1)

    with pytest.raises(ValueError, match="시가"):
        engine.run({DAY1: [candle]})
