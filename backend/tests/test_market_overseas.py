import json
from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.nh.client import NHClient
from app.nh.domestic.market import MarketService
from tests.test_nh_client import TOKEN_BODY, FakeLimiter

CODE, EXCHANGE = "ZNZ26", "FCME"
PARAMS = {"market": "overseas", "exchange": EXCHANGE}

PRICE = {
    "nrec": "1",
    "Occurs1": [
        {
            "occurs1_sym": CODE, "occurs1_sym_nm": "10Year U.S. T-Notes", "occurs1_last_pric": "106.500000000",
            "occurs1_diff_rt": "-0.359375000", "occurs1_rt": "-0.33", "occurs1_open_pric": "106.734375000",
            "occurs1_high_pric": "106.906250000", "occurs1_low_pric": "106.375000000", "occurs1_pre_close_pric": "106.859375000",
            "occurs1_cum_trd_qty": "1748340",
        }
    ],
}
BOOK = {"sym": CODE, "qt_rcv_tm": "035928", "ask_qty": "25325", "bid_qty": "24883", "last_pric": "106.5", "rt": "-0.33"}
for step in range(1, 6):
    BOOK[f"ask_pric_{step}"] = str(106.5 + step / 64)
    BOOK[f"ask_qty_{step}"] = str(100 * step)
    BOOK[f"bid_pric_{step}"] = str(106.5 - (step - 1) / 64)
    BOOK[f"bid_qty_{step}"] = str(50 * step)


def minute_row(day, clock, close, volume):
    return {
        "occurs1_ref_dt": day, "occurs1_exch_tm": clock, "occurs1_open_pric": str(close), "occurs1_high_pric": str(close + 1),
        "occurs1_low_pric": str(close - 1), "occurs1_close_pric": str(close), "occurs1_cum_trd_qty": str(volume),
    }


MINUTES = {
    "nxt_key": "K1",
    "Occurs1": [minute_row("20261103", "000500", 106.4, 20), minute_row("20261103", "000000", 106.3, 10)],
}
MINUTES_OLDER = {"nxt_key": "K2", "Occurs1": [minute_row("20261102", "235500", 106.2, 5)]}
DAILY = {
    "Occurs1": [
        {"occurs1_ref_dt": day, "occurs1_open_pric": "106", "occurs1_high_pric": "107", "occurs1_low_pric": "105",
         "occurs1_close_pric": close, "occurs1_cum_trd_qty": "1000"}
        for day, close in (("20261103", "106.5"), ("20261102", "106.8"))
    ]
}


HOURS = {
    "nrec": "2",
    "Occurs1": [
        {"occurs1_prd_cd": "ZB", "occurs1_trd_tm_inf": "09:00 ~ 08:00"},
        {"occurs1_prd_cd": "ZN", "occurs1_trd_tm_inf": "08:00 ~ 07:00"},
    ],
}


class Backend:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.minutes = [MINUTES, MINUTES_OLDER]
        self.hours_error = False

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth-service/v1/token":
            return httpx.Response(200, json=TOKEN_BODY)
        payload = json.loads(request.content)
        self.calls.append((request.url.path, payload))
        name = request.url.path.rsplit("/", 1)[-1]
        if name == "chart-minute":
            return httpx.Response(200, json=self.minutes.pop(0) if self.minutes else {"Occurs1": []})
        if name == "market-operations":
            if self.hours_error:
                return httpx.Response(200, json={"errorCode": "EGW053", "errorMessage": "호출 불가"})
            return httpx.Response(200, json=HOURS)
        return httpx.Response(200, json={"price": PRICE, "bid-price": BOOK, "chart-daily": DAILY}[name])


@pytest.fixture
def make(tmp_path):
    def build(now=datetime(2026, 11, 4, 3, 50), **settings_kwargs):
        backend = Backend()
        values = {"_env_file": None, "trading_env": "mock", "nh_app_key": "k", "nh_app_secret": "s",
                  "nh_overseas_app_key": "ok", "nh_overseas_app_secret": "os",
                  "strategies_dir": tmp_path / "s", "runs_dir": tmp_path / "r"}
        settings = Settings(**{**values, **settings_kwargs})
        app = create_app(settings)
        service = MarketService(settings, now=lambda: now)
        service._overseas_client = NHClient(
            settings, market="overseas", http_client=httpx.Client(transport=httpx.MockTransport(backend)), limiter=FakeLimiter()
        )
        app.state.market = service
        return TestClient(app), backend

    return build


