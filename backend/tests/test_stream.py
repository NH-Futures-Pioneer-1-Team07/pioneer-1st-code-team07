import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config import Settings
from app.main import create_app
from app.nh.hub import MAX_CODES, HubFull, MarketHub, Subscriber, serialize
from app.nh.realtime import State
from app.nh.realtime_data import BookLevel, Feed, OrderBook, Reconnected, SubscriptionFailed, Trade

CODE = "A116B000"


class FakeRealtime:
    def __init__(self, on_event, on_state):
        self.on_event, self.on_state = on_event, on_state
        self.subscribed: list[Feed] = []
        self.started = self.stopped = False

    async def subscribe(self, feed):
        self.subscribed.append(feed)

    async def unsubscribe(self, feed):
        self.subscribed.remove(feed)

    def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True


def trade(code=CODE, price=243000.0):
    return Trade(code, "100000", price, 3, 1200, 242000.0, 244000.0, 241000.0, 243500.0, 243000.0, "1")


def book(code=CODE):
    return OrderBook(code, "100001", 120, 110, [BookLevel(243500.0, 10, 243000.0, 12)])


class Env:
    def __init__(self, tmp_path, **settings_kwargs):
        self.connections: list[FakeRealtime] = []

        def factory(on_event, on_state):
            connection = FakeRealtime(on_event, on_state)
            self.connections.append(connection)
            return connection

        values = {"trading_env": "mock", "nh_app_key": "k", "nh_app_secret": "s",
                  "strategies_dir": tmp_path / "s", "runs_dir": tmp_path / "r"}
        self.app = create_app(Settings(**{**values, **settings_kwargs}))
        self.app.state.hub = MarketHub(Settings(**{**values, **settings_kwargs}), realtime_factory=factory)
        self.client = TestClient(self.app)

    @property
    def connection(self) -> FakeRealtime:
        return self.connections[0]

    def emit(self, client, event):
        """NH 실시간 이벤트를 서버의 이벤트 루프에서 일으킨다."""
        client.portal.call(lambda: self.connection.on_event(event))

    def state(self, client, state, detail=""):
        client.portal.call(lambda: self.connection.on_state(state, detail))


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def test_연결하면_현재_상태를_보내고_체결과_호가를_변환해_전달한다(env):
    with env.client as client, client.websocket_connect(f"/ws/market?code={CODE}") as ws:
        assert ws.receive_json() == {"type": "state", "state": "connecting", "detail": ""}
        assert env.connection.started
        assert env.connection.subscribed == [Feed("KA", CODE), Feed("KB", CODE)]

        env.emit(client, trade())
        env.emit(client, book())

        assert ws.receive_json() == {
            "type": "trade", "code": CODE, "time": "100000", "price": 243000.0, "quantity": 3, "cum_volume": 1200,
            "open": 242000.0, "high": 244000.0, "low": 241000.0, "best_ask": 243500.0, "best_bid": 243000.0,
            "is_trade": True,
        }
        assert ws.receive_json() == {
            "type": "orderbook", "code": CODE, "time": "100001", "total_ask_quantity": 120, "total_bid_quantity": 110,
            "levels": [{"ask_price": 243500.0, "ask_quantity": 10, "bid_price": 243000.0, "bid_quantity": 12}],
        }


def test_연결_상태_변화를_전달한다(env):
    with env.client as client, client.websocket_connect(f"/ws/market?code={CODE}") as ws:
        ws.receive_json()
        env.state(client, State.LIVE, "")
        env.state(client, "reconnecting", "5초 뒤 다시 연결")

        assert ws.receive_json() == {"type": "state", "state": "live", "detail": ""}
        assert ws.receive_json() == {"type": "state", "state": "reconnecting", "detail": "5초 뒤 다시 연결"}

    with env.client as client, client.websocket_connect(f"/ws/market?code={CODE}") as ws:
        assert ws.receive_json()["state"] == "reconnecting"  # 새 화면은 현재 상태를 먼저 받는다


def test_같은_종목을_여러_화면이_보면_구독을_공유하고_마지막이_떠나면_해제한다(env):
    with env.client as client:
        with client.websocket_connect(f"/ws/market?code={CODE}") as first:
            first.receive_json()
            with client.websocket_connect(f"/ws/market?code={CODE}") as second:
                second.receive_json()
                assert len(env.connections) == 1
                assert env.connection.subscribed == [Feed("KA", CODE), Feed("KB", CODE)]

                env.emit(client, trade())
                assert first.receive_json()["type"] == "trade" and second.receive_json()["type"] == "trade"
            # 둘째가 떠나도 첫째가 남아 있으니 구독은 그대로
            env.emit(client, trade(price=244000.0))
            assert first.receive_json()["price"] == 244000.0
            assert env.connection.subscribed == [Feed("KA", CODE), Feed("KB", CODE)]
    # 마지막 화면이 떠난 뒤
    assert env.connection.subscribed == []


