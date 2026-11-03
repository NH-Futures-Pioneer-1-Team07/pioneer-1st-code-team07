"""해외 시세 조회: 분봉·일봉과 현재가.

봉 시각(`occurs1_ref_dt`, `occurs1_exch_tm`)은 응답의 거래소 시간 그대로 쓴다. 한국 시간으로의 변환과
봉 시각이 시작인지 마감인지는 모의환경 호출로 확인해야 한다.
"""

from datetime import date, datetime, timedelta
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
# 한 번에 조회하는 기간(일). 5분봉 기준 하루 약 288개라 요청 한도(9999건) 안에 들어온다.
CHUNK_DAYS = 7


def fetch_quote(client: NHClient, exchange: str, code: str) -> Quote:
    """현재가. 응답에 최종거래일이 없어 `last_trading_day`는 `None`이다."""
    body = client.call(PRICE_PATH, {"Iccurs1": {"iccurs1_exch_cd": exchange, "iccurs1_sym": code}}, Limit.QUOTE)
    rows = _rows(body)
    last_price = number(rows[0].get("occurs1_last_pric")) if rows else None
    return Quote(code, last_price, None)


def fetch_minute_bars(
    client: NHClient, exchange: str, code: str, *, minutes: int, start: date, end: date
) -> list[Bar]:
    """분봉을 `start`부터 `end`까지(양 끝 포함) 오래된 순서로 돌려준다. 해외 시장은 주말을 건너뛰지 않고 그대로 조회한다."""
    if end < start:
        raise ValueError("조회 끝 날짜가 시작 날짜보다 빠릅니다")
    bars: dict[datetime, Bar] = {}
    day = start
    while day <= end:
        chunk_end = min(day + timedelta(days=CHUNK_DAYS - 1), end)
        payload = {
            "exch_cd": exchange,
            "sym": code,
            "inq_strt_dt": day.strftime("%Y%m%d"),
            "strt_tm": "000000",
            "inq_ed_dt": chunk_end.strftime("%Y%m%d"),
            "ed_tm": "235959",
            "req_qty": str(MAX_ROWS),
            "dcnt": str(minutes),
            "cidx_yn": "0",
            "nxt_key": "99999999",
        }
        for row in _rows(client.call(MINUTE_PATH, payload, Limit.QUOTE)):
            bar = parse_minute_bar(row)
            if bar is not None:
                bars[bar.time] = bar
        day = chunk_end + timedelta(days=1)
    return [bars[time] for time in sorted(bars)]


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
