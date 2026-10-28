import asyncio
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.nh.errors import NHConfigError
from app.nh.hub import HubFull, MarketHub

router = APIRouter()

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{6,16}$")

# 닫힘 코드. 4000번대는 애플리케이션이 정한다.
CLOSE_BAD_CODE = 4422
CLOSE_NO_CREDENTIALS = 4503
CLOSE_FULL = 4429


@router.websocket("/ws/market")
async def market_stream(websocket: WebSocket, code: str = "") -> None:
    """종목의 실시간 체결·호가를 JSON 메시지로 보낸다. 메시지 형식은 `backend/README.md`를 본다."""
    hub: MarketHub = websocket.app.state.hub
    await websocket.accept()
    if not CODE_PATTERN.match(code):
        await websocket.close(code=CLOSE_BAD_CODE, reason="종목코드 형식이 올바르지 않습니다")
        return
    try:
        subscriber = await hub.join(code)
    except NHConfigError:
        await websocket.close(code=CLOSE_NO_CREDENTIALS, reason="NH 인증 정보가 설정되지 않았습니다")
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