def test_해외_시세는_가격과_등락을_돌려주고_월물과_가격_제한은_비운다(make):
    client, backend = make()

    body = client.get(f"/api/market/{CODE}/quote", params=PARAMS).json()

    assert (body["code"], body["name"], body["price"], body["change"], body["change_rate"]) == (CODE, "10Year U.S. T-Notes", 106.5, -0.359375, -0.33)
    assert (body["open"], body["high"], body["low"], body["prev_close"], body["volume"]) == (106.734375, 106.90625, 106.375, 106.859375, 1748340)
    assert body["contract"] is None and body["upper_limit"] is None
    assert backend.calls[0] == ("/trade/v1/overseas/price", {"Iccurs1": {"iccurs1_exch_cd": EXCHANGE, "iccurs1_sym": CODE}})


def test_해외_분봉은_필요한_개수까지만_이어받고_오래된_순서로_돌려준다(make):
    client, backend = make()

    body = client.get(f"/api/market/{CODE}/candles", params={**PARAMS, "interval": "5", "count": 2}).json()

    assert [c["time"] for c in body] == ["2026-11-03T00:00:00", "2026-11-03T00:05:00"]
    assert len(backend.calls) == 1  # 첫 쪽에서 개수를 채웠으므로 더 받지 않는다


def test_해외_분봉이_모자라면_다음_쪽을_이어받는다(make):
    client, backend = make()

    body = client.get(f"/api/market/{CODE}/candles", params={**PARAMS, "interval": "5", "count": 3}).json()

    assert [c["close"] for c in body] == [106.2, 106.3, 106.4]
    assert backend.calls[0][1]["dcnt"] == "5" and backend.calls[1][1]["nxt_key"] == "K1"


def test_해외_일봉은_날짜로_오래된_순서로_돌아온다(make):
    client, _ = make()

    body = client.get(f"/api/market/{CODE}/candles", params={**PARAMS, "interval": "day", "count": 5}).json()

    assert [(c["time"], c["close"]) for c in body] == [("2026-11-02", 106.8), ("2026-11-03", 106.5)]


def test_해외_호가는_다섯_단계다(make):
    client, _ = make()

    body = client.get(f"/api/market/{CODE}/orderbook", params=PARAMS).json()

    assert len(body["levels"]) == 5
    assert (body["levels"][0]["ask_quantity"], body["levels"][4]["bid_quantity"]) == (100, 250)
    assert (body["total_ask_quantity"], body["total_bid_quantity"], body["price"]) == (25325, 24883, 106.5)


def test_해외_종목은_거래소_코드가_없으면_422이고_NH를_부르지_않는다(make):
    client, backend = make()

    for path in ("quote", "candles", "orderbook"):
        assert client.get(f"/api/market/{CODE}/{path}", params={"market": "overseas"}).status_code == 422
    assert backend.calls == []


def test_해외_키가_없으면_해외_변수_이름을_알려_주며_503이다(make):
    client, backend = make(nh_overseas_app_key=None, nh_overseas_app_secret=None)

    response = client.get(f"/api/market/{CODE}/quote", params=PARAMS)

    assert response.status_code == 503 and "NH_OVERSEAS_APP_KEY" in response.json()["detail"]
    assert backend.calls == []


def test_시장이_다르면_같은_코드도_따로_보관한다(make):
    client, backend = make()

    client.get(f"/api/market/{CODE}/quote", params=PARAMS)
    client.get(f"/api/market/{CODE}/quote", params=PARAMS)

    assert sum(path.endswith("/price") for path, _ in backend.calls) == 1  # 보관 시간 안의 같은 요청은 NH를 다시 부르지 않는다


def test_해외_장_종류는_품목의_거래시간으로_판정한다(make):
    client, backend = make(now=datetime(2026, 11, 4, 3, 50))  # 수요일 03:50, 08:00 ~ 07:00 구간 안

    body = client.get(f"/api/market/{CODE}/quote", params=PARAMS).json()

    assert body["market_session"] == "regular"
    hours_call = next(payload for path, payload in backend.calls if path.endswith("market-operations"))
    assert hours_call == {"fut_opt_div_cd": "F", "exch_cd": "CME", "prd_cd": "2", "prd_nm": "ZN"}


def test_거래시간_밖이면_장_마감이다(make):
    client, _ = make(now=datetime(2026, 11, 4, 7, 30))  # 07:00 ~ 08:00 휴장

    assert client.get(f"/api/market/{CODE}/quote", params=PARAMS).json()["market_session"] == "closed"


def test_거래시간을_못_구해도_시세는_돌려주고_장_종류만_모른다(make):
    client, backend = make()
    backend.hours_error = True

    response = client.get(f"/api/market/{CODE}/quote", params=PARAMS)

    assert response.status_code == 200 and response.json()["market_session"] == "unknown"


def test_거래시간은_보관해_다시_조회하지_않는다(make):
    client, backend = make()

    client.get(f"/api/market/{CODE}/quote", params=PARAMS)
    client.get(f"/api/market/{CODE}/candles", params={**PARAMS, "interval": "day"})
    client.get(f"/api/market/{CODE}/quote", params=PARAMS)

    assert sum(path.endswith("market-operations") for path, _ in backend.calls) == 1
