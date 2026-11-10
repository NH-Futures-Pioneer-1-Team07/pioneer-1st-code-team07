import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.nh.domestic.market import MarketService

LEGS = [("ZFZ26", 3), ("ZNZ26", -2)]


def quote(code, price, prev, volume, **extra):
    return {"code": code, "price": price, "prev_close": prev, "volume": volume, "open": price - 1, "market_session": "regular", **extra}


def candle(time, open_, close, volume):
    return {"time": time, "open": open_, "high": close + 1, "low": open_ - 1, "close": close, "volume": volume}


@pytest.fixture
def service():
    service = MarketService.__new__(MarketService)
    quotes = {"ZFZ26": quote("ZFZ26", 104.0, 103.5, 500), "ZNZ26": quote("ZNZ26", 106.0, 105.0, 800)}
    service.quote = lambda code, market, exchange: quotes[code]
    candles = {
        "ZFZ26": [candle("2026-11-11T09:00:00", 104, 104.5, 10), candle("2026-11-11T09:05:00", 104.5, 105, 12), candle("2026-11-11T09:10:00", 105, 105, 0)],
        "ZNZ26": [candle("2026-11-11T09:05:00", 106, 106.5, 7), candle("2026-11-11T09:10:00", 106.5, 107, 9)],
    }
    service.candles = lambda code, interval, quantity, market, exchange: candles[code]
    return service


def test_스프레드_현재가는_두_종목을_비율대로_합친다(service):
    result = service.spread_quote("ZFZ26-ZNZ26", LEGS, "FCME")

    assert result["price"] == pytest.approx(3 * 104.0 - 2 * 106.0)
    assert result["prev_close"] == pytest.approx(3 * 103.5 - 2 * 105.0)
    assert result["change"] == pytest.approx(result["price"] - result["prev_close"])
    assert result["change_rate"] == pytest.approx(result["change"] / abs(result["prev_close"]) * 100)
    assert result["volume"] == 500
    assert result["market_session"] == "regular"
    assert result["expiry"] is None


def test_스프레드_차트는_같은_시각의_유효한_봉만_합친다(service):
    rows = service.spread_candles(LEGS, "5", 100, "FCME")

    assert [row["time"] for row in rows] == ["2026-11-11T09:05:00"]
    row = rows[0]
    assert row["close"] == pytest.approx(3 * 105 - 2 * 106.5)
    assert row["open"] == pytest.approx(3 * 104.5 - 2 * 106)
    assert row["high"] == max(row["open"], row["close"]) and row["low"] == min(row["open"], row["close"])
    assert row["volume"] == 7


def test_스프레드_호가는_비어_있다(service):
    result = service.spread_orderbook("ZFZ26-ZNZ26")
    assert result["levels"] == [] and result["total_ask_quantity"] is None


@pytest.fixture
def client(service, tmp_path):
    app = create_app(
        Settings(trading_env="mock", nh_overseas_app_key="k", nh_overseas_app_secret="s", strategies_dir=tmp_path, runs_dir=tmp_path / "runs")
    )
    app.state.market = service
    service.has_credentials = lambda market: True
    return TestClient(app)


BASE = {"market": "overseas", "exchange": "FCME", "legs": "ZFZ26:3,ZNZ26:-2"}


def test_api가_legs가_있으면_스프레드로_계산한다(client):
    first = client.get("/api/market/ZFZ26-ZNZ26/quote", params=BASE)
    assert first.status_code == 200, first.text
    assert first.json()["price"] == pytest.approx(100.0)
    assert len(client.get("/api/market/ZFZ26-ZNZ26/candles", params=BASE).json()) == 1
    assert client.get("/api/market/ZFZ26-ZNZ26/orderbook", params=BASE).json()["levels"] == []


@pytest.mark.parametrize("legs", ["ZFZ26:3", "ZFZ26:3,ZFZ26:-2", "ZFZ26:0,ZNZ26:-2", "ZFZ26,ZNZ26", "ZFZ26:3,ZNZ26:-2,ZBZ26:1"])
def test_api가_잘못된_스프레드_구성을_거절한다(client, legs):
    response = client.get("/api/market/ZFZ26-ZNZ26/quote", params={**BASE, "legs": legs})
    assert response.status_code == 422


def test_스프레드는_해외_종목에만_쓸_수_있다(client):
    response = client.get("/api/market/ZFZ26-ZNZ26/quote", params={"market": "domestic", "legs": "ZFZ26:3,ZNZ26:-2"})
    assert response.status_code == 422
