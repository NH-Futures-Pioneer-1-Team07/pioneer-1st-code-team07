import asyncio
import json
import logging

import pytest
from websockets.exceptions import ConnectionClosedError

from app.nh import realtime
from app.nh.account import OrderStatus
from app.nh.realtime import (
    MAX_SUBSCRIPTIONS,
    RealtimeConnection,
    State,
    SubscriptionLimitExceeded,
    subscribe_message,
)
from app.nh.realtime_data import (
    Feed,
    OrderBook,
    OrderEvent,
    Reconnected,
    SubscriptionFailed,
    Trade,
)
from strategy_base.models import Side

INIT_OK = {"code": "INIT", "msg": "INIT_SUCCESS"}
KA = Feed("KA", "A116B000")
KB = Feed("KB", "A116B000")
O1 = Feed("O1")


class FakeSocket:
    def __init__(self, *script):
        self.inbox: asyncio.Queue = asyncio.Queue()
        for item in script:
            self.inbox.put_nowait(item)
        self.sent: list[dict] = []
        self.closed = False

    def push(self, item):
        self.inbox.put_nowait(item)

    async def send(self, message):
        self.sent.append(json.loads(message))

    async def recv(self):
        item = await self.inbox.get()
        if isinstance(item, BaseException):
            raise item
        return item if isinstance(item, (str, bytes)) else json.dumps(item)

    async def close(self):
        self.closed = True


class FakeClient:
    base_url = "https://apidemo.futures.co.kr"

    def __init__(self):
        self.keys = 0

    def issue_websocket_key(self):
        self.keys += 1
        return f"WSKEY-{self.keys}"

    def session_token(self):
        return "SESSION-TOKEN"


class Harness:
    def __init__(self, *sockets, **kwargs):
        self.sockets = list(sockets)
        self.urls: list[str] = []
        self.events: list = []
        self.states: list = []
        self.delays: list[float] = []
        self.client = FakeClient()

        async def connect(url):
            self.urls.append(url)
            return self.sockets.pop(0) if self.sockets else FakeSocket()

        async def sleep(seconds):
            self.delays.append(seconds)
            await asyncio.sleep(0)

        self.connection = RealtimeConnection(
            self.client,
            on_event=self.events.append,
            on_state=lambda state, detail: self.states.append(state),
            connect=connect,
            sleep=sleep,
            **kwargs,
        )


async def until(predicate, timeout=2.0):
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    while not predicate():
        if loop.time() > end:
            raise AssertionError("조건이 시간 안에 충족되지 않았습니다")
        await asyncio.sleep(0.005)


def run(scenario):
    asyncio.run(scenario())


def trade_message(**extra):
    body = {"sym": "A116B000", "tick_div": "1", "exch_tm": "093012", "last_pric": "70,500", "exec_qty": "3",
            "cum_trd_qty": "1200", "open_pric": "70000", "high_pric": "70600", "low_pric": "69900",
            "ask_best_pric": "70510", "bid_best_pric": "70500", **extra}
    return {"header": {"action_code": "KA", "action_sym": "A116B000"}, "body": body}


# ---- 연결과 구독 ----


def test_접속키는_연결마다_새로_받고_세션을_초기화한_뒤_구독한다():
    async def scenario():
        socket = FakeSocket(INIT_OK)
        h = Harness(socket)
        await h.connection.subscribe(KB)
        await h.connection.subscribe(O1)
        await h.connection.subscribe(KA)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        await h.connection.stop()

        assert h.urls == ["wss://apidemo.futures.co.kr/trade/ws-stream?access_key=WSKEY-1"]
        assert socket.sent[0] == {
            "header": {"api_ver": "1", "action": "0"},
            "body": {"action_code": "session_init", "session_token": "SESSION-TOKEN"},
        }
        assert socket.sent[1:] == [
            {"header": {"api_ver": "1", "action": "A"}, "body": {"action_code": "KA", "action_sym": "A116B000"}},
            {"header": {"api_ver": "1", "action": "A"}, "body": {"action_code": "KB", "action_sym": "A116B000"}},
            {"header": {"api_ver": "1", "action": "A"}, "body": {"action_code": "O1"}},
        ]

    run(scenario)


