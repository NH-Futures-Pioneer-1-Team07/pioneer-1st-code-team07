
from app.nh.domestic.account import Deposit, OrderRecord, OrderStatus, Position
from app.nh.errors import TransportError
from app.runners.clearing import ClearConfig, account_view, run_clear
from strategy_base.models import Side

CONFIG = ClearConfig(poll=1.0, cancel_timeout=10.0, stop_timeout=10.0, flatten_timeout=20.0, flatten_retry=5.0)


def position(code, side, quantity, closable=None):
    return Position(code, f"{code} 이름", side, quantity, closable if closable is not None else quantity,
                    243000.0, 243500.0, 5000.0, 0.5)


def order(order_no, code, side, quantity=5, filled=0):
    return OrderRecord(order_no, "", code, side, OrderStatus.ACCEPTED, "new", quantity, 0.0, filled, None,
                       quantity - filled, "100000", "")


class FakeGateway:
    environment = "mock"

    def __init__(self):
        self.positions_list: list[Position] = []
        self.orders_list: list[OrderRecord] = []
        self.cancel_calls, self.close_calls = [], []
        self.fill_on_close = True
        self.fail: set[str] = set()
        self.on_cancel = None
        self.deposit_value = Deposit(1e8, 1.01e8, 9e7, 8.5e7, 1e6, 7e5, 5000.0, 5000.0, 100.0)
        self.close_numbers = 0

    def _check(self, name):
        if name in self.fail:
            raise TransportError(f"{name} 실패")

    def deposit(self):
        self._check("deposit")
        return self.deposit_value

    def positions(self):
        return list(self.positions_list)

    def open_orders(self):
        return list(self.orders_list)

    def cancel(self, code, side, quantity, order_no):
        self._check("cancel")
        self.cancel_calls.append((code, side, quantity, order_no))
        self.orders_list = [o for o in self.orders_list if o.order_no != order_no]
        if self.on_cancel:
            self.on_cancel(self)
        return "C" + order_no

    def close(self, code, side, quantity):
        self._check("close")
        self.close_calls.append((code, side, quantity))
        self.close_numbers += 1
        if self.fill_on_close:
            self.positions_list = [p for p in self.positions_list if p.code != code]
        else:
            self.orders_list.append(order(f"close-{self.close_numbers}", code, side, quantity))
        return f"close-{self.close_numbers}"


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def clear(gateway, config=CONFIG, run_states=(False,), stop_calls=None):
    clock = Clock()
    steps = []
    states = list(run_states)

    def active():
        return states.pop(0) if len(states) > 1 else states[0]

    result = run_clear(
        gateway, config,
        report=lambda step, detail: steps.append(step),
        stop_run=lambda: stop_calls.append(clock.now) if stop_calls is not None else None,
        run_active=active, sleep=clock.sleep, monotonic=clock.monotonic,
    )
    return result, steps


def test_계좌에_아무것도_없으면_바로_완료다():
    result, steps = clear(FakeGateway())

    assert result["status"] == "completed"
    assert (result["open_orders"], result["positions"], result["cancelled"], result["closed"]) == ([], [], 0, [])
    assert steps == ["cancel", "stop_run", "flatten", "verify"]


def test_종목과_관계없이_모든_미체결_주문을_잔량만큼_취소한다():
    gateway = FakeGateway()
    gateway.orders_list = [order("1", "A116B000", Side.BUY, 5, filled=2), order("2", "A0169000", Side.SELL, 3)]

    result, _ = clear(gateway)

    assert gateway.cancel_calls == [("A116B000", Side.BUY, 3, "1"), ("A0169000", Side.SELL, 3, "2")]
    assert result["cancelled"] == 2 and result["status"] == "completed"


def test_취소_중에_체결된_수량도_포함해_남은_포지션을_청산한다():
    gateway = FakeGateway()
    gateway.orders_list = [order("1", "A116B000", Side.BUY, 5, filled=2)]
    gateway.on_cancel = lambda g: g.positions_list.append(position("A116B000", Side.BUY, 2))

    result, _ = clear(gateway)

    assert gateway.close_calls == [("A116B000", Side.SELL, 2)]
    assert result["status"] == "completed" and result["positions"] == []


def test_매수_보유는_매도로_매도_보유는_매수로_종목마다_청산한다():
    gateway = FakeGateway()
    gateway.positions_list = [position("A116B000", Side.BUY, 5), position("A0169000", Side.SELL, 3, closable=2)]

    result, _ = clear(gateway)

    assert gateway.close_calls == [("A116B000", Side.SELL, 5), ("A0169000", Side.BUY, 2)]
    assert result["closed"] == [
        {"code": "A116B000", "side": "sell", "quantity": 5},
        {"code": "A0169000", "side": "buy", "quantity": 2},
    ]