def test_다른_종목을_보는_화면에는_그_종목의_메시지만_간다(env):
    with env.client as client:
        with client.websocket_connect(f"/ws/market?code={CODE}") as mine, client.websocket_connect("/ws/market?code=A0169000") as other:
            mine.receive_json()
            other.receive_json()

            env.emit(client, trade(code="A0169000", price=1.0))
            env.emit(client, trade(code=CODE, price=2.0))

            assert other.receive_json()["price"] == 1.0
            assert mine.receive_json()["price"] == 2.0


def test_재연결과_구독_거절을_전달하고_거절은_해당_종목_화면에만_간다(env):
    with env.client as client:
        with client.websocket_connect(f"/ws/market?code={CODE}") as mine, client.websocket_connect("/ws/market?code=A0169000") as other:
            mine.receive_json()
            other.receive_json()

            env.emit(client, SubscriptionFailed(Feed("KA", CODE), "RT_FAIL", "미신청 거래소"))
            env.emit(client, Reconnected())

            assert mine.receive_json() == {
                "type": "subscription_failed", "code": CODE, "reason_code": "RT_FAIL", "message": "미신청 거래소"}
            assert mine.receive_json() == {"type": "reconnected"}
            assert other.receive_json() == {"type": "reconnected"}  # 다른 종목 화면은 거절을 받지 않았다


def test_어느_종목의_거절인지_모르면_모든_화면에_알린다(env):
    with env.client as client, client.websocket_connect(f"/ws/market?code={CODE}") as ws:
        ws.receive_json()

        env.emit(client, SubscriptionFailed(None, "EST06", "구독 상한"))

        assert ws.receive_json() == {"type": "subscription_failed", "code": None, "reason_code": "EST06", "message": "구독 상한"}


def test_종목이_다섯_개째면_거부한다(env):
    codes = [f"A00000{n}" for n in range(MAX_CODES)]
    with env.client as client:
        sockets = [client.websocket_connect(f"/ws/market?code={code}") for code in codes]
        opened = [socket.__enter__() for socket in sockets]
        try:
            for ws in opened:
                ws.receive_json()
            with client.websocket_connect("/ws/market?code=A000009") as extra:
                with pytest.raises(WebSocketDisconnect) as closed:
                    extra.receive_json()
            assert closed.value.code == 4429
            # 이미 보고 있는 종목은 계속 붙을 수 있다
            with client.websocket_connect(f"/ws/market?code={codes[0]}") as again:
                assert again.receive_json()["type"] == "state"
        finally:
            for socket in sockets:
                socket.__exit__(None, None, None)


def test_잘못된_종목코드는_닫힘_코드로_거부하고_NH를_부르지_않는다(env):
    with env.client as client:
        for bad in ("", "A1", "../x"):
            with client.websocket_connect(f"/ws/market?code={bad}") as ws:
                with pytest.raises(WebSocketDisconnect) as closed:
                    ws.receive_json()
            assert closed.value.code == 4422
    assert env.connections == []


def test_인증_정보가_없으면_닫힘_코드로_거부한다(tmp_path):
    env = Env(tmp_path, nh_app_key=None, nh_app_secret=None)
    with env.client as client, client.websocket_connect(f"/ws/market?code={CODE}") as ws:
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
    assert closed.value.code == 4503
    assert env.connections == []


def test_서버를_끄면_NH_실시간_연결을_정리한다(env):
    with env.client as client, client.websocket_connect(f"/ws/market?code={CODE}") as ws:
        ws.receive_json()
        connection = env.connection
    assert connection.stopped


def test_느린_화면은_오래된_메시지부터_버리고_다른_화면을_막지_않는다():
    subscriber = Subscriber(CODE)

    for n in range(300):
        subscriber.push({"type": "trade", "n": n})

    assert subscriber.queue.qsize() == 256
    assert subscriber.dropped == 44
    assert subscriber.queue.get_nowait()["n"] == 44  # 가장 오래된 44개가 버려졌다


def test_알_수_없는_이벤트는_보내지_않는다():
    assert serialize(object()) is None