def test_연결되면_연결됨_상태가_알려지고_중지하면_소켓을_닫는다():
    async def scenario():
        socket = FakeSocket(INIT_OK)
        h = Harness(socket)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        await h.connection.stop()

        assert h.states[:2] == [State.CONNECTING, State.LIVE]
        assert h.states[-1] == State.STOPPED
        assert socket.closed

    run(scenario)


def test_연결된_뒤_구독과_해제는_바로_보낸다():
    async def scenario():
        socket = FakeSocket(INIT_OK)
        h = Harness(socket)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)

        await h.connection.subscribe(KA)
        await h.connection.unsubscribe(KA)
        await h.connection.stop()

        assert [m["header"]["action"] for m in socket.sent[1:]] == ["A", "D"]
        assert h.connection.feeds == frozenset()

    run(scenario)


def test_같은_구독은_한_번만_걸고_스물한_번째_구독은_요청_없이_거부한다():
    async def scenario():
        socket = FakeSocket(INIT_OK)
        h = Harness(socket)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)

        await h.connection.subscribe(KA)
        await h.connection.subscribe(KA)
        for number in range(MAX_SUBSCRIPTIONS - 1):
            await h.connection.subscribe(Feed("KA", f"A{number:04d}"))
        sent = len(socket.sent)

        with pytest.raises(SubscriptionLimitExceeded):
            await h.connection.subscribe(Feed("KB", "OVER"))
        await h.connection.stop()

        assert len(h.connection.feeds) == MAX_SUBSCRIPTIONS
        assert len(socket.sent) == sent

    run(scenario)


def test_구독_종류와_종목_조합이_잘못되면_만들_수_없다():
    for args in [("KA",), ("KB", ""), ("O1", "A116B000"), ("ZZ", "A")]:
        with pytest.raises(ValueError):
            Feed(*args)


def test_구독_메시지_형식():
    assert subscribe_message(O1, "A") == {"header": {"api_ver": "1", "action": "A"}, "body": {"action_code": "O1"}}


# ---- 세션 유지 ----


def test_세션_유지_신호를_받은_그대로_되돌린다():
    async def scenario():
        socket = FakeSocket({"code": "pingpong", "seq": 1}, INIT_OK)  # 초기화 도중에도 온다
        h = Harness(socket)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        socket.push({"code": "pingpong", "seq": 2})
        await until(lambda: {"code": "pingpong", "seq": 2} in socket.sent)
        await h.connection.stop()

        assert {"code": "pingpong", "seq": 1} in socket.sent

    run(scenario)


def test_웹소켓_핑_프레임을_끄고_연결한다(monkeypatch):
    captured = {}

    async def fake_connect(url, **kwargs):
        captured.update(kwargs)
        return FakeSocket()

    monkeypatch.setattr(realtime, "ws_connect", fake_connect)

    asyncio.run(realtime._default_connect("wss://x"))

    assert captured["ping_interval"] is None


# ---- 수신 변환 ----


