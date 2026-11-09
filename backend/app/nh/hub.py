"""화면용 시세 허브. NH 실시간 연결 하나를 여러 화면이 나눠 쓴다.

국내와 해외는 키가 달라 NH 실시간 연결을 시장마다 하나씩 둔다. 종목마다 체결(국내 `KA`, 해외 `FA`)과
호가(국내 `KB`, 해외 `FB`)를 구독하고, 그 종목을 보는 화면의 대기열로 메시지를 나눠 준다.
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

MARKETS = ("domestic", "overseas")
FEED_CODES = {"domestic": ("KA", "KB"), "overseas": ("FA", "FB")}


class HubFull(NHError):
    pass


class Subscriber:
    """화면 하나. 대기열이 가득 차면 오래된 메시지부터 버린다."""

    def __init__(self, code: str, market: str = "domestic"):
        self.code = code
        self.market = market
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
    def __init__(
        self,
        settings: Settings,
        *,
        realtime_factory: RealtimeFactory | None = None,
        overseas_realtime_factory: RealtimeFactory | None = None,
    ):
        self._settings = settings
        self._factories: dict[str, RealtimeFactory] = {
            "domestic": realtime_factory
            or (lambda on_event, on_state: RealtimeConnection(NHClient(settings), on_event=on_event, on_state=on_state)),
            "overseas": overseas_realtime_factory
            or (
                lambda on_event, on_state: RealtimeConnection(
                    NHClient(settings, market="overseas"), on_event=on_event, on_state=on_state
                )
            ),
        }
        self._connections: dict[str, Any] = {}
        self._subscribers: dict[tuple[str, str], set[Subscriber]] = {}
        self._states = {market: "connecting" for market in MARKETS}
        self._lock = asyncio.Lock()

    def has_credentials(self, market: str = "domestic") -> bool:
        if market == "overseas":
            return bool(self._settings.nh_overseas_app_key and self._settings.nh_overseas_app_secret)
        return bool(self._settings.nh_app_key and self._settings.nh_app_secret)

    def state(self, market: str = "domestic") -> str:
        return self._states[market]

    @property
    def codes(self) -> frozenset[str]:
        return frozenset(code for market, code in self._subscribers if market == "domestic")

    async def join(self, code: str, market: str = "domestic") -> Subscriber:
        """종목을 보는 화면을 등록한다. 시장마다 서로 다른 종목이 `MAX_CODES`개를 넘으면 `HubFull`이다."""
        if not self.has_credentials(market):
            names = "NH_OVERSEAS_APP_KEY, NH_OVERSEAS_APP_SECRET" if market == "overseas" else "NH_APP_KEY, NH_APP_SECRET"
            raise NHConfigError(f"{names} 환경변수를 설정하세요")
        async with self._lock:
            key = (market, code)
            in_market = sum(1 for item in self._subscribers if item[0] == market)
            if key not in self._subscribers and in_market >= MAX_CODES:
                raise HubFull(f"시세는 서로 다른 종목 {MAX_CODES}개까지 볼 수 있습니다")
            connection = self._connections.get(market)
            if connection is None:
                connection = self._factories[market](
                    lambda event, market=market: self._on_event(market, event),
                    lambda state, detail, market=market: self._on_state(market, state, detail),
                )
                self._connections[market] = connection
                connection.start()
            subscriber = Subscriber(code, market)
            if key not in self._subscribers:
                self._subscribers[key] = set()
                for action_code in FEED_CODES[market]:
                    await connection.subscribe(Feed(action_code, code))
            self._subscribers[key].add(subscriber)
            subscriber.push({"type": "state", "state": self._states[market], "detail": ""})
            return subscriber

    async def leave(self, subscriber: Subscriber) -> None:
        async with self._lock:
            key = (subscriber.market, subscriber.code)
            group = self._subscribers.get(key)
            if group is None:
                return
            group.discard(subscriber)
            if group:
                return
            del self._subscribers[key]
            connection = self._connections.get(subscriber.market)
            if connection is not None:
                for action_code in FEED_CODES[subscriber.market]:
                    await connection.unsubscribe(Feed(action_code, subscriber.code))

    async def close(self) -> None:
        async with self._lock:
            connections, self._connections = list(self._connections.values()), {}
            self._subscribers.clear()
        for connection in connections:
            await connection.stop()

    # ---- NH 실시간에서 오는 것 ----

    def _on_state(self, market: str, state: Any, detail: str) -> None:
        self._states[market] = str(state.value if isinstance(state, State) else state)
        self._broadcast(market, {"type": "state", "state": self._states[market], "detail": detail})

    def _on_event(self, market: str, event: Any) -> None:
        message = serialize(event)
        if message is None:
            return
        if message["type"] == "reconnected":
            self._broadcast(market, message)
            return
        code = message["code"]
        if code is None:  # 어느 종목의 거절인지 모르면 그 시장의 모든 화면에 알린다
            self._broadcast(market, message)
            return
        for subscriber in list(self._subscribers.get((market, code), ())):
            subscriber.push(message)

    def _broadcast(self, market: str, message: dict[str, Any]) -> None:
        for (group_market, _), group in list(self._subscribers.items()):
            if group_market != market:
                continue
            for subscriber in list(group):
                subscriber.push(message)
