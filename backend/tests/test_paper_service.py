import shutil
import time as clock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.nh.realtime_data import OrderEvent, Trade
from app.nh.account import OrderStatus
from app.runners import paper
from app.runners.paper_service import PaperService
from strategy_base.models import Side
from app.runners.clearing import ClearConfig
from tests.test_clearing import FakeGateway
from tests.test_clearing import order as gateway_order
from tests.test_clearing import position as gateway_position
from tests.test_paper_session import CODE, FakeBroker, account_position, record
from tests.test_registry import make_folder

STRATEGY = """
from strategy_base.interface import BaseStrategy
from strategy_base.models import IntentKind, OrderIntent, Side, StrategyOutput


class Strategy(BaseStrategy):
    def on_bar(self, ctx):
        return StrategyOutput()

    def on_price(self, ctx):
        if not ctx.lots and not ctx.open_orders and not ctx.state.get("bought"):
            order = OrderIntent(Side.BUY, 1, IntentKind.ENTRY, "e1", "테스트")
            return StrategyOutput(orders=[order], state={"bought": True})
        return StrategyOutput()
"""
MANIFEST = {
    "name": "모의매매 테스트 전략",
    "description": "테스트용",
    "instruments": [{"name": "삼성전자선물", "code": CODE, "multiplier": 10}],
    "bar": {"unit": "minute", "size": 3},
    "parameters": {"quantity": {"default": 1, "description": "수량"}},
}
FAST = {"poll_interval": 0.05, "reconcile_interval": 0.05, "stop_reconcile_interval": 0.05, "flatten_retry": 0.05,
        "stop_timeout": 5.0, "price_throttle": 0.0}


class FakeRealtime:
    def __init__(self, on_event, on_state, hub):
        self.on_event, self.on_state, self.hub = on_event, on_state, hub
        self.feeds, self.started, self.stopped = [], False, False
        hub.append(self)

    async def subscribe(self, feed):
        self.feeds.append(feed)

    def start(self):
        self.started = True
        self.on_state("live", "")

    async def stop(self):
        self.stopped = True


class Env:
    def __init__(self, tmp_path, monkeypatch, manifest=MANIFEST, **settings_kwargs):
        monkeypatch.setattr(paper, "TICK_SECONDS", 0.02)
        self.broker = FakeBroker()
        self.hub: list[FakeRealtime] = []
        strategies = tmp_path / "strategies"
        strategies.mkdir(parents=True, exist_ok=True)
        if (strategies / "week02_stub").exists():
            shutil.rmtree(strategies / "week02_stub")
        make_folder(strategies, "week02_stub", manifest=manifest, strategy=STRATEGY)
        values = {"trading_env": "mock", "nh_app_key": "k", "nh_app_secret": "s",
                  "strategies_dir": strategies, "runs_dir": tmp_path / "runs"}
        self.app = create_app(Settings(**{**values, **settings_kwargs}))
        self.service: PaperService = self.app.state.trading
        self.service._components = lambda code, minutes: (
            self.broker, lambda on_event, on_state: FakeRealtime(on_event, on_state, self.hub))
        self.service._overrides = FAST
        self.gateway = FakeGateway()
        self.service._gateway = self.gateway
        self.service._clear_config = ClearConfig(
            poll=0.02, cancel_timeout=2.0, stop_timeout=5.0, flatten_timeout=2.0, flatten_retry=0.05
        )
        self.client = TestClient(self.app)

    def start(self, **body):
        return self.client.post("/api/trading/start", json={"strategy_id": "week02_stub", **body})

    def emit(self, event):
        """실시간 이벤트를 세션 루프로 넘긴다."""
        self.service._loop.call_soon_threadsafe(self.service._session.post, event)

    def wait(self, condition, timeout=5.0):
        end = clock.time() + timeout
        while clock.time() < end:
            if condition():
                return
            clock.sleep(0.01)
        raise AssertionError("조건이 시간 안에 충족되지 않았습니다")

    def status(self):
        return self.client.get("/api/trading/status").json()

    def detail(self, started):
        return self.client.get(f"/api/runs/{started['strategy_id']}/paper/{started['run_id']}").json()

    def journal(self, started, kind):
        url = f"/api/runs/{started['strategy_id']}/paper/{started['run_id']}/journal"
        return self.client.get(url, params={"kind": kind, "limit": 1000}).json()["items"]