def test_체결_호가_주문체결_메시지를_변환해_전달한다():
    async def scenario():
        book = {"sym": "A116B000", "exch_tm": "093013", "ask_qty": "120", "bid_qty": "110",
                "ask_pric_1": "70510", "ask_qty_1": "10", "bid_pric_1": "70500", "bid_qty_1": "12",
                "ask_pric_2": "70520", "ask_qty_2": "8", "bid_pric_2": "70490", "bid_qty_2": "9"}
        order = {"ac_no": "123-45-678901", "ord_no": "0000012345", "org_ord_no": "", "sym": "A116B000",
                 "ord_sts": "4", "trd_div": "1", "ord_qty": "5", "exec_qty": "2", "ord_pric": "0",
                 "exec_pric": "70500", "per_exec_qty": "2", "rem_ord_qty": "3", "err_cd": "",
                 "rcv_tm": "093012", "exec_tm": "093013"}
        socket = FakeSocket(
            INIT_OK,
            trade_message(),
            {"header": {"action_code": "KB", "action_sym": "A116B000"}, "body": book},
            {"header": {"action_code": "O1"}, "body": order},
        )
        h = Harness(socket)
        h.connection.start()
        await until(lambda: len(h.events) == 3)
        await h.connection.stop()

        trade, orderbook, event = h.events
        assert isinstance(trade, Trade)
        assert (trade.code, trade.time, trade.price, trade.quantity, trade.cum_volume) == (
            "A116B000", "093012", 70500, 3, 1200)
        assert (trade.best_ask, trade.best_bid, trade.is_trade) == (70510, 70500, True)
        assert isinstance(orderbook, OrderBook)
        assert (orderbook.total_ask_quantity, orderbook.total_bid_quantity) == (120, 110)
        assert [(l.ask_price, l.ask_quantity, l.bid_price, l.bid_quantity) for l in orderbook.levels] == [
            (70510, 10, 70500, 12), (70520, 8, 70490, 9)]
        assert isinstance(event, OrderEvent)
        assert (event.order_no, event.side, event.status) == ("0000012345", Side.BUY, OrderStatus.PARTIAL)
        assert (event.quantity, event.filled_quantity, event.execution_quantity, event.remaining_quantity) == (
            5, 2, 2, 3)
        assert "123-45-678901" not in repr(event)

    run(scenario)


def test_체결량이_0인_틱은_체결이_아니다():
    async def scenario():
        socket = FakeSocket(INIT_OK, trade_message(tick_div="0", exec_qty="0"))
        h = Harness(socket)
        h.connection.start()
        await until(lambda: len(h.events) == 1)
        await h.connection.stop()

        assert h.events[0].is_trade is False

    run(scenario)


def test_읽을_수_없는_메시지와_모르는_실시간_구분은_건너뛴다():
    async def scenario():
        socket = FakeSocket(INIT_OK, "not json", b"\xff\xfe", [1, 2], {"header": {"action_code": "ZZ"}, "body": {}},
                            trade_message())
        h = Harness(socket)
        h.connection.start()
        await until(lambda: len(h.events) == 1)
        await h.connection.stop()

        assert isinstance(h.events[0], Trade)

    run(scenario)


# ---- 구독 거절 ----


def test_서버가_구독을_거절하면_실패한_구독과_사유를_알린다():
    async def scenario():
        refused = {"code": "RT_FAIL", "msg": "미신청 거래소",
                   "data": {"action": "A", "action_code": "KA", "action_sym": "A116B000"}}
        socket = FakeSocket(INIT_OK)
        h = Harness(socket)
        await h.connection.subscribe(KA)
        await h.connection.subscribe(KB)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        socket.push(refused)
        await until(lambda: len(h.events) == 1)
        await h.connection.stop()

        assert h.events == [SubscriptionFailed(KA, "RT_FAIL", "미신청 거래소")]

    run(scenario)


def test_거절_글에_종목만_있어도_그_구독을_찾고_알_수_없으면_구독_없이_알린다():
    async def scenario():
        socket = FakeSocket(INIT_OK)
        h = Harness(socket)
        await h.connection.subscribe(KA)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        socket.push({"rt_cd": "RT_FAIL", "message": "거절 [action_sym::A116B000]"})
        socket.push({"code": "EST06", "msg": "구독 상한"})
        await until(lambda: len(h.events) == 2)
        await h.connection.stop()

        assert h.events[0].feed == KA
        assert h.events[1] == SubscriptionFailed(None, "EST06", "구독 상한")

    run(scenario)


def test_구독_성공과_해제_답은_실패로_알리지_않는다():
    async def scenario():
        socket = FakeSocket(INIT_OK, {"code": "RT_INIT", "data": {"action": "A"}},
                            {"code": "RT_OK", "data": {"action": "D", "action_code": "KA"}})
        h = Harness(socket)
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        await asyncio.sleep(0.05)
        await h.connection.stop()

        assert h.events == []

    run(scenario)


