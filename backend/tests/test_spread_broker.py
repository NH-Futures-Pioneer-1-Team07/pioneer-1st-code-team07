from datetime import date, datetime, timedelta

import pytest

from app.nh.domestic.account import OrderableQuantity, OrderRecord, OrderStatus, Position
from app.nh.domestic.quotes import Quote
from app.nh.realtime_data import Trade
from app.runners.spread_broker import SpreadBroker, SpreadPriceMux
from strategy_base.manifest import SpreadLeg
from strategy_base.models import Bar, Side

LEGS = [SpreadLeg(code="ZFZ26", ratio=3), SpreadLeg(code="ZNZ26", ratio=-2)]
START = datetime(2026, 11, 11, 10, 0, 0)


class FakeLeg:
    """한 종목의 가짜 NH 호출. 주문은 접수만 하고 체결은 테스트가 `fill`로 시킨다."""

    environment = "mock"

    def __init__(self, code, price):
        self.code, self.price = code, price
        self.records: list[OrderRecord] = []
        self.rows: list[Position] = []
        self.cancelled: list[tuple] = []
        self.placed: list[tuple] = []
        self.orderable_quantity = 72

    def place(self, side, quantity):
        number = f"{len(self.records) + 1:010d}"
        self.placed.append((side, quantity))
        self.records.append(
            OrderRecord(number, "0", self.code, side, OrderStatus.CONFIRMED, "new", quantity, 0.0, 0, None, quantity, "100000", "")
        )
        return number

    def fill(self, number, quantity=None, price=None):
        index = next(i for i, r in enumerate(self.records) if r.order_no == number)
        row = self.records[index]
        quantity = row.quantity if quantity is None else quantity
        price = self.price if price is None else price
        status = OrderStatus.FILLED if quantity >= row.quantity else OrderStatus.PARTIAL
        self.records[index] = OrderRecord(
            row.order_no, "0", self.code, row.side, status, "new", row.quantity, 0.0, quantity, price, row.quantity - quantity, row.received_time, ""
        )
        sign = 1 if row.side == Side.BUY else -1
        held = sum(p.quantity * (1 if p.side == Side.BUY else -1) for p in self.rows) + sign * quantity
        self.rows = [Position(self.code, "", Side.BUY if held > 0 else Side.SELL, abs(held), abs(held), price, price, 0.0, None)] if held else []

    def cancel(self, side, quantity, order_no):
        self.cancelled.append((side, quantity, order_no))
        index = next(i for i, r in enumerate(self.records) if r.order_no == order_no)
        row = self.records[index]
        self.records[index] = OrderRecord(
            row.order_no, "0", self.code, row.side, OrderStatus.AUTO_CANCELLED, "new", row.quantity, 0.0, row.filled_quantity,
            row.filled_price, 0, row.received_time, ""
        )
        return "C" + order_no

    def orders(self):
        return list(self.records)

    def open_orders(self):
        return [r for r in self.records if r.status in (OrderStatus.ACCEPTED, OrderStatus.CONFIRMED, OrderStatus.PARTIAL)]

    def positions(self):
        return list(self.rows)

    def orderable(self, side, price):
        return OrderableQuantity(self.orderable_quantity, 0, self.orderable_quantity, 1000.0)

    def fetch_quote(self):
        return Quote(self.code, self.price, None)

    def fetch_bars(self, day):
        start = datetime(day.year, day.month, day.day, 9, 0)
        return [Bar(start + timedelta(minutes=5 * n), self.price, self.price, self.price, 10, self.price) for n in range(2)]

    def deposit(self):
        return "deposit"


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now


@pytest.fixture
def setup():
    zf, zn, clock = FakeLeg("ZFZ26", 104.0), FakeLeg("ZNZ26", 106.0), Clock()
    broker = SpreadBroker([zf, zn], LEGS, "ZFZ26-ZNZ26", name="스프레드", entry_confirm_seconds=30, clock=clock)
    return broker, zf, zn, clock


def test_스프레드_매수는_ZF_매수와_ZN_매도_두_주문으로_나간다(setup):
    broker, zf, zn, _ = setup

    number = broker.place(Side.BUY, 2)

    assert number == "S000001"
    assert zf.placed == [(Side.BUY, 6)]
    assert zn.placed == [(Side.SELL, 4)]


def test_스프레드_매도는_반대_방향으로_나간다(setup):
    broker, zf, zn, _ = setup
    broker.place(Side.SELL, 1)
    assert zf.placed == [(Side.SELL, 3)]
    assert zn.placed == [(Side.BUY, 2)]


def test_두_종목이_모두_체결되면_세트_수와_스프레드_체결가를_돌려준다(setup):
    broker, zf, zn, _ = setup
    number = broker.place(Side.BUY, 1)
    zf.fill("0000000001", price=104.5)
    zn.fill("0000000001", price=106.0)

    record = broker.orders()[0]

    assert record.order_no == number and record.code == "ZFZ26-ZNZ26"
    assert record.status == OrderStatus.FILLED
    assert record.filled_quantity == 1
    assert record.filled_price == pytest.approx(3 * 104.5 - 2 * 106.0)
    assert broker.open_orders() == []
    [position] = broker.positions()
    assert (position.code, position.side, position.quantity) == ("ZFZ26-ZNZ26", Side.BUY, 1)
    assert position.avg_price == pytest.approx(3 * 104.5 - 2 * 106.0)


def test_한쪽만_체결된_동안은_세트로_세지_않는다(setup):
    broker, zf, zn, _ = setup
    broker.place(Side.BUY, 1)
    zf.fill("0000000001")

    [record] = broker.open_orders()

    assert record.status == OrderStatus.CONFIRMED
    assert record.filled_quantity == 0
    codes = [p.code for p in broker.positions()]
    assert codes == ["ZFZ26"]


