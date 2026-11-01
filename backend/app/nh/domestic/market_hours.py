"""종목별 장 시간표와 장 종류 판정. NH API에 삼성전자선물의 장 시간을 알려 주는 조회가 없어 직접 정의한다.

시간은 NH 모의환경의 분봉 실측(첫 봉 08:45, 마지막 봉 15:45)에 맞췄다. 공휴일과 최종거래일은 다루지 않는다.
종목을 더하려면 `SCHEDULES`에 상품명과 시간표를 넣는다.
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Literal

MarketSession = Literal["before_open", "auction", "regular", "closed", "holiday", "unknown"]


@dataclass(frozen=True)
class MarketHours:
    """평일 하루의 구간. `open_auction`·`close_auction`은 (시작, 끝)이고 정규장은 두 동시호가 사이다. 마감 동시호가가 끝나면 장 마감이다."""

    open_auction: tuple[time, time]
    close_auction: tuple[time, time]

    def session(self, at: datetime) -> MarketSession:
        if at.weekday() >= 5:
            return "holiday"
        now = at.time()
        if now < self.open_auction[0]:
            return "before_open"
        if now < self.open_auction[1]:
            return "auction"
        if now < self.close_auction[0]:
            return "regular"
        if now < self.close_auction[1]:
            return "auction"
        return "closed"


STOCK_FUTURES = MarketHours(
    open_auction=(time(8, 30), time(8, 45)),
    close_auction=(time(15, 35), time(15, 45)),
)

# 시세 응답의 종목명(`삼성전자 F 202611 ( 10)`)에서 월물 앞부분을 상품명으로 본다.
SCHEDULES: dict[str, MarketHours] = {"삼성전자": STOCK_FUTURES}


def product_name(name: str) -> str:
    return name.split(" F ")[0].strip()


def market_session(name: str, at: datetime) -> MarketSession:
    hours = SCHEDULES.get(product_name(name))
    return hours.session(at) if hours else "unknown"
