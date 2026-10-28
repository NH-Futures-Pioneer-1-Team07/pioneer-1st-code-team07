"""NH선물 실시간 웹소켓 연결.

- 접속키는 연결할 때마다 새로 발급받고 보관하지 않는다. 주소 뒤에 키가 붙으므로 주소와
  연결 예외의 글은 로그에 남기지 않는다(예외 종류만 남긴다).
- 서버가 `pingpong`을 보내면 받은 그대로 되돌려야 세션이 유지된다. 웹소켓 규격의 핑 프레임은
  보내지 않는다.
- 끊기면 간격을 늘려 가며 다시 연결하고 구독을 모두 다시 건다. 끊긴 동안의 값은 다시 오지
  않으므로 `Reconnected`를 알려 호출하는 쪽이 조회로 채우게 한다.
"""

import asyncio
import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, Protocol

from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed

from app.nh.errors import NHError
from app.nh.realtime_data import (
    Feed,
    OrderBook,
    OrderEvent,
    Reconnected,
    SubscriptionFailed,
    Trade,
    parse_order_book,
    parse_order_event,
    parse_trade,
)

logger = logging.getLogger(__name__)

STREAM_PATH = "/trade/ws-stream"
API_VERSION = "1"
ACTION_INIT, ACTION_SUBSCRIBE, ACTION_UNSUBSCRIBE = "0", "A", "D"

INIT_CODE = "INIT"
INIT_SUCCESS = "INIT_SUCCESS"
PINGPONG = "pingpong"
SUBSCRIBED = "RT_INIT"

MAX_SUBSCRIPTIONS = 20
OPEN_TIMEOUT = 10.0
INIT_TIMEOUT = 10.0
CLOSE_TIMEOUT = 1.0
# 서버가 세션 유지 신호를 주기적으로 보내므로 살아 있는 연결이 이만큼 조용할 일은 없다.
IDLE_TIMEOUT = 90.0
# 이만큼 붙어 있다 끊기면 정상으로 보고 다음 재연결을 기다리지 않는다.
SETTLED_AFTER = 60.0
BACKOFF = (0.0, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)

_SYMBOL_IN_TEXT = re.compile(r"\[action_sym::([^\]]*)\]")

Event = Trade | OrderBook | OrderEvent | SubscriptionFailed | Reconnected


class State(StrEnum):
    CONNECTING = "connecting"
    LIVE = "live"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"


class SubscriptionLimitExceeded(NHError):
    pass


class RealtimeError(NHError):
    pass


class Socket(Protocol):
    async def send(self, message: str) -> None: ...

    async def recv(self) -> Any: ...

    async def close(self) -> None: ...


class KeySource(Protocol):
    base_url: str

    def issue_websocket_key(self) -> str: ...

    def session_token(self) -> str: ...


Connect = Callable[[str], Awaitable[Socket]]


async def _default_connect(url: str) -> Socket:
    # 라이브러리 기본 핑 프레임(20초 주기)을 끈다. 켜 두면 국내 실시간 연결이 같은 주기로 끊긴다.
    return await ws_connect(url, ping_interval=None, open_timeout=OPEN_TIMEOUT)


def subscribe_message(feed: Feed, action: str) -> dict[str, Any]:
    body: dict[str, Any] = {"action_code": feed.action_code}
    if feed.symbol:
        body["action_sym"] = feed.symbol
    return {"header": {"api_ver": API_VERSION, "action": action}, "body": body}


