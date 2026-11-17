import asyncio
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.nh.errors import NHConfigError
from app.nh.hub import HubFull, MarketHub
from strategy_base.manifest import SpreadLeg
from app.records.events import RESYNC
from app.records.store import MODES, RunStore

router = APIRouter()

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{6,16}$")
# 해외 종목코드는 ZNZ26처럼 5자일 수 있다.
OVERSEAS_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{3,16}$")

# 닫힘 코드. 4000번대는 애플리케이션이 정한다.
CLOSE_BAD_CODE = 4422
CLOSE_NO_CREDENTIALS = 4503
CLOSE_FULL = 4429
CLOSE_BAD_MODE = 4422


def _parse_legs(text: str) -> list[SpreadLeg] | None:
    """`종목코드:가중치,종목코드:가중치`를 읽는다(가중치는 소수도 가능). 서로 다른 종목 2개가 아니거나 형식이 틀리면 `None`."""
    parsed = []
    for part in text.split(","):
        leg_code, _, ratio = part.partition(":")
        if not OVERSEAS_CODE_PATTERN.match(leg_code) or not re.fullmatch(r"-?[1-9][0-9]{0,2}(\.[0-9]{1,4})?", ratio):
            return None
        weight = float(ratio)
        parsed.append(SpreadLeg(code=leg_code, ratio=int(weight) or (1 if weight > 0 else -1), weight=weight))
    if len(parsed) != 2 or parsed[0].code == parsed[1].code:
        return None
    return parsed


@router.websocket("/ws/market")
async def market_stream(websocket: WebSocket, code: str = "", market: str = "domestic", legs: str = "") -> None:
    """종목의 실시간 체결·호가를 JSON 메시지로 보낸다. `market`은 `domestic`(기본) 또는 `overseas`다. 메시지 형식은 `backend/README.md`를 본다.

    `legs=종목코드:가중치,종목코드:가중치`(해외만)을 함께 보내면 두 종목의 체결을 합성한 스프레드 체결을 보낸다(호가는 없다).
    """
    hub: MarketHub = websocket.app.state.hub
    await websocket.accept()
    if market not in ("domestic", "overseas"):
        await websocket.close(code=CLOSE_BAD_CODE, reason="market은 domestic 또는 overseas여야 합니다")
        return
    spread = _parse_legs(legs) if legs else None
    if legs and (spread is None or market != "overseas"):
        await websocket.close(code=CLOSE_BAD_CODE, reason="스프레드 구성이 올바르지 않습니다")
        return
    plain = code.replace("-", "") if spread else code
    if not (OVERSEAS_CODE_PATTERN if market == "overseas" else CODE_PATTERN).match(plain):
        await websocket.close(code=CLOSE_BAD_CODE, reason="종목코드 형식이 올바르지 않습니다")
        return
    try:
        subscriber = await hub.join(code, market, spread)
    except NHConfigError as error:
        reason = str(error) if market == "overseas" else "NH 인증 정보가 설정되지 않았습니다"
        await websocket.close(code=CLOSE_NO_CREDENTIALS, reason=reason)
        return
    except HubFull as error:
        await websocket.close(code=CLOSE_FULL, reason=str(error))
        return

    try:
        listener = asyncio.ensure_future(websocket.receive())
        while True:
            getter = asyncio.ensure_future(subscriber.queue.get())
            done, _ = await asyncio.wait({getter, listener}, return_when=asyncio.FIRST_COMPLETED)
            if listener in done:
                getter.cancel()
                if listener.result().get("type") == "websocket.disconnect":
                    break
                listener = asyncio.ensure_future(websocket.receive())
            if getter in done:
                await websocket.send_json(getter.result())
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        listener.cancel()
        await hub.leave(subscriber)


@router.websocket("/ws/runs")
async def run_stream(websocket: WebSocket, mode: str = "") -> None:
    """실행 이력의 변경(`run`, `journal`, `pnl`)을 JSON 메시지로 보낸다. 형식은 `backend/README.md`를 본다.

    구독을 시작하면 `ready`를 먼저 보낸다. 화면은 `ready`를 받은 뒤 REST로 현재 상태를 조회하면
    그 사이에 생긴 변경을 놓치지 않는다. 메시지가 밀리면 `resync`를 보내 다시 조회하게 한다.
    """
    store: RunStore = websocket.app.state.run_store
    await websocket.accept()
    if mode not in MODES:
        await websocket.close(code=CLOSE_BAD_MODE, reason="mode는 backtest 또는 paper여야 합니다")
        return
    subscriber = store.events.subscribe(asyncio.get_running_loop(), mode)
    try:
        await websocket.send_json({"type": "ready"})
        listener = asyncio.ensure_future(websocket.receive())
        while True:
            getter = asyncio.ensure_future(subscriber.queue.get())
            done, _ = await asyncio.wait({getter, listener}, return_when=asyncio.FIRST_COMPLETED)
            if listener in done:
                getter.cancel()
                if listener.result().get("type") == "websocket.disconnect":
                    break
                listener = asyncio.ensure_future(websocket.receive())
            if getter in done:
                message = getter.result()
                if message is RESYNC:
                    subscriber.acknowledge_resync()
                await websocket.send_json(message)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        listener.cancel()
        store.events.unsubscribe(subscriber)
