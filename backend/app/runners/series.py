"""전략이 선언한 추가 봉 계열(일봉)을 NH에서 불러온다."""

from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta

from app.config import Settings
from app.nh.auth import KST
from app.nh.client import NHClient
from app.nh.domestic.market import fetch_daily_bars as fetch_domestic_daily
from app.nh.overseas.quotes import fetch_daily_bars as fetch_overseas_daily
from app.nh.overseas.quotes import fetch_minute_bars as fetch_overseas_minutes
from strategy_base.manifest import Instrument
from strategy_base.models import Bar

# (종목, 최근 일봉 개수) -> 일봉(오래된 것부터)
DailyFetcher = Callable[[Instrument, int], list[Bar]]

# 일봉 계열에 더해 두는 여유. 휴장일과 `history_bars` 계산에 쓰인다.
DAILY_MARGIN = 60


# 영업일 경계: CME 정규 휴장 시간(한국 시간 06~08시) 직전·직후를 가르도록 한국 시간에서 7시간을 뺀 날짜를 영업일로 본다.
BUSINESS_DAY_SHIFT = timedelta(hours=7)
SYNTHETIC_MINUTES = 5


def daily_from_minutes(bars: Sequence[Bar]) -> list[Bar]:
    """분봉을 영업일별 일봉으로 합친다. 일봉의 시각은 영업일 0시(한국 시간)이고 오래된 순서로 돌려준다."""
    days: dict[date, list[Bar]] = {}
    for bar in sorted(bars, key=lambda item: item.time):
        days.setdefault((bar.time - BUSINESS_DAY_SHIFT).date(), []).append(bar)
    return [
        Bar(
            datetime.combine(day, time(0, 0), tzinfo=KST),
            max(bar.high for bar in group),
            min(bar.low for bar in group),
            group[-1].close,
            sum(bar.volume for bar in group),
            group[0].open,
        )
        for day, group in days.items()
    ]


def nh_daily_fetcher(settings: Settings) -> DailyFetcher:
    def fetch(instrument: Instrument, quantity: int) -> list[Bar]:
        if instrument.market == "overseas":
            client = NHClient(settings, market="overseas")
            return fetch_overseas_daily(client, instrument.exchange or "", instrument.code or "", quantity=quantity)
        client = NHClient(settings)
        candles = fetch_domestic_daily(client, instrument.code or "", quantity=quantity)
        return [Bar(c.time, c.high, c.low, c.close, c.volume, c.open) for c in candles]

    def from_minutes(instrument: Instrument, quantity: int) -> list[Bar]:
        """NH가 일봉을 주지 않는 해외 종목(예: 3년물 `Z3NZ26`)의 일봉을 5분봉으로 합성한다. 스프레드 일봉 짝짓기가 쓴다."""
        client = NHClient(settings, market="overseas")
        start = datetime.now(KST).date() - timedelta(days=quantity)
        minutes = fetch_overseas_minutes(client, instrument.exchange or "", instrument.code or "", minutes=SYNTHETIC_MINUTES, start=start)
        return daily_from_minutes(minutes)[-quantity:]

    fetch.from_minutes = from_minutes  # type: ignore[attr-defined]
    return fetch


def days_needed(start: date, today: date) -> int:
    """`start`부터 오늘까지 지표를 계산하기에 충분한 일봉 개수."""
    return (today - start).days + DAILY_MARGIN


def warmup_start(start: date, days: int) -> date:
    return start - timedelta(days=days)
