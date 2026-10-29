"""실행 기록 변경을 웹소켓 구독자에게 알리는 통로.

기록은 러너 스레드에서 쓰고 구독자는 API의 이벤트 루프에 있으므로, 메시지는 구독자가 속한
루프로 안전하게 넘긴다. 구독자가 느려 큐가 차면 메시지를 버리고 `resync`를 한 번 보내
다시 조회하게 한다.
"""

import asyncio
import threading
from typing import Any

QUEUE_SIZE = 1000
RESYNC = {"type": "resync"}


def _mode_of(message: dict[str, Any]) -> str | None:
    holder = message.get("line") or message.get("run") or message
    return holder.get("mode")


class RunSubscriber:
    def __init__(self, loop: asyncio.AbstractEventLoop, mode: str | None = None):
        self.loop = loop
        self.mode = mode
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self._overflowed = False

    def _put(self, message: dict[str, Any]) -> None:
        if self._overflowed:
            return
        try:
            self.queue.put_nowait(message)
        except asyncio.QueueFull:
            # 쌓인 메시지를 모두 버리고, 다시 조회하라는 신호 하나만 남긴다.
            while not self.queue.empty():
                self.queue.get_nowait()
            self.queue.put_nowait(RESYNC)
            self._overflowed = True

    def acknowledge_resync(self) -> None:
        """`resync`를 보낸 뒤 다시 메시지를 받기 시작한다."""
        self._overflowed = False


class RunEvents:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: set[RunSubscriber] = set()

    def subscribe(self, loop: asyncio.AbstractEventLoop, mode: str | None = None) -> RunSubscriber:
        subscriber = RunSubscriber(loop, mode)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: RunSubscriber) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, message: dict[str, Any]) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        mode = _mode_of(message)
        for subscriber in subscribers:
            if subscriber.mode and mode and subscriber.mode != mode:
                continue
            try:
                subscriber.loop.call_soon_threadsafe(subscriber._put, message)
            except RuntimeError:
                # 구독자의 루프가 이미 닫혔다.
                self.unsubscribe(subscriber)