def trade(price):
    return Trade(CODE, "100000", price, 1, 100, price, price, price, price, price, "1")


@pytest.fixture
def env(tmp_path, monkeypatch):
    return Env(tmp_path, monkeypatch)


def test_시작하면_식별자를_돌려주고_실시간을_구독하며_상태가_운용_중이다(env):
    response = env.start()

    assert response.status_code == 202
    started = response.json()
    assert started["mode"] == "paper"
    env.wait(lambda: env.hub and env.hub[0].started)
    assert [(f.action_code, f.symbol) for f in env.hub[0].feeds] == [("KA", CODE), ("O1", None)]
    env.wait(lambda: env.status().get("feed") == "live")
    status = env.status()
    assert status["phase"] == "running" and status["run"] == started
    assert status["strategy"] == "모의매매 테스트 전략" and status["instrument"] == CODE
    meta = env.detail(started)["meta"]
    assert meta["status"] == "running" and meta["mode"] == "paper"
    assert meta["instrument"]["code"] == CODE
    events = env.journal(started, "event")
    assert events[0]["text"] == "운용 전 계좌" and events[0]["deposit"]["cash"] == 1e8

    env.client.post("/api/trading/stop")
    env.service.join(10)


def test_시작_전에는_대기_상태다(env):
    assert env.status() == {"phase": "idle", "run": None, "last_run": None}


def test_실시간_체결이_전략을_거쳐_주문과_체결_기록이_된다(env):
    started = env.start().json()
    env.wait(lambda: env.hub and env.hub[0].started)

    env.emit(trade(243000.0))
    env.wait(lambda: env.broker.place_calls)
    assert env.broker.place_calls == [(Side.BUY, 1)]

    order_no = "0000000001"
    env.emit(OrderEvent(order_no, "", CODE, Side.BUY, OrderStatus.FILLED, 1, 1, 0, 243000.0, 1, 0, "", "", ""))
    env.broker.positions_list = [account_position(Side.BUY, 1)]
    env.wait(lambda: env.status().get("lots"))
    status = env.status()
    assert status["lots"][0]["quantity"] == 1
    assert status["pnl"]["fee_estimated"] is True

    assert [o["status"] for o in env.journal(started, "order")] == ["submitted"]
    assert env.journal(started, "fill")[0]["price"] == 243000.0

    env.client.post("/api/trading/stop")
    env.wait(lambda: env.broker.place_calls[1:])
    assert env.broker.place_calls[1] == (Side.SELL, 1)
    env.emit(OrderEvent("0000000002", "", CODE, Side.SELL, OrderStatus.FILLED, 1, 1, 0, 243500.0, 1, 0, "", "", ""))
    env.broker.positions_list = []
    env.service.join(10)

    detail = env.detail(started)
    assert detail["meta"]["status"] == "completed"
    assert detail["result"]["trade_count"] == 1
    assert detail["result"]["gross_pnl"] == pytest.approx(500 * 10)
    assert env.hub[0].stopped
    assert env.status()["phase"] == "idle"
    assert env.status()["last_run"]["status"] == "completed"


def test_정상_종료는_보유가_없으면_바로_끝난다(env):
    started = env.start().json()
    env.wait(lambda: env.hub and env.hub[0].started)

    stop = env.client.post("/api/trading/stop")
    env.service.join(10)

    assert stop.status_code == 202 and stop.json() == {"phase": "stopping"}
    assert env.detail(started)["meta"]["status"] == "completed"
    assert env.hub[0].stopped


def test_운용_중에_다시_시작하면_409다(env):
    env.start()

    second = env.start()

    assert second.status_code == 409
    env.client.post("/api/trading/stop")
    env.service.join(10)
    assert env.start().status_code == 202
    env.client.post("/api/trading/stop")
    env.service.join(10)


