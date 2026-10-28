"""화면용 시세 허브. NH 실시간 연결 하나를 여러 화면이 나눠 쓴다.

종목마다 체결(`KA`)과 호가(`KB`)를 구독하고, 그 종목을 보는 화면의 대기열로 메시지를 나눠 준다.
구독은 종목별로 화면 수를 세어 첫 화면이 붙을 때 걸고 마지막 화면이 떠날 때 푼다.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from app.config import Settings
from app.nh.client import NHClient
from app.nh.errors import NHConfigError, NHError
from app.nh.realtime import RealtimeConnection, State
from app.nh.realtime_data import Feed, OrderBook, Reconnected, SubscriptionFailed, Trade

logger = logging.getLogger(__name__)

# 한 종목에 체결·호가 두 건을 구독한다. NH 구독 한도(20건)에서 모의매매 운용이 쓰는 몫을 남긴다.
MAX_CODES = 4
QUEUE_SIZE = 256

RealtimeFactory = Callable[[Callable[[Any], None], Callable[[Any, str], None]], Any]


class HubFull(NHError):
    pass


class Subscriber:
    """화면 하나. 대기열이 가득 차면 오래된 메시지부터 버린다."""

    def __init__(self, code: str):
        self.code = code
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self.dropped = 0

    def push(self, message: dict[str, Any]) -> None:
        if self.queue.full():
            self.queue.get_nowait()
            self.dropped += 1
        self.queue.put_nowait(message)


def serialize(event: Any) -> dict[str, Any] | None:
    """NH 실시간 이벤트를 화면에 보낼 메시지로 바꾼다."""
    if isinstance(event, Trade):
        return {
            "type": "trade",
            "code": event.code,
            "time": event.time,
            "price": event.price,
            "quantity": event.quantity,
            "cum_volume": event.cum_volume,
            "open": event.open,
            "high": event.high,
            "low": event.low,
            "best_ask": event.best_ask,
            "best_bid": event.best_bid,
            "is_trade": event.is_trade,
        }
    if isinstance(event, OrderBook):
        return {
            "type": "orderbook",
            "code": event.code,
            "time": event.time,
            "total_ask_quantity": event.total_ask_quantity,
            "total_bid_quantity": event.total_bid_quantity,
            "levels": [
                {
                    "ask_price": level.ask_price,
                    "ask_quantity": level.ask_quantity,
                    "bid_price": level.bid_price,
                    "bid_quantity": level.bid_quantity,
                }
                for level in event.levels
            ],
        }
    if isinstance(event, Reconnected):
        return {"type": "reconnected"}
    if isinstance(event, SubscriptionFailed):
        return {
            "type": "subscription_failed",
            "code": event.feed.symbol if event.feed else None,
            "reason_code": event.code,
            "message": event.message,
        }
    return None


class MarketHub:
    def __init__(self, settings: Settings, *, realtime_factory: RealtimeFactory | None = None):
        self._settings = settings
        self._factory = realtime_factory or (
            lambda on_event, on_state: RealtimeConnection(NHClient(settings), on_event=on_event, on_state=on_state)
        )
        self._connection: Any = None
        self._subscribers: dict[str, set[Subscriber]] = {}
        self._state = "connecting"
        self._lock = asyncio.Lock()

    def has_credentials(self) -> bool:
        return bool(self._settings.nh_app_key and self._settings.nh_app_secret)

    @property
    def state(self) -> str:
        return self._state

    @property
    def codes(self) -> frozenset[str]:
        return frozenset(self._subscribers)

    async def join(self, code: str) -> Subscriber:
        """종목을 보는 화면을 등록한다. 서로 다른 종목이 `MAX_CODES`개를 넘으면 `HubFull`이다."""
        if not self.has_credentials():
            raise NHConfigError("NH_APP_KEY, NH_APP_SECRET 환경변수를 설정하세요")
        async with self._lock:
            if code not in self._subscribers and len(self._subscribers) >= MAX_CODES:
                raise HubFull(f"시세는 서로 다른 종목 {MAX_CODES}개까지 볼 수 있습니다")
            if self._connection is None:
                self._connection = self._factory(self._on_event, self._on_state)
                self._connection.start()
            subscriber = Subscriber(code)
            if code not in self._subscribers:
                self._subscribers[code] = set()
                await self._connection.subscribe(Feed("KA", code))
                await self._connection.subscribe(Feed("KB", code))
            self._subscribers[code].add(subscriber)
            subscriber.push({"type": "state", "state": self._state, "detail": ""})
            return subscriber

    async def leave(self, subscriber: Subscriber) -> None:
        async with self._lock:
            group = self._subscribers.get(subscriber.code)
            if group is None:
                return
            group.discard(subscriber)
            if group:
                return
            del self._subscribers[subscriber.code]
            if self._connection is not None:
                await self._connection.unsubscribe(Feed("KA", subscriber.code))
                await self._connection.unsubscribe(Feed("KB", subscriber.code))

    async def close(self) -> None:
        async with self._lock:
            connection, self._connection = self._connection, None
            self._subscribers.clear()
        if connection is not None:
            await connection.stop()

    # ---- NH 실시간에서 오는 것 ----

    def _on_state(self, state: Any, detail: str) -> None:
        self._state = str(state.value if isinstance(state, State) else state)
        self._broadcast({"type": "state", "state": self._state, "detail": detail})

    def _on_event(self, event: Any) -> None:
        message = serialize(event)
        if message is None:
            return
        if message["type"] == "reconnected":
            self._broadcast(message)
            return
        code = message["code"]
        if code is None:  # 어느 종목의 거절인지 모르면 모든 화면에 알린다
            self._broadcast(message)
            return
        for subscriber in list(self._subscribers.get(code, ())):
            subscriber.push(message)

    def _broadcast(self, message: dict[str, Any]) -> None:
        for group in list(self._subscribers.values()):
            for subscriber in list(group):
                subscriber.push(message)