class RealtimeConnection:
    def __init__(
        self,
        client: KeySource,
        *,
        on_event: Callable[[Event], None],
        on_state: Callable[[State, str], None] | None = None,
        connect: Connect = _default_connect,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        idle_timeout: float = IDLE_TIMEOUT,
    ):
        self._client = client
        self._on_event = on_event
        self._on_state = on_state
        self._connect = connect
        self._sleep = sleep
        self._monotonic = monotonic
        self._idle_timeout = idle_timeout
        self._feeds: set[Feed] = set()
        self._socket: Socket | None = None
        self._task: asyncio.Task[None] | None = None
        self._stopping = False
        self._ever_live = False
        self.state = State.STOPPED

    @property
    def feeds(self) -> frozenset[Feed]:
        return frozenset(self._feeds)

    # ---- 시작과 중지 ----

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stopping = False
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopping = True
        task, self._task = self._task, None
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self._close(self._socket)
        self._socket = None
        self._set_state(State.STOPPED, "")

    # ---- 구독 ----

    async def subscribe(self, feed: Feed) -> None:
        if feed in self._feeds:
            return
        if len(self._feeds) >= MAX_SUBSCRIPTIONS:
            raise SubscriptionLimitExceeded(f"실시간 구독은 {MAX_SUBSCRIPTIONS}건까지 걸 수 있습니다")
        self._feeds.add(feed)
        await self._send_if_live(subscribe_message(feed, ACTION_SUBSCRIBE))

    async def unsubscribe(self, feed: Feed) -> None:
        if feed not in self._feeds:
            return
        self._feeds.discard(feed)
        await self._send_if_live(subscribe_message(feed, ACTION_UNSUBSCRIBE))

    async def _send_if_live(self, message: dict[str, Any]) -> None:
        socket = self._socket
        if socket is not None and self.state == State.LIVE:
            await socket.send(json.dumps(message, ensure_ascii=False))

    # ---- 연결 유지 ----

    async def _run(self) -> None:
        failures = 0
        while not self._stopping:
            self._set_state(State.RECONNECTING if self._ever_live else State.CONNECTING, "")
            started = self._monotonic()
            try:
                await self._session()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                # 예외 글에 접속 주소(키 포함)가 들어갈 수 있으므로 종류만 남긴다.
                logger.warning("실시간 연결이 끊겼습니다: %s", type(error).__name__)
            if self._stopping:
                return
            failures = 0 if self._monotonic() - started >= SETTLED_AFTER else failures + 1
            delay = BACKOFF[min(failures, len(BACKOFF) - 1)]
            self._set_state(State.RECONNECTING, f"{delay:g}초 뒤 다시 연결")
            await self._sleep(delay)

    async def _session(self) -> None:
        key = await asyncio.to_thread(self._client.issue_websocket_key)
        token = await asyncio.to_thread(self._client.session_token)
        url = f"{_ws_base(self._client.base_url)}{STREAM_PATH}?access_key={key}"
        socket = await asyncio.wait_for(self._connect(url), OPEN_TIMEOUT + 1)
        self._socket = socket
        try:
            await self._initialise(socket, token)
            for feed in sorted(self._feeds, key=lambda item: (item.action_code, item.symbol or "")):
                await socket.send(json.dumps(subscribe_message(feed, ACTION_SUBSCRIBE), ensure_ascii=False))
            reconnected = self._ever_live
            self._ever_live = True
            self._set_state(State.LIVE, "")
            if reconnected:
                self._on_event(Reconnected())
            await self._listen(socket)
        finally:
            self._socket = None
            await self._close(socket)

    async def _initialise(self, socket: Socket, token: str) -> None:
        init = {
            "header": {"api_ver": API_VERSION, "action": ACTION_INIT},
            "body": {"action_code": "session_init", "session_token": token},
        }
        await socket.send(json.dumps(init, ensure_ascii=False))
        deadline = self._monotonic() + INIT_TIMEOUT
        while True:
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                raise TimeoutError("세션 초기화 응답이 오지 않았습니다")
            message = _decode(await asyncio.wait_for(socket.recv(), remaining))
            if message is None:
                continue
            if _is_pingpong(message):
                await socket.send(json.dumps(message, ensure_ascii=False))
                continue
            if message.get("code") == INIT_CODE and message.get("msg") == INIT_SUCCESS:
                return
            raise RealtimeError("세션 초기화가 받아들여지지 않았습니다")

    async def _listen(self, socket: Socket) -> None:
        while True:
            try:
                raw = await asyncio.wait_for(socket.recv(), self._idle_timeout)
            except TimeoutError:
                raise RealtimeError("서버에서 오는 신호가 없어 연결을 다시 맺습니다") from None
            except ConnectionClosed:
                raise
            message = _decode(raw)
            if message is not None:
                await self._handle(socket, message)

    # ---- 메시지 처리 ----

    async def _handle(self, socket: Socket, message: dict[str, Any]) -> None:
        if _is_pingpong(message):
            await socket.send(json.dumps(message, ensure_ascii=False))
            return
        header, body = message.get("header"), message.get("body")
        if isinstance(header, dict):
            if isinstance(body, dict):
                self._data(header, body)
            return
        code = str(message.get("code") or message.get("rt_cd") or "").strip()
        if code and code != SUBSCRIBED:
            self._refused(code, message)

    def _data(self, header: dict[str, Any], body: dict[str, Any]) -> None:
        action_code = str(header.get("action_code") or "").strip()
        symbol = str(header.get("action_sym") or "").strip()
        if action_code == "KA":
            event: Event = parse_trade(body, symbol)
        elif action_code == "KB":
            event = parse_order_book(body, symbol)
        elif action_code == "O1":
            event = parse_order_event(body)
        else:
            return
        self._on_event(event)

    def _refused(self, code: str, message: dict[str, Any]) -> None:
        """구독 요청이 거절됐다는 답. 해제(`D`)에 대한 답은 알리지 않는다."""
        data = message.get("data") if isinstance(message.get("data"), dict) else {}
        if str(data.get("action") or "") == ACTION_UNSUBSCRIBE:
            return
        said = str(message.get("message") or message.get("msg") or "").strip()
        feed = self._feed_of(data, said)
        logger.warning("실시간 구독이 거절되었습니다: code=%s", code)
        self._on_event(SubscriptionFailed(feed, code, said))

    def _feed_of(self, data: dict[str, Any], said: str) -> Feed | None:
        action_code = str(data.get("action_code") or "").strip()
        symbol = str(data.get("action_sym") or "").strip()
        if not symbol:
            found = _SYMBOL_IN_TEXT.search(said)
            symbol = found.group(1).strip() if found else ""
        if not action_code and not symbol:
            return None
        candidates = [
            feed
            for feed in self._feeds
            if (not action_code or feed.action_code == action_code) and (not symbol or feed.symbol == symbol)
        ]
        return candidates[0] if len(candidates) == 1 else None

    # ---- 내부 ----

    def _set_state(self, state: State, detail: str) -> None:
        if state != self.state or detail:
            self.state = state
            if self._on_state:
                self._on_state(state, detail)

    async def _close(self, socket: Socket | None) -> None:
        if socket is None:
            return
        try:
            await asyncio.wait_for(socket.close(), CLOSE_TIMEOUT)
        except Exception:
            pass


def _decode(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    try:
        message = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return message if isinstance(message, dict) else None


def _is_pingpong(message: dict[str, Any]) -> bool:
    return str(message.get("code") or "").lower() == PINGPONG


def _ws_base(base_url: str) -> str:
    if base_url.startswith("https://"):
        return "wss://" + base_url[len("https://") :]
    if base_url.startswith("http://"):
        return "ws://" + base_url[len("http://") :]
    return base_url
