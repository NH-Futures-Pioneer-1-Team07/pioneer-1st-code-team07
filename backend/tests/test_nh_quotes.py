from datetime import date, datetime

import httpx
import pytest

from app.config import Settings
from app.nh.client import NHClient
from app.nh.domestic.quotes import fetch_minute_bars, fetch_quote
from app.nh.errors import NHError
from tests.test_nh_client import FakeLimiter, Server


def row(day, clock, high, low, close, volume):
    return {
        "occurs1_ref_dt": day,
        "occurs1_exch_tm": clock,
        "occurs1_open_pric": "0",
        "occurs1_high_pric": str(high),
        "occurs1_low_pric": str(low),
        "occurs1_close_pric": str(close),
        "occurs1_cum_trd_qty": str(volume),
    }


def make(*responses):
    server = Server(*responses)
    settings = Settings(trading_env="mock", nh_app_key="k", nh_app_secret="s")
    client = NHClient(
        settings, http_client=httpx.Client(transport=httpx.MockTransport(server)), limiter=FakeLimiter()
    )
    return client, server


def body_of(request):
    import json

    return json.loads(request.content)


def test_분봉을_Bar로_바꾸고_오래된_순서로_정렬한다():
    client, _ = make(
        {
            "nrec": "3",
            "Occurs1": [  # 최신 봉이 먼저 오는 경우
                row("20261027", "090600", "70,700", 70400, 70600, 80),
                row("20261027", "090300", 70500, 70200, 70400, 120),
                row("20261027", "090000", 70300, 70000, 70200, 100),
            ],
        }
    )

    bars = fetch_minute_bars(client, "A116B000", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27))

    assert [(b.time, b.high, b.low, b.close, b.volume) for b in bars] == [
        (datetime(2026, 10, 27, 9, 0), 70300, 70000, 70200, 100),
        (datetime(2026, 10, 27, 9, 3), 70500, 70200, 70400, 120),
        (datetime(2026, 10, 27, 9, 6), 70700, 70400, 70600, 80),
    ]


def test_요청_형식은_명세를_따른다():
    client, server = make({"Occurs1": []})

    fetch_minute_bars(client, "A116B000", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27))

    [request] = server.api_requests()
    assert request.url.path == "/trade/v1/domestic/chart-minute"
    assert body_of(request) == {
        "nght_tp": "1",
        "sym": "A116B000",
        "inq_strt_dt": "20261027",
        "strt_tm": "000000",
        "inq_ed_dt": "20261027",
        "ed_tm": "235959",
        "req_qty": "9999",
        "dcnt": "3",
        "cidx_yn": "0",
        "nxt_key": "99999999",
        "fut_cidx_exp_mod": "0",
    }


def test_여러_날의_기간은_하루씩_조회해_합치고_주말은_건너뛴다():
    # 2026-10-23(금) ~ 2026-10-27(화): 금, 월, 화만 조회한다
    client, server = make(
        {"Occurs1": [row("20261023", "090000", 3, 1, 2, 10)]},
        {"Occurs1": [row("20261026", "090000", 6, 4, 5, 20)]},
        {"Occurs1": [row("20261027", "090000", 9, 7, 8, 30)]},
    )

    bars = fetch_minute_bars(client, "A", minutes=3, start=date(2026, 10, 23), end=date(2026, 10, 27))

    assert [body_of(r)["inq_strt_dt"] for r in server.api_requests()] == ["20261023", "20261026", "20261027"]
    assert [b.time.date().isoformat() for b in bars] == ["2026-10-23", "2026-10-26", "2026-10-27"]


def test_같은_시각의_봉은_하나만_남긴다():
    client, _ = make({"Occurs1": [row("20261027", "090000", 1, 1, 1, 10), row("20261027", "090000", 2, 2, 2, 20)]})

    bars = fetch_minute_bars(client, "A", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27))

    assert len(bars) == 1


def test_응답_시각이_마감_시각이면_봉_길이를_빼서_시작_시각으로_바꾼다():
    client, _ = make({"Occurs1": [row("20261027", "090300", 1, 1, 1, 10)]})

    bars = fetch_minute_bars(
        client, "A", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27), time_marks="end"
    )

    assert bars[0].time == datetime(2026, 10, 27, 9, 0)


def test_읽을_수_없는_줄은_건너뛴다():
    client, _ = make(
        {
            "Occurs1": [
                row("20261027", "090000", 1, 1, 1, 10),
                row("", "090300", 1, 1, 1, 10),
                row("20261027", "090600", "", 1, 1, 10),
                row("20261027", "25xx00", 1, 1, 1, 10),
            ]
        }
    )

    bars = fetch_minute_bars(client, "A", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27))

    assert len(bars) == 1


def test_응답에_줄이_없으면_빈_목록이다():
    client, _ = make({"nrec": "0"})

    assert fetch_minute_bars(client, "A", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27)) == []


def test_Occurs1_형식이_이상하면_오류다():
    client, _ = make({"Occurs1": "x"})

    with pytest.raises(NHError):
        fetch_minute_bars(client, "A", minutes=3, start=date(2026, 10, 27), end=date(2026, 10, 27))


def test_끝_날짜가_시작보다_빠르면_오류다():
    client, _ = make()

    with pytest.raises(ValueError):
        fetch_minute_bars(client, "A", minutes=3, start=date(2026, 10, 28), end=date(2026, 10, 27))


def test_현재가와_최종거래일을_돌려준다():
    client, server = make({"last_pric": "70,500", "lst_trd_dt": "20261112"})

    quote = fetch_quote(client, "A116B000")

    assert (quote.code, quote.last_price, quote.last_trading_day) == ("A116B000", 70500, date(2026, 11, 12))
    assert body_of(server.api_requests()[0]) == {"sym": "A116B000"}
    assert server.api_requests()[0].url.path == "/trade/v1/domestic/price"


def test_현재가_응답이_비어_있으면_값이_없다():
    client, _ = make({"last_pric": "", "lst_trd_dt": ""})

    quote = fetch_quote(client, "A")

    assert (quote.last_price, quote.last_trading_day) == (None, None)
