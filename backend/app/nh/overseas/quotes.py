"""해외 시세 조회: 분봉·일봉과 현재가.

봉 시각(`occurs1_ref_dt`, `occurs1_exch_tm`)은 한국 시간이고 봉이 시작한 시각이다. 모의환경에서 진행 중인 봉의
거래량이 계속 늘어나는 것과 현재 시각으로 확인했다(2026-11-04). 그대로 `Bar.time`으로 쓴다.
"""

from datetime import date, datetime
from typing import Any

from app.nh.client import NHClient
from app.nh.domestic.quotes import Quote
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.values import number
from strategy_base.models import Bar

MINUTE_PATH = "/trade/v1/overseas/chart-minute"
DAILY_PATH = "/trade/v1/overseas/chart-daily"
PRICE_PATH = "/trade/v1/overseas/price"

MAX_ROWS = 9999
FIRST_KEY = "99999999"
# 분봉을 이어받는 쪽 수의 상한. 한 쪽은 약 495개라 5분봉 기준 쪽당 하루 반쯤이다.
MAX_PAGES = 600


def fetch_quote(client: NHClient, exchange: str, code: str) -> Quote:
    """현재가. 응답에 최종거래일이 없어 `last_trading_day`는 `None`이다."""
    body = client.call(PRICE_PATH, {"Iccurs1": {"iccurs1_exch_cd": exchange, "iccurs1_sym": code}}, Limit.QUOTE)
    rows = _rows(body)
    last_price = number(rows[0].get("occurs1_last_pric")) if rows else None
    return Quote(code, last_price, None)


def fetch_minute_bars(
    client: NHClient, exchange: str, code: str, *, minutes: int, start: date | None = None, end: date | None = None
) -> list[Bar]:
    """분봉을 `start`부터 `end`까지(양 끝 포함) 오래된 순서로 돌려준다. `start`가 없으면 조회되는 가장 오래된 봉까지 이어받는다.

    모의환경은 조회 기간을 무시하고 최신 봉부터 한 쪽(약 495개)씩 돌려주며, 다음 데이터 키로 과거 쪽을 이어받는다.
    그래서 기간 밖의 봉은 걸러 내고, `start`보다 오래된 봉이 나오면 멈춘다. 데이터 끝에 이르면 키가
    최신 쪽으로 되돌아가므로 쪽의 가장 오래된 봉이 앞 쪽보다 새로우면 멈춘다.
    """
    if start is not None and end is not None and end < start:
        raise ValueError("조회 끝 날짜가 시작 날짜보다 빠릅니다")
    payload = {
        "exch_cd": exchange,
        "sym": code,
        "inq_strt_dt": start.strftime("%Y%m%d") if start else "00000000",
        "strt_tm": "000000",
        "inq_ed_dt": end.strftime("%Y%m%d") if end else "99999999",
        "ed_tm": "235959",
        "req_qty": str(MAX_ROWS),
        "dcnt": str(minutes),
        "cidx_yn": "0",
        "nxt_key": FIRST_KEY,
    }
    bars: dict[datetime, Bar] = {}
    seen_keys: set[str] = set()
    oldest: datetime | None = None
    for _ in range(MAX_PAGES):
        body = client.call(MINUTE_PATH, payload, Limit.QUOTE)
        page = [bar for row in _rows(body) if (bar := parse_minute_bar(row)) is not None]
        if not page:
            break
        page_oldest = min(bar.time for bar in page)
        if oldest is not None and page_oldest >= oldest:
            break
        oldest = page_oldest
        for bar in page:
            bars[bar.time] = bar
        key = str(body.get("nxt_key") or "").strip()
        if not key or key == FIRST_KEY or key in seen_keys or (start is not None and page_oldest.date() < start):
            break
        seen_keys.add(key)
        payload = {**payload, "nxt_key": key}
    return [
        bars[time]
        for time in sorted(bars)
        if (start is None or time.date() >= start) and (end is None or time.date() <= end)
    ]


def fetch_daily_bars(client: NHClient, exchange: str, code: str, *, quantity: int) -> list[Bar]:
    """최근 일봉 `quantity`개를 오래된 순서로 돌려준다. `Bar.time`은 그날 0시다."""
    payload = {
        "exch_cd": exchange,
        "sym": code,
        "inq_strt_dt": "00000000",
        "inq_ed_dt": "99999999",
        "req_qty": str(quantity),
        "cidx_yn": "0",
        "nxt_key": "99999999",
    }
    bars = [bar for row in _rows(client.call(DAILY_PATH, payload, Limit.QUOTE)) if (bar := parse_daily_bar(row)) is not None]
    bars.sort(key=lambda bar: bar.time)
    return bars[-quantity:]


def parse_minute_bar(row: dict[str, Any]) -> Bar | None:
    day, clock = str(row.get("occurs1_ref_dt") or "").strip(), str(row.get("occurs1_exch_tm") or "").strip()
    if len(day) != 8 or len(clock) != 6:
        return None
    try:
        moment = datetime.strptime(day + clock, "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return _bar(moment, row)


def parse_daily_bar(row: dict[str, Any]) -> Bar | None:
    try:
        moment = datetime.strptime(str(row.get("occurs1_ref_dt") or "").strip(), "%Y%m%d")
    except ValueError:
        return None
    return _bar(moment, row)


def _bar(moment: datetime, row: dict[str, Any]) -> Bar | None:
    high, low = number(row.get("occurs1_high_pric")), number(row.get("occurs1_low_pric"))
    close, volume = number(row.get("occurs1_close_pric")), number(row.get("occurs1_cum_trd_qty"))
    if None in (high, low, close, volume):
        return None
    return Bar(time=moment, high=high, low=low, close=close, volume=int(volume), open=number(row.get("occurs1_open_pric")))


def _rows(body: dict[str, Any]) -> list[dict[str, Any]]:
    rows = body.get("Occurs1") or []
    if not isinstance(rows, list):
        raise NHError("해외 시세 응답의 Occurs1 형식이 올바르지 않습니다")
    return rows
