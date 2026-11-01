"""시세 조회: 국내 분봉과 현재가."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Literal

from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.values import day as _day
from app.nh.values import number as _number
from strategy_base.models import Bar

MINUTE_PATH = "/trade/v1/domestic/chart-minute"
PRICE_PATH = "/trade/v1/domestic/price"

DAY_SESSION = "1"
MAX_ROWS = 9999

# 응답의 봉 시각(`occurs1_exch_tm`)이 봉의 시작인지 마감인지는 모의환경 호출로 확인해야 한다.
TimeMarks = Literal["start", "end"]


@dataclass(frozen=True)
class Quote:
    code: str
    last_price: float | None
    last_trading_day: date | None


def fetch_quote(client: NHClient, code: str) -> Quote:
    """현재가와 최종거래일."""
    body = client.call(PRICE_PATH, {"sym": code}, Limit.QUOTE)
    return Quote(code, _number(body.get("last_pric")), _day(body.get("lst_trd_dt")))


def fetch_minute_bars(
    client: NHClient,
    code: str,
    *,
    minutes: int,
    start: date,
    end: date,
    time_marks: TimeMarks = "start",
) -> list[Bar]:
    """주간 분봉을 `start`부터 `end`까지(양 끝 포함) 오래된 순서로 돌려준다.

    하루씩 나눠 조회한다. 주말은 건너뛰고, 휴장일은 빈 응답이라 봉이 없다.
    `time_marks`가 `"end"`이면 응답의 봉 시각을 봉이 마감한 시각으로 보고 `minutes`분을 빼서
    `Bar.time`(봉이 시작한 시각)으로 바꾼다.
    """
    if end < start:
        raise ValueError("조회 끝 날짜가 시작 날짜보다 빠릅니다")
    bars: dict[datetime, Bar] = {}
    day = start
    while day <= end:
        if day.weekday() < 5:
            for bar in _fetch_day(client, code, minutes, day, time_marks):
                bars[bar.time] = bar
        day += timedelta(days=1)
    return [bars[time] for time in sorted(bars)]


def _fetch_day(client: NHClient, code: str, minutes: int, day: date, time_marks: TimeMarks) -> list[Bar]:
    text = day.strftime("%Y%m%d")
    payload = {
        "nght_tp": DAY_SESSION,
        "sym": code,
        "inq_strt_dt": text,
        "strt_tm": "000000",
        "inq_ed_dt": text,
        "ed_tm": "235959",
        "req_qty": str(MAX_ROWS),
        "dcnt": str(minutes),
        "cidx_yn": "0",
        "nxt_key": "99999999",
        "fut_cidx_exp_mod": "0",
    }
    body = client.call(MINUTE_PATH, payload, Limit.QUOTE)
    rows = body.get("Occurs1") or []
    if not isinstance(rows, list):
        raise NHError("분봉 응답의 Occurs1 형식이 올바르지 않습니다")
    shift = timedelta(minutes=minutes) if time_marks == "end" else timedelta()
    bars = []
    for row in rows:
        bar = parse_bar(row, shift)
        if bar is not None:
            bars.append(bar)
    return bars


def parse_bar(row: dict[str, Any], shift: timedelta = timedelta()) -> Bar | None:
    day, clock = str(row.get("occurs1_ref_dt") or "").strip(), str(row.get("occurs1_exch_tm") or "").strip()
    high, low = _number(row.get("occurs1_high_pric")), _number(row.get("occurs1_low_pric"))
    close, volume = _number(row.get("occurs1_close_pric")), _number(row.get("occurs1_cum_trd_qty"))
    open_ = _number(row.get("occurs1_open_pric"))
    if len(day) != 8 or len(clock) != 6 or None in (high, low, close, volume):
        return None
    try:
        moment = datetime.strptime(day + clock, "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return Bar(time=moment - shift, high=high, low=low, close=close, volume=int(volume), open=open_)
