"""해외 선물의 장 시간. NH 해외 장운영 조회(`market-operations`)의 거래시간(한국 시간)으로 장 종류를 판정한다.

거래시간은 `08:00 ~ 07:00`처럼 하루 한 구간이며 끝이 시작보다 빠르면 다음 날로 이어진다. 월요일부터 금요일 저녁에
시작한 구간이 다음 날 아침에 끝나므로 월요일 시작 시각 전과 토요일 끝 시각 뒤부터 일요일까지는 닫혀 있다.
공휴일과 조기 마감은 다루지 않는다.
"""

import re
from datetime import datetime, time

from app.nh.client import NHClient
from app.nh.domestic.market_hours import MarketSession
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.values import text

PATH = "/trade/v1/overseas/market-operations"
WINDOW_PATTERN = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*~\s*(\d{1,2}):(\d{2})\s*$")
PRODUCT_PATTERN = re.compile(r"^(.+?)[FGHJKMNQUVXZ]\d{2}$")

Window = tuple[time, time]


def product_code(symbol: str) -> str:
    """종목코드에서 품목코드를 뽑는다. 예: `ZNZ26` → `ZN`. 형식이 다르면 그대로 돌려준다."""
    match = PRODUCT_PATTERN.match(symbol)
    return match.group(1) if match else symbol


def exchange_name(exchange: str) -> str:
    """`FCME` → `CME`. 장운영 조회는 선물·옵션 접두어가 없는 거래소 코드를 받는다."""
    return exchange[1:] if len(exchange) > 3 and exchange[0] in "FO" else exchange


def parse_window(value: str) -> Window | None:
    match = WINDOW_PATTERN.match(value or "")
    if not match:
        return None
    start_hour, start_minute, end_hour, end_minute = (int(part) for part in match.groups())
    try:
        return time(start_hour, start_minute), time(end_hour % 24, end_minute)
    except ValueError:
        return None


def session(window: Window, at: datetime) -> MarketSession:
    start, end = window
    now, weekday = at.time(), at.weekday()
    if start == end:
        return "regular" if weekday < 5 else "closed"
    if end < start:
        evening = now >= start and weekday <= 4  # 월~금 저녁에 시작
        morning = now < end and 1 <= weekday <= 5  # 화~토 아침에 이어서 끝남
        return "regular" if evening or morning else "closed"
    return "regular" if start <= now < end and weekday < 5 else "closed"


def fetch_window(client: NHClient, exchange: str, code: str) -> Window | None:
    """종목의 품목 거래시간. 응답에 없거나 읽을 수 없으면 `None`이다."""
    product = product_code(code)
    payload = {"fut_opt_div_cd": "F", "exch_cd": exchange_name(exchange), "prd_cd": "2", "prd_nm": product}
    body = client.call(PATH, payload, Limit.ACCOUNT)
    rows = body.get("Occurs1") or []
    if not isinstance(rows, list):
        raise NHError(f"{PATH} 응답의 Occurs1 형식이 올바르지 않습니다")
    for row in rows:
        if text(row.get("occurs1_prd_cd")) == product:
            return parse_window(text(row.get("occurs1_trd_tm_inf")))
    return None
