"""백테스트로 검증할 수 있는 기간. 종목의 분봉이 있는 첫 날부터 마지막으로 마감된 거래일까지다."""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from app.nh.client import NHClient
from app.nh.quotes import fetch_minute_bars, fetch_quote

MAX_BACK_DAYS = 400
EMPTY_WEEKS = 3
LATEST_LOOKBACK_DAYS = 14


@dataclass(frozen=True)
class AvailableRange:
    start: date
    end: date
    last_trading_day: date | None


class ProbeSource(Protocol):
    """한 종목에 대해 날짜별 분봉 수와 최종거래일을 알려 준다."""

    def bars_on(self, day: date) -> int: ...

    def last_trading_day(self) -> date | None: ...


class NHProbe:
    def __init__(self, client: NHClient, code: str, minutes: int):
        self._client = client
        self._code = code
        self._minutes = minutes

    def bars_on(self, day: date) -> int:
        return len(fetch_minute_bars(self._client, self._code, minutes=self._minutes, start=day, end=day))

    def last_trading_day(self) -> date | None:
        return fetch_quote(self._client, self._code).last_trading_day


def _previous_weekday(day: date) -> date:
    day -= timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def find_range(source: ProbeSource, today: date) -> AvailableRange | None:
    """분봉이 있는 첫 날과 마지막 날을 찾는다. 분봉이 전혀 없으면 `None`이다.

    마지막 날은 오늘 이전, 최종거래일 이하에서 분봉이 있는 가장 최근 날이다. 첫 날은 주 단위로 거슬러
    올라가며 분봉이 있는 주를 찾고(연속 `EMPTY_WEEKS`주가 비면 멈춘다), 마지막으로 찾은 주 앞의 6일을
    하루씩 확인해 정한다.
    """
    last_trading_day = source.last_trading_day()
    cap = today - timedelta(days=1)
    if last_trading_day is not None and last_trading_day < cap:
        cap = last_trading_day

    end: date | None = None
    day = cap
    for _ in range(LATEST_LOOKBACK_DAYS):
        if day.weekday() < 5 and source.bars_on(day) > 0:
            end = day
            break
        day -= timedelta(days=1)
    if end is None:
        return None

    earliest, probe, empty = end, end, 0
    while empty < EMPTY_WEEKS and (end - probe).days < MAX_BACK_DAYS:
        probe -= timedelta(days=7)
        hit = next((d for d in (_nearest_weekday(probe), _previous_weekday(_nearest_weekday(probe))) if source.bars_on(d) > 0), None)
        if hit is None:
            empty += 1
        else:
            empty, earliest = 0, min(earliest, hit)
    day = earliest - timedelta(days=6)
    while day < earliest:
        if day.weekday() < 5 and source.bars_on(day) > 0:
            earliest = day
            break
        day += timedelta(days=1)
    return AvailableRange(earliest, end, last_trading_day)


def _nearest_weekday(day: date) -> date:
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


class RangeCache:
    """같은 종목의 가능 기간을 하루 동안 보관한다."""

    def __init__(self, today: Callable[[], date]):
        self._today = today
        self._lock = threading.Lock()
        self._values: dict[tuple[str, date], AvailableRange | None] = {}

    def get(self, code: str, source: ProbeSource) -> AvailableRange | None:
        today = self._today()
        with self._lock:
            key = (code, today)
            if key not in self._values:
                self._values = {k: v for k, v in self._values.items() if k[1] == today}
                self._values[key] = find_range(source, today)
            return self._values[key]