def test_운용_중이_아닐_때_종료하면_409다(env):
    assert env.client.post("/api/trading/stop").status_code == 409


def test_그_종목에_기존_포지션이_있으면_시작을_거부하고_기록을_만들지_않는다(env):
    env.broker.positions_list = [account_position(Side.BUY, 2)]

    response = env.start()

    assert response.status_code == 409 and "전체 정리" in response.json()["detail"]
    assert env.client.get("/api/runs").json() == []
    assert env.status()["phase"] == "idle"


def test_그_종목에_미체결_주문이_있으면_시작을_거부한다(env):
    env.broker.open_list = [record(Side.BUY, "1", 1)]

    assert env.start().status_code == 409


def test_다른_종목의_포지션은_시작을_막지_않는다(env):
    other = account_position(Side.BUY, 2)
    env.broker.positions_list = [type(other)("OTHER", "다른", other.side, 2, 2, 1, 1, 0, 0)]

    assert env.start().status_code == 202
    env.client.post("/api/trading/stop")
    env.service.join(10)


def test_NH_조회가_실패하면_502이고_기록을_만들지_않는다(env):
    env.broker.failing = {"positions"}

    response = env.start()

    assert response.status_code == 502
    assert env.client.get("/api/runs").json() == []


@pytest.mark.parametrize(
    "body, status",
    [({"strategy_id": "nope"}, 404), ({"params": {"unknown": 1}}, 422)],
)
def test_잘못된_요청은_거부한다(env, body, status):
    response = env.client.post("/api/trading/start", json={"strategy_id": "week02_stub", **body})

    assert response.status_code == status


def test_실전_환경에서는_거부한다(tmp_path, monkeypatch):
    env = Env(tmp_path, monkeypatch, trading_env="real")

    response = env.start()

    assert response.status_code == 422 and "모의 환경" in response.json()["detail"]


def test_인증_정보가_없으면_503이다(tmp_path, monkeypatch):
    env = Env(tmp_path, monkeypatch, nh_app_key=None, nh_app_secret=None)

    assert env.start().status_code == 503


def test_종목_정보가_모자라거나_일봉_전략은_거부한다(tmp_path, monkeypatch):
    no_code = {**MANIFEST, "instruments": [{"name": "삼성전자선물", "code": CODE}]}
    assert Env(tmp_path, monkeypatch, manifest=no_code).start().status_code == 422

    daily = {**MANIFEST, "bar": {"unit": "day", "size": 1}}
    assert Env(tmp_path / "b", monkeypatch, manifest=daily).start().status_code == 422


def test_전략_파라미터를_덮어쓸_수_있고_기록에_남는다(env):
    started = env.start(params={"quantity": 3}).json()

    assert env.detail(started)["meta"]["params"] == {"quantity": 3}
    env.client.post("/api/trading/stop")
    env.service.join(10)


def test_서버가_멈춰_실행_중으로_남은_모의매매는_다음_시작_때_중단으로_표시된다(tmp_path, monkeypatch):
    first = Env(tmp_path, monkeypatch)
    started = first.start().json()
    first.wait(lambda: first.hub and first.hub[0].started)
    # 서버가 갑자기 꺼진 것처럼 상태를 바꾸지 않고 새 앱을 띄운다
    second = Env(tmp_path, monkeypatch)

    assert second.detail(started)["meta"]["status"] == "interrupted"
    first.client.post("/api/trading/stop")
    first.service.join(10)


# ---- 계좌 조회와 전체 정리 ----


def test_계좌_조회는_운용_중이_아니어도_예탁금_포지션_미체결을_돌려준다(env):
    env.gateway.positions_list = [gateway_position(CODE, Side.BUY, 3)]
    env.gateway.orders_list = [gateway_order("1", CODE, Side.SELL, 2)]

    response = env.client.get("/api/trading/account")

    assert response.status_code == 200
    body = response.json()
    assert body["deposit"]["cash"] == 1e8 and body["deposit"]["order_available_total"] == 9e7
    assert body["positions"][0]["code"] == CODE and body["positions"][0]["quantity"] == 3
    assert body["open_orders"][0]["order_no"] == "1"


