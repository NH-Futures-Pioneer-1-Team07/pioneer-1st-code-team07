"""선물 봉에 같은 시각의 기초자산 지수 종가를 붙인다.

종목에 `index_code`가 있으면 선물 봉과 지수 봉을 봉 시작 시각으로 짝지어 `Bar.reference`에 지수 종가를 넣는다.
선물 봉은 지우지 않는다. 체결·손익은 선물 가격으로 계산하고, 베이시스(`close - reference`)는 전략이 계산한다.
지수 봉이 없거나 종가가 양의 유한한 수가 아니면 `reference`는 `None`이다.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date

from app.nh.client import NHClient
from app.nh.domestic.quotes import fetch_minute_bars
from strategy_base.manifest import Instrument
from strategy_base.models import Bar


def attach_index(bars: Sequence[Bar], index_bars: Sequence[Bar]) -> list[Bar]:
    """같은 시작 시각의 지수 봉 종가를 `reference`로 붙인 선물 봉을 돌려준다."""
    closes = {bar.time: bar.close for bar in index_bars if math.isfinite(bar.close) and bar.close > 0}
    return [replace(bar, reference=closes.get(bar.time)) for bar in bars]


def index_loader(base, index_code: str):
    """선물 분봉 로더를 감싸 같은 기간의 지수 분봉을 받아 붙이는 로더를 만든다. 진행률은 두 호출을 합쳐 알린다."""

    def load(code: str, minutes: int, start: date, end: date, on_progress: Callable[[int, int], None]):
        from app.runners.service import LoadedData

        futures = base(code, minutes, start, end, lambda done, total: on_progress(done, 2 * total))
        index = base(index_code, minutes, start, end, lambda done, total: on_progress(total + done, 2 * total))
        days = {day: attach_index(bars, index.days.get(day, [])) for day, bars in futures.days.items()}
        return LoadedData(days, futures.last_trading_day, futures.fee_price)

    return load


class IndexBroker:
    """선물 브로커를 감싸 분봉 조회 결과에 지수 종가를 붙인다. 나머지 호출은 그대로 넘긴다."""

    def __init__(self, inner, client: NHClient, index_code: str, minutes: int):
        self._inner = inner
        self._client = client
        self._index_code = index_code
        self._minutes = minutes

    def fetch_bars(self, day: date) -> list[Bar]:
        bars = self._inner.fetch_bars(day)
        index = fetch_minute_bars(self._client, self._index_code, minutes=self._minutes, start=day, end=day)
        return attach_index(bars, index)

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


def wrap_broker(broker, instrument: Instrument, client: NHClient, minutes: int):
    """종목에 `index_code`가 있으면 지수 종가를 붙이는 브로커로 감싼다."""
    if not instrument.index_code:
        return broker
    return IndexBroker(broker, client, instrument.index_code, minutes)
