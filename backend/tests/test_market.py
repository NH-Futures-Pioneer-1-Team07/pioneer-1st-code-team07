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

CODE = "A116B000"

QUOTE = {
    "chg_sign": "+", "sym_exch": CODE, "sym_nm": "삼성전자   F 202611 (  10)", "last_pric": "243000",
    "ref_pric": "223000", "chg": "20000", "rt": "8.97", "trd_qty": "2711873", "open_pric": "229000",
    "high_pric": "243500", "low_pric": "228500", "lst_trd_dt": "20261112", "mltplr": "10", "rem_dy": "16",
    "up": "245000", "lo": "201000",
}


def minute_row(day, clock, o, h, l, c, v):
    return {"occurs1_ref_dt": day, "occurs1_exch_tm": clock, "occurs1_open_pric": f"{o}.0", "occurs1_high_pric": f"{h}.0",
            "occurs1_low_pric": f"{l}.0", "occurs1_close_pric": f"{c}.0", "occurs1_cum_trd_qty": str(v)}


def daily_row(day, o, h, l, c, v):
    return {"occurs1_ref_dt": day, "occurs1_open_pric": f"{o}.0", "occurs1_high_pric": f"{h}.0",
            "occurs1_low_pric": f"{l}.0", "occurs1_close_pric": f"{c}.0", "occurs1_cum_trd_qty": str(v)}


MINUTES = {"nrec": "3", "Occurs1": [  # 최신 봉이 먼저 온다
    minute_row("20261028", "090600", 70, 80, 60, 75, 30),
    minute_row("20261028", "090300", 65, 72, 62, 70, 20),
    minute_row("20261027", "154500", 60, 66, 59, 65, 10),
]}
DAILY = {"nrec": "3", "Occurs1": [
    daily_row("20261028", 229000, 243500, 228500, 243000, 2711873),
    daily_row("20261027", 220000, 226000, 220000, 223000, 2430621),
    daily_row("20261026", 214000, 216500, 211500, 213500, 2279023),
]}
BOOK = {
    "sym": CODE, "qt_tm": "154500", "ask_qty": "17514", "bid_qty": "104867", "last_pric": "243000", "rt": "8.97", "nrec": "10",
    "Occurs1": [{"occurs1_ask_best_pric": str(243000 + 500 * n), "occurs1_ask_qty": str(100 * (n + 1)),
                 "occurs1_bid_best_pric": str(242500 - 500 * n), "occurs1_bid_qty": str(50 * (n + 1))} for n in range(10)],
}


class Backend:
    def __init__(self, **bodies):
        self.bodies = bodies
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth-service/v1/token":
            return httpx.Response(200, json=TOKEN_BODY)
        self.calls.append((request.url.path, json.loads(request.content)))
        body = self.bodies[request.url.path.rsplit("/", 1)[-1]]
        return httpx.Response(200, json=body)


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
def make(tmp_path):
    def build(backend=None, **settings_kwargs):
        backend = backend or Backend(price=QUOTE, **{"chart-minute": MINUTES, "chart-daily": DAILY, "price-bid": BOOK})
        values = {"trading_env": "mock", "nh_app_key": "k", "nh_app_secret": "s",
                  "strategies_dir": tmp_path / "s", "runs_dir": tmp_path / "r"}
        settings = Settings(**{**values, **settings_kwargs})
        app = create_app(settings)
        clock = Clock()
        client = NHClient(settings, http_client=httpx.Client(transport=httpx.MockTransport(backend)), limiter=FakeLimiter())
        app.state.market = MarketService(settings, client=client, clock=clock, now=lambda: datetime(2026, 10, 28, 10, 0))
        return TestClient(app), backend, clock

    return build


def test_시세는_종목명_월물_만기_현재가_등락_거래량을_돌려준다(make):
    client, backend, _ = make()

    response = client.get(f"/api/market/{CODE}/quote")

    assert response.status_code == 200
    assert response.json() == {
        "code": CODE, "name": "삼성전자 F 202611 ( 10)", "contract": "2026.11", "expiry": "2026-11-12",
        "price": 243000.0, "change": 20000.0, "change_rate": 8.97, "volume": 2711873,
        "open": 229000.0, "high": 243500.0, "low": 228500.0, "prev_close": 223000.0,
        "upper_limit": 245000.0, "lower_limit": 201000.0, "multiplier": 10, "remaining_days": 16,
        "market_session": "regular",
    }
    assert backend.calls == [("/trade/v1/domestic/price", {"sym": CODE})]


def test_하락_종목의_전일대비와_등락률은_음수다(make):
    falling = {**QUOTE, "chg_sign": "-", "chg": "5000", "rt": "2.2"}
    client, _, _ = make(Backend(price=falling))

    body = client.get(f"/api/market/{CODE}/quote").json()

    assert (body["change"], body["change_rate"]) == (-5000.0, -2.2)


def test_이미_음수로_오면_그대로_두고_보합은_양수_부호가_없다(make):
    client, _, _ = make(Backend(price={**QUOTE, "chg_sign": "-", "chg": "-5000", "rt": "-2.2"}))
    assert client.get(f"/api/market/{CODE}/quote").json()["change"] == -5000.0

    client, _, _ = make(Backend(price={**QUOTE, "chg_sign": "", "chg": "0", "rt": "0"}))
    body = client.get(f"/api/market/{CODE}/quote").json()
    assert (body["change"], body["change_rate"]) == (0.0, 0.0)