def test_계좌_조회가_실패하면_502다(env):
    env.gateway.fail = {"deposit"}

    assert env.client.get("/api/trading/account").status_code == 502


def test_계좌_조회와_정리는_인증_정보가_없으면_503이고_실전_환경에서는_422다(tmp_path, monkeypatch):
    no_keys = Env(tmp_path, monkeypatch, nh_app_key=None, nh_app_secret=None)
    real = Env(tmp_path / "r", monkeypatch, trading_env="real")

    assert no_keys.client.get("/api/trading/account").status_code == 503
    assert no_keys.client.post("/api/trading/clear").status_code == 503
    assert real.client.get("/api/trading/account").status_code == 422
    assert real.client.post("/api/trading/clear").status_code == 422
    assert real.gateway.cancel_calls == [] and real.gateway.close_calls == []


def test_운용이_없어도_전체_정리가_미체결을_취소하고_포지션을_청산한다(env):
    env.gateway.orders_list = [gateway_order("1", "A0169000", Side.BUY, 4)]
    env.gateway.positions_list = [gateway_position(CODE, Side.BUY, 5), gateway_position("A0169000", Side.SELL, 2)]

    response = env.client.post("/api/trading/clear")
    env.service.join(10)

    assert response.status_code == 202 and response.json() == {"phase": "clearing"}
    status = env.status()
    assert status["phase"] == "idle"
    result = status["clear"]["result"]
    assert status["clear"]["state"] == "done" and result["status"] == "completed"
    assert result["cancelled"] == 1
    assert env.gateway.close_calls == [(CODE, Side.SELL, 5), ("A0169000", Side.BUY, 2)]
    assert env.gateway.positions_list == [] and env.gateway.orders_list == []


def test_정리_중에는_상태가_clearing이고_다시_정리하면_409다(env):
    import threading

    release = threading.Event()
    original = env.gateway.open_orders

    def blocking():
        release.wait(5)
        return original()

    env.gateway.open_orders = blocking

    first = env.client.post("/api/trading/clear")
    env.wait(lambda: env.status().get("clear", {}).get("step") == "cancel")
    second = env.client.post("/api/trading/clear")
    status = env.status()
    release.set()
    env.service.join(10)

    assert first.status_code == 202 and second.status_code == 409
    assert status["phase"] == "clearing" and status["clear"]["state"] == "running"
    assert env.status()["clear"]["state"] == "done"


def test_운용_중에_정리하면_전략을_끝내고_계좌_전체를_정리하며_기록에_남긴다(env):
    started = env.start().json()
    env.wait(lambda: env.hub and env.hub[0].started)
    env.gateway.orders_list = [gateway_order("9", "A0169000", Side.BUY, 4)]
    env.gateway.positions_list = [gateway_position("A0169000", Side.SELL, 2)]

    response = env.client.post("/api/trading/clear")
    env.service.join(15)

    assert response.status_code == 202
    detail = env.detail(started)
    assert detail["meta"]["status"] == "completed"
    texts = [e["text"] for e in env.journal(started, "event")]
    assert any("계좌 전체 정리" in t and "미체결" in t for t in texts)
    assert any(t == "계좌 전체 정리 결과" for t in texts)
    assert env.status()["clear"]["result"]["status"] == "completed"
    assert env.gateway.close_calls == [("A0169000", Side.BUY, 2)]
    assert env.broker.place_calls == []  # 운용은 보유가 없어 주문을 내지 않았다
    assert env.hub[0].stopped


def test_정리가_시작되면_운용은_더_이상_전략을_호출하지_않는다(env):
    env.start()
    env.wait(lambda: env.hub and env.hub[0].started)
    env.emit(trade(243000.0))
    env.wait(lambda: env.broker.place_calls)
    placed = len(env.broker.place_calls)
    env.gateway.orders_list = [gateway_order("9", "A0169000", Side.BUY, 4)]

    env.client.post("/api/trading/clear")
    env.service.join(15)

    assert len(env.broker.place_calls) == placed
