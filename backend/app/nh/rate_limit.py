"""호출 제한(초당 건수)을 지키도록 요청 사이를 벌린다."""

import threading
import time
from collections.abc import Callable
from enum import StrEnum


class Limit(StrEnum):
    ORDER = "order"
    ACCOUNT = "account"
    QUOTE = "quote"


PER_SECOND = {Limit.ORDER: 5, Limit.ACCOUNT: 10, Limit.QUOTE: 10}


class RateLimiter:
    """등급별로 요청 간격(1 / 초당 건수)을 지킨다. 환경(모의·실전)마다 따로 센다."""

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._monotonic = monotonic
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next_allowed: dict[tuple[str, Limit], float] = {}

    def wait(self, environment: str, limit: Limit) -> float:
        """보내도 될 때까지 기다리고 기다린 시간(초)을 돌려준다."""
        interval = 1.0 / PER_SECOND[limit]
        key = (environment, limit)
        with self._lock:
            now = self._monotonic()
            allowed_at = self._next_allowed.get(key, now)
            delay = max(0.0, allowed_at - now)
            self._next_allowed[key] = max(allowed_at, now) + interval
        if delay > 0:
            self._sleep(delay)
        return delay


# 프로세스 안의 모든 NH 클라이언트가 함께 쓰는 제한기. 한도는 클라이언트가 아니라 계정마다 걸린다.
SHARED_LIMITER = RateLimiter()
