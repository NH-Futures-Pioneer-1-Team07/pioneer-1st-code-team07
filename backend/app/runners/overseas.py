"""해외 종목을 백테스트·모의매매에서 실행하는 데 쓰는 NH 호출 묶음.

해외 분봉의 시각은 국내와 같이 한국 시간이고 봉이 시작한 시각이다(모의환경 호출로 확인).
"""

from datetime import date

from app.config import Settings
from app.nh.client import NHClient
from app.nh.overseas import quotes
from strategy_base.manifest import Instrument

# 해외 선물은 거의 하루 종일 거래한다. 하루 정상 봉 수를 어림하는 거래 시간(분).
OVERSEAS_SESSION_MINUTES = 1380

OVERSEAS_KEY_NAMES = "NH_OVERSEAS_APP_KEY, NH_OVERSEAS_APP_SECRET"


def has_keys(settings: Settings, market: str) -> bool:
    if market == "overseas":
        return bool(settings.nh_overseas_app_key and settings.nh_overseas_app_secret)
    return bool(settings.nh_app_key and settings.nh_app_secret)


def key_names(market: str) -> str:
    return OVERSEAS_KEY_NAMES if market == "overseas" else "NH_APP_KEY, NH_APP_SECRET"


class OverseasProbe:
    """백테스트 가능 기간을 찾는 데 쓰는 해외 분봉 조회. 최종거래일은 알 수 없다.

    해외 분봉은 날짜를 지정해 조회할 수 없어 처음 한 번 조회되는 전체 분봉을 이어받아 날짜별 봉 수를 센다.
    """

    def __init__(self, client: NHClient, exchange: str, code: str, minutes: int):
        self._client = client
        self._exchange = exchange
        self._code = code
        self._minutes = minutes
        self._counts: dict[date, int] | None = None

    def bars_on(self, day: date) -> int:
        if self._counts is None:
            counts: dict[date, int] = {}
            for bar in quotes.fetch_minute_bars(self._client, self._exchange, self._code, minutes=self._minutes):
                counts[bar.time.date()] = counts.get(bar.time.date(), 0) + 1
            self._counts = counts
        return self._counts.get(day, 0)

    def last_trading_day(self) -> date | None:
        return None


def overseas_instrument_ready(instrument: Instrument) -> str | None:
    """해외 종목에 필요한 값이 빠졌으면 사유를 돌려준다."""
    if not instrument.exchange:
        return "해외 종목에는 거래소 코드(exchange)가 필요합니다"
    return None