def test_분봉은_오래된_순서로_돌아오고_시각은_봉_시작_시각이다(make):
    client, backend, _ = make()

    response = client.get(f"/api/market/{CODE}/candles", params={"interval": "3", "count": 200})

    assert response.status_code == 200
    assert response.json() == [
        {"time": "2026-10-27T15:45:00", "open": 60.0, "high": 66.0, "low": 59.0, "close": 65.0, "volume": 10},
        {"time": "2026-10-28T09:03:00", "open": 65.0, "high": 72.0, "low": 62.0, "close": 70.0, "volume": 20},
        {"time": "2026-10-28T09:06:00", "open": 70.0, "high": 80.0, "low": 60.0, "close": 75.0, "volume": 30},
    ]
    [(path, payload)] = backend.calls
    assert path == "/trade/v1/domestic/chart-minute"
    assert (payload["dcnt"], payload["req_qty"], payload["nght_tp"], payload["inq_ed_dt"]) == ("3", "200", "1", "99999999")


def test_분봉_개수가_요청보다_많으면_최근_것만_돌려준다(make):
    client, _, _ = make()

    body = client.get(f"/api/market/{CODE}/candles", params={"interval": "5", "count": 2}).json()

    assert [c["time"] for c in body] == ["2026-10-28T09:03:00", "2026-10-28T09:06:00"]


def test_일봉은_날짜로_오래된_순서로_돌아온다(make):
    client, backend, _ = make()

    body = client.get(f"/api/market/{CODE}/candles", params={"interval": "day", "count": 2}).json()

    assert body == [
        {"time": "2026-10-27", "open": 220000.0, "high": 226000.0, "low": 220000.0, "close": 223000.0, "volume": 2430621},
        {"time": "2026-10-28", "open": 229000.0, "high": 243500.0, "low": 228500.0, "close": 243000.0, "volume": 2711873},
    ]
    assert backend.calls[0][0] == "/trade/v1/domestic/chart-daily"
    assert backend.calls[0][1]["req_qty"] == "2"


def test_읽을_수_없는_봉은_건너뛴다(make):
    broken = {"Occurs1": [minute_row("20261028", "090300", 65, 72, 62, 70, 20), {"occurs1_ref_dt": "", "occurs1_exch_tm": "090600"}]}
    client, _, _ = make(Backend(**{"chart-minute": broken}))

    assert len(client.get(f"/api/market/{CODE}/candles", params={"interval": "3"}).json()) == 1


def test_호가는_열_단계까지_돌아온다(make):
    client, backend, _ = make()

    body = client.get(f"/api/market/{CODE}/orderbook").json()

    assert body["code"] == CODE and body["time"] == "154500" and body["price"] == 243000.0 and body["change_rate"] == 8.97
    assert (body["total_ask_quantity"], body["total_bid_quantity"]) == (17514, 104867)
    assert len(body["levels"]) == 10
    assert body["levels"][0] == {"ask_price": 243000.0, "ask_quantity": 100, "bid_price": 242500.0, "bid_quantity": 50}
    assert body["levels"][9]["ask_price"] == 247500.0
    assert backend.calls == [("/trade/v1/domestic/price-bid", {"exch_cd": "KSP", "sym": CODE})]


@pytest.mark.parametrize("params", [{"interval": "2"}, {"interval": "week"}, {"count": 0}, {"count": 1001}])
def test_허용하지_않는_차트_조건은_422다(make, params):
    client, backend, _ = make()

    assert client.get(f"/api/market/{CODE}/candles", params=params).status_code == 422
    assert backend.calls == []


def test_종목코드_형식이_틀리면_422이고_NH를_부르지_않는다(make):
    client, backend, _ = make()

    for path in ("quote", "candles", "orderbook"):
        assert client.get(f"/api/market/A1/{path}").status_code == 422
        assert client.get(f"/api/market/..%2Fx/{path}").status_code in (404, 422)
    assert backend.calls == []


def test_인증_정보가_없으면_503이다(make):
    client, backend, _ = make(nh_app_key=None, nh_app_secret=None)

    for path in ("quote", "candles", "orderbook"):
        assert client.get(f"/api/market/{CODE}/{path}").status_code == 503
    assert backend.calls == []


def test_NH가_거절하면_502이고_원인_종류를_알린다(make):
    refused = Backend(price={"errorCode": "EGW053", "errorMessage": "호출 불가"})
    client, _, _ = make(refused)

    response = client.get(f"/api/market/{CODE}/quote")

    assert response.status_code == 502 and "GatewayError" in response.json()["detail"]


def test_같은_요청은_보관_시간_안에_NH를_다시_부르지_않는다(make):
    client, backend, clock = make()

    client.get(f"/api/market/{CODE}/quote")
    client.get(f"/api/market/{CODE}/quote")
    clock.now = 0.5
    client.get(f"/api/market/{CODE}/quote")
    assert len(backend.calls) == 1

    clock.now = 1.5
    client.get(f"/api/market/{CODE}/quote")
    assert len(backend.calls) == 2


def test_차트와_호가는_요청_조건별로_따로_보관한다(make):
    client, backend, clock = make()

    client.get(f"/api/market/{CODE}/candles", params={"interval": "3"})
    client.get(f"/api/market/{CODE}/candles", params={"interval": "5"})
    client.get(f"/api/market/{CODE}/candles", params={"interval": "3"})
    assert len(backend.calls) == 2

    clock.now = 2.5
    client.get(f"/api/market/{CODE}/candles", params={"interval": "3"})
    assert len(backend.calls) == 3
