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
    """백테스트 가능 기간을 찾는 데 쓰는 해외 분봉 조회. 최종거래일은 알 수 없다."""

    def __init__(self, client: NHClient, exchange: str, code: str, minutes: int):
        self._client = client
        self._exchange = exchange
        self._code = code
        self._minutes = minutes

    def bars_on(self, day: date) -> int:
        return len(
            quotes.fetch_minute_bars(self._client, self._exchange, self._code, minutes=self._minutes, start=day, end=day)
        )

    def last_trading_day(self) -> date | None:
        return None


class NullRealtime:
    """실시간 연결 자리. 해외 종목은 실시간 체결 대신 세션이 현재가를 주기적으로 조회한다."""

    async def subscribe(self, feed) -> None:
        return None

    def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None


def overseas_instrument_ready(instrument: Instrument) -> str | None:
    """해외 종목에 필요한 값이 빠졌으면 사유를 돌려준다."""
    if not instrument.exchange:
        return "해외 종목에는 거래소 코드(exchange)가 필요합니다"
    return None