def test_진입이_제한_시간_안에_체결되지_않으면_취소하고_체결된_종목을_되돌린다(setup):
    broker, zf, zn, clock = setup
    broker.place(Side.BUY, 1)
    zf.fill("0000000001")

    clock.now = START + timedelta(seconds=31)
    broker.open_orders()  # 제한 시간이 지나 ZN 주문을 취소
    assert zn.cancelled == [(Side.SELL, 2, "0000000001")]
    assert zf.cancelled == []

    broker.open_orders()  # 취소가 확인되어 ZF 체결분을 반대 매매
    assert zf.placed[-1] == (Side.SELL, 3)

    zf.fill("0000000002")
    assert broker.open_orders() == []
    assert broker.positions() == []
    assert broker.orders()[0].status == OrderStatus.AUTO_CANCELLED


def test_제한_시간_전에는_취소하지_않는다(setup):
    broker, zf, zn, clock = setup
    broker.place(Side.BUY, 1)
    zf.fill("0000000001")
    clock.now = START + timedelta(seconds=29)

    broker.open_orders()

    assert zn.cancelled == [] and zf.cancelled == []


def test_청산_주문은_제한_시간이_지나도_취소하지_않는다(setup):
    broker, zf, zn, clock = setup
    broker.place(Side.BUY, 1)
    zf.fill("0000000001")
    zn.fill("0000000001")
    broker.open_orders()
    broker.place(Side.SELL, 1)  # 청산
    zf.fill("0000000002")
    clock.now = START + timedelta(seconds=300)

    broker.open_orders()

    assert zn.cancelled == []


def test_주문가능수량은_두_종목에서_만들_수_있는_세트_수다(setup):
    broker, zf, zn, _ = setup
    zf.orderable_quantity, zn.orderable_quantity = 72, 48
    assert broker.orderable(Side.BUY, 100.0).order_quantity == 24
    zn.orderable_quantity = 5
    assert broker.orderable(Side.BUY, 100.0).order_quantity == 2


def test_스프레드_주문이_아닌_종목_미체결은_그대로_돌려준다(setup):
    broker, zf, zn, _ = setup
    zf.place(Side.BUY, 1)  # 다른 곳에서 낸 주문

    [record] = broker.open_orders()

    assert record.code == "ZFZ26"


def test_현재가와_분봉은_스프레드로_합쳐_돌려준다(setup):
    broker, *_ = setup
    assert broker.fetch_quote().last_price == pytest.approx(3 * 104.0 - 2 * 106.0)
    bars = broker.fetch_bars(date(2026, 11, 11))
    assert [b.close for b in bars] == [100.0, 100.0]
    assert broker.notional_price() == pytest.approx(3 * 104.0 + 2 * 106.0)


def test_두번째_종목_주문이_거절되면_첫_주문을_취소하고_오류를_알린다(setup):
    broker, zf, zn, _ = setup

    from app.nh.errors import NHError

    class Rejected(NHError):
        pass

    def reject(side, quantity):
        raise Rejected("거절")

    zn.place = reject
    with pytest.raises(Rejected):
        broker.place(Side.BUY, 1)

    assert zf.cancelled == [(Side.BUY, 3, "0000000001")]


def trade(code, price, tick="1"):
    return Trade(code, "100000", price, 1, None, None, None, None, None, None, tick)


def test_실시간_체결은_두_종목이_모두_들어온_뒤에_스프레드_체결로_전달한다():
    posted = []
    mux = SpreadPriceMux("ZFZ26-ZNZ26", LEGS, posted.append)

    mux(trade("ZFZ26", 104.0))
    assert posted == []
    mux(trade("ZNZ26", 106.0))
    mux(trade("ZFZ26", 104.5))
    mux("연결 상태")

    assert [getattr(item, "price", item) for item in posted] == [100.0, 101.5, "연결 상태"]
    assert posted[0].code == "ZFZ26-ZNZ26" and posted[0].is_trade


# ---- 모의매매 서비스 ----


def test_운용_종료_일시는_스프레드_전략에서_필수이고_지금보다_뒤여야_한다(tmp_path):
    from app.config import Settings
    from app.main import create_app
    from app.runners.paper_service import TradingRejected

    app = create_app(Settings(trading_env="mock", strategies_dir=tmp_path, runs_dir=tmp_path / "runs"))
    service = app.state.trading
    service._clock = lambda: START

    with pytest.raises(TradingRejected, match="필요"):
        service._parse_end_at(None, required=True)
    assert service._parse_end_at(None, required=False) is None
    with pytest.raises(TradingRejected, match="형식"):
        service._parse_end_at("내일", required=True)
    with pytest.raises(TradingRejected, match="뒤"):
        service._parse_end_at("2026-11-11T09:00", required=True)
    assert service._parse_end_at("2026-11-12T18:00", required=True) == datetime(2026, 11, 12, 18, 0)
    assert service._parse_end_at("2026-11-12T18:00+09:00", required=True) == datetime(2026, 11, 12, 18, 0)


def test_시작_전_계좌_확인은_두_종목의_기존_미체결도_거부한다(setup):
    from app.runners.paper_service import PaperService, TradingRejected

    broker, zf, zn, _ = setup
    zf.place(Side.BUY, 1)  # 계좌에 남은 주문
    service = PaperService.__new__(PaperService)

    with pytest.raises(TradingRejected, match="기존 포지션이나 미체결"):
        service._check_account(broker, "ZFZ26-ZNZ26", ["ZFZ26", "ZNZ26"])