# ---- 재연결 ----


def test_끊기면_새_접속키로_다시_연결하고_구독을_모두_다시_걸고_알린다():
    async def scenario():
        first = FakeSocket(INIT_OK, trade_message(), ConnectionClosedError(None, None))
        second = FakeSocket(INIT_OK)
        h = Harness(first, second)
        await h.connection.subscribe(KA)
        await h.connection.subscribe(O1)
        h.connection.start()
        await until(lambda: any(isinstance(e, Reconnected) for e in h.events))
        await h.connection.stop()

        assert h.urls == [
            "wss://apidemo.futures.co.kr/trade/ws-stream?access_key=WSKEY-1",
            "wss://apidemo.futures.co.kr/trade/ws-stream?access_key=WSKEY-2",
        ]
        assert [m["body"]["action_code"] for m in second.sent[1:]] == ["KA", "O1"]
        assert isinstance(h.events[0], Trade) and isinstance(h.events[-1], Reconnected)
        assert h.states.count(State.LIVE) == 2
        assert State.RECONNECTING in h.states
        assert first.closed

    run(scenario)


def test_처음_연결에서는_다시_연결됨을_알리지_않는다():
    async def scenario():
        h = Harness(FakeSocket(INIT_OK))
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        await h.connection.stop()

        assert not any(isinstance(e, Reconnected) for e in h.events)

    run(scenario)


def test_짧게_끊기는_일이_이어지면_기다리는_시간을_늘린다():
    async def scenario():
        sockets = [FakeSocket(INIT_OK, ConnectionClosedError(None, None)) for _ in range(3)]
        sockets.append(FakeSocket(INIT_OK))
        h = Harness(*sockets)
        h.connection.start()
        await until(lambda: len(h.urls) == 4 and h.connection.state == State.LIVE)
        await h.connection.stop()

        assert h.delays[:3] == [1.0, 2.0, 5.0]

    run(scenario)


def test_세션_초기화가_거부되면_다시_연결한다():
    async def scenario():
        bad = FakeSocket({"code": "INIT", "msg": "INIT_FAIL"})
        h = Harness(bad, FakeSocket(INIT_OK))
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        await h.connection.stop()

        assert len(h.urls) == 2
        assert bad.closed

    run(scenario)


def test_서버가_오래_조용하면_죽은_연결로_보고_다시_연결한다():
    async def scenario():
        h = Harness(FakeSocket(INIT_OK), FakeSocket(INIT_OK), idle_timeout=0.05)
        h.connection.start()
        await until(lambda: len(h.urls) >= 2 and h.connection.state == State.LIVE)
        await h.connection.stop()

        assert any(isinstance(e, Reconnected) for e in h.events)

    run(scenario)


def test_접속키_발급이_실패해도_다시_시도한다():
    async def scenario():
        h = Harness(FakeSocket(INIT_OK))
        calls = {"n": 0}
        original = h.client.issue_websocket_key

        def flaky():
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("발급 실패")
            return original()

        h.client.issue_websocket_key = flaky
        h.connection.start()
        await until(lambda: h.connection.state == State.LIVE)
        await h.connection.stop()

        assert calls["n"] == 2

    run(scenario)


# ---- 비밀정보 ----


def test_연결_예외에_접속키가_들어_있어도_로그에_남기지_않는다(caplog):
    async def scenario():
        h = Harness()

        async def connect(url):
            raise OSError(f"연결 실패: {url}")

        h.connection._connect = connect
        h.connection.start()
        await until(lambda: len(h.delays) >= 1)
        await h.connection.stop()

    with caplog.at_level(logging.DEBUG):
        run(scenario)

    assert "WSKEY" not in caplog.text and "SESSION-TOKEN" not in caplog.text
    assert "OSError" in caplog.text
