import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from app.nh.hub import MarketHub
from app.nh.realtime_data import Feed, Trade
from strategy_base.manifest import SpreadLeg
from tests.test_stream import Env, FakeRealtime

LEGS = [SpreadLeg(code="ZFZ26", ratio=3), SpreadLeg(code="ZNZ26", ratio=-2)]
SPREAD = "ZFZ26-ZNZ26"
URL = f"/ws/market?code={SPREAD}&market=overseas&legs=ZFZ26:3,ZNZ26:-2"


def trade(code, price):
    return Trade(code, "100000", price, 1, None, None, None, None, None, None, "1")


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path, nh_overseas_app_key="k", nh_overseas_app_secret="s")


def emit(env, client, event):
    client.portal.call(lambda: env.overseas_connections[0].on_event(event))


def test_스프레드_소켓은_두_종목_체결을_합성해_보낸다(env):
    with env.client as client, client.websocket_connect(URL) as ws:
        assert ws.receive_json()["type"] == "state"
        assert env.overseas_connections[0].subscribed == [Feed("FA", "ZFZ26"), Feed("FA", "ZNZ26")]

        emit(env, client, trade("ZFZ26", 104.0))
        emit(env, client, trade("ZNZ26", 106.0))
        message = ws.receive_json()

        assert message["type"] == "trade" and message["code"] == SPREAD
        assert message["price"] == pytest.approx(3 * 104.0 - 2 * 106.0)
        assert message["is_trade"] is True

        emit(env, client, trade("ZFZ26", 104.5))
        assert ws.receive_json()["price"] == pytest.approx(101.5)


@pytest.mark.parametrize("legs", ["ZFZ26:3", "ZFZ26:3,ZFZ26:-2", "ZFZ26:0,ZNZ26:-2", "ZFZ26,ZNZ26"])
def test_잘못된_스프레드_구성은_거절한다(env, legs):
    with env.client as client:
        with pytest.raises(WebSocketDisconnect) as closed:
            with client.websocket_connect(f"/ws/market?code={SPREAD}&market=overseas&legs={legs}") as ws:
                ws.receive_json()
        assert closed.value.code == 4422


def test_스프레드는_해외에서만_쓸_수_있다(env):
    with env.client as client:
        with pytest.raises(WebSocketDisconnect) as closed:
            with client.websocket_connect(f"/ws/market?code={SPREAD}&legs=ZFZ26:3,ZNZ26:-2") as ws:
                ws.receive_json()
        assert closed.value.code == 4422


def make_hub():
    connections = []

    def factory(on_event, on_state):
        connections.append(FakeRealtime(on_event, on_state))
        return connections[-1]

    from app.config import Settings

    settings = Settings(trading_env="mock", nh_overseas_app_key="k", nh_overseas_app_secret="s", _env_file=None)
    return MarketHub(settings, overseas_realtime_factory=factory), connections


def run(scenario):
    asyncio.run(scenario())


def test_같은_종목을_직접_보는_화면과_구독을_함께_쓰고_서로_끊지_않는다():
    async def scenario():
        hub, connections = make_hub()
        spread = await hub.join(SPREAD, "overseas", LEGS)
        direct = await hub.join("ZNZ26", "overseas")
        feeds = connections[0].subscribed
        assert feeds == [Feed("FA", "ZFZ26"), Feed("FA", "ZNZ26"), Feed("FB", "ZNZ26")]

        await hub.leave(direct)  # 스프레드가 쓰는 체결은 남기고 호가만 푼다
        assert connections[0].subscribed == [Feed("FA", "ZFZ26"), Feed("FA", "ZNZ26")]

        direct = await hub.join("ZNZ26", "overseas")
        await hub.leave(spread)  # 직접 보는 화면이 쓰는 ZN은 남기고 ZF만 푼다
        assert connections[0].subscribed == [Feed("FA", "ZNZ26"), Feed("FB", "ZNZ26")]
        await hub.leave(direct)
        assert connections[0].subscribed == []

    run(scenario)


def test_스프레드는_구독_한도를_두_종목으로_센다():
    async def scenario():
        from app.nh.hub import HubFull

        hub, _ = make_hub()
        await hub.join(SPREAD, "overseas", LEGS)
        await hub.join("ZBZ26", "overseas")
        await hub.join("ZTZ26", "overseas")
        with pytest.raises(HubFull):
            await hub.join("UBZ26", "overseas")

    run(scenario)