def test_청산_주문이_아직_체결되지_않았으면_중복으로_내지_않고_기다린다():
    gateway = FakeGateway()
    gateway.fill_on_close = False
    gateway.positions_list = [position("A116B000", Side.BUY, 5)]

    result, _ = clear(gateway)

    assert len(gateway.close_calls) == 1
    assert result["status"] == "incomplete"
    assert [p["code"] for p in result["positions"]] == ["A116B000"]
    assert [o["order_no"] for o in result["open_orders"]] == ["close-1"]
    assert any("시간 안에 끝나지 않았습니다" in p for p in result["problems"])


def test_청산_주문이_접수되지_않아_포지션이_남으면_간격을_두고_다시_낸다():
    gateway = FakeGateway()
    gateway.positions_list = [position("A116B000", Side.BUY, 5)]
    gateway.fill_on_close = False

    def drop_orders(g):
        g.orders_list = []

    original_close = gateway.close

    def close_and_lose(code, side, quantity):
        original_close(code, side, quantity)
        drop_orders(gateway)  # 주문이 접수되지 않아 미체결에도 없고 포지션도 그대로
        if len(gateway.close_calls) == 3:
            gateway.positions_list = []
        return "x"

    gateway.close = close_and_lose

    result, _ = clear(gateway)

    assert len(gateway.close_calls) == 3
    assert result["status"] == "completed"


def test_청산_주문이_실패하면_문제로_기록하고_계속한다():
    gateway = FakeGateway()
    gateway.fail = {"close"}
    gateway.positions_list = [position("A116B000", Side.BUY, 5)]

    result, _ = clear(gateway)

    assert result["status"] == "incomplete"
    assert any("청산 주문 실패" in p for p in result["problems"])
    assert len(gateway.close_calls) == 0


def test_취소가_실패하면_문제로_기록하고_이어서_정리한다():
    gateway = FakeGateway()
    gateway.fail = {"cancel"}
    gateway.orders_list = [order("1", "A116B000", Side.BUY)]
    gateway.positions_list = [position("A116B000", Side.BUY, 1)]

    result, _ = clear(gateway)

    assert any("취소 실패" in p for p in result["problems"])
    assert result["status"] == "incomplete"
    assert [o["order_no"] for o in result["open_orders"]] == ["1"]


def test_운용이_끝날_때까지_기다리고_종료는_한_번만_요청한다():
    gateway = FakeGateway()
    stops = []

    result, steps = clear(gateway, run_states=(True, True, True, False), stop_calls=stops)

    assert len(stops) == 1
    assert result["status"] == "completed"
    assert steps.index("stop_run") < steps.index("flatten")


def test_운용_종료가_시간_안에_끝나지_않아도_이어서_정리한다():
    gateway = FakeGateway()
    gateway.positions_list = [position("A116B000", Side.BUY, 1)]

    result, _ = clear(gateway, run_states=(True,))

    assert any("운용 종료가 시간 안에 끝나지 않았습니다" in p for p in result["problems"])
    assert gateway.close_calls == [("A116B000", Side.SELL, 1)]


def test_계좌_조회는_예탁금과_포지션과_미체결을_돌려주고_계좌_식별정보가_없다():
    gateway = FakeGateway()
    gateway.positions_list = [position("A116B000", Side.BUY, 5), position("A0169000", Side.SELL, 0)]
    gateway.orders_list = [order("1", "A116B000", Side.BUY, 5, filled=2)]

    view = account_view(gateway)

    assert view["deposit"]["cash"] == 1e8 and view["deposit"]["order_available_total"] == 9e7
    assert view["deposit"]["initial_margin"] == 1e6
    assert [p["code"] for p in view["positions"]] == ["A116B000"]  # 수량 0인 포지션은 뺀다
    assert view["positions"][0] == {
        "code": "A116B000", "name": "A116B000 이름", "side": "buy", "quantity": 5, "closable_quantity": 5,
        "avg_price": 243000.0, "last_price": 243500.0, "pnl": 5000.0, "pnl_rate": 0.5,
    }
    assert view["open_orders"] == [{
        "order_no": "1", "code": "A116B000", "side": "buy", "status": "accepted", "quantity": 5,
        "filled_quantity": 2, "remaining_quantity": 3, "price": 0.0, "received_time": "100000",
    }]
    assert "ac_no" not in repr(view) and "계좌" not in repr(view)
