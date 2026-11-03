"""전략이 선언한 추가 봉 계열(일봉)을 NH에서 불러온다."""

from collections.abc import Callable
from datetime import date, timedelta

from app.config import Settings
from app.nh.client import NHClient
from app.nh.domestic.market import fetch_daily_bars as fetch_domestic_daily
from app.nh.overseas.quotes import fetch_daily_bars as fetch_overseas_daily
from strategy_base.manifest import Instrument
from strategy_base.models import Bar

# (종목, 최근 일봉 개수) -> 일봉(오래된 것부터)
DailyFetcher = Callable[[Instrument, int], list[Bar]]

# 일봉 계열에 더해 두는 여유. 휴장일과 `history_bars` 계산에 쓰인다.
DAILY_MARGIN = 60


def nh_daily_fetcher(settings: Settings) -> DailyFetcher:
    def fetch(instrument: Instrument, quantity: int) -> list[Bar]:
        if instrument.market == "overseas":
            client = NHClient(settings, market="overseas")
            return fetch_overseas_daily(client, instrument.exchange or "", instrument.code or "", quantity=quantity)
        client = NHClient(settings)
        candles = fetch_domestic_daily(client, instrument.code or "", quantity=quantity)
        return [Bar(c.time, c.high, c.low, c.close, c.volume, c.open) for c in candles]

    return fetch


def days_needed(start: date, today: date) -> int:
    """`start`부터 오늘까지 지표를 계산하기에 충분한 일봉 개수."""
    return (today - start).days + DAILY_MARGIN


def warmup_start(start: date, days: int) -> date:
    return start - timedelta(days=days)
