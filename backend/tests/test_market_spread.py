import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.nh.domestic.market import MarketService, TtlCache

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


# ---- 한 종목의 장 정보·봉이 비어 있을 때(예: 3년물) ----


def test_한_종목의_장_정보를_모르면_알_수_있는_값을_쓴다(service):
    quotes = {"ZFZ26": quote("ZFZ26", 104.0, 103.5, 500, market_session="unknown"), "ZNZ26": quote("ZNZ26", 106.0, 105.0, 800)}
    service.quote = lambda code, market, exchange: quotes[code]
    assert service.spread_quote("ZFZ26-ZNZ26", LEGS, "FCME")["market_session"] == "regular"
    quotes["ZNZ26"] = quote("ZNZ26", 106.0, 105.0, 800, market_session="unknown")
    assert service.spread_quote("ZFZ26-ZNZ26", LEGS, "FCME")["market_session"] == "unknown"


def test_분봉은_종목마다_넉넉히_받아_짝지은_뒤_최근_봉만_돌려준다(service):
    asked = []
    original = service.candles
    service.candles = lambda code, interval, quantity, market, exchange: (asked.append(quantity), original(code, interval, quantity, market, exchange))[1]
    rows = service.spread_candles(LEGS, "5", 100, "FCME")
    assert asked == [400, 400] and len(rows) == 1
    assert service.spread_candles(LEGS, "5", 1, "FCME") == rows[-1:]


def test_일봉이_비어_있으면_5분_스프레드를_영업일별로_합성한다(service):
    day = lambda d, h, m, o, c: candle(f"2026-11-{d:02d}T{h:02d}:{m:02d}:00", o, c, 10)  # noqa: E731
    candles = {
        "ZFZ26": [day(9, 9, 0, 100, 101), day(9, 9, 5, 101, 102), day(10, 9, 0, 102, 103)],
        "ZNZ26": [day(9, 9, 0, 50, 50), day(9, 9, 5, 50, 51), day(10, 9, 0, 51, 51)],
    }

    def fake(code, interval, quantity, market, exchange):
        return [] if interval == "day" else candles[code]

    service.candles = fake
    service._cache = TtlCache()
    rows = service.spread_candles([("ZFZ26", 1), ("ZNZ26", -1)], "day", 10, "FCME")
    assert [r["time"] for r in rows] == ["2026-11-09", "2026-11-10"]
    assert [r["close"] for r in rows] == [102 - 51, 103 - 51]
    assert rows[0]["open"] == 100 - 50 and rows[0]["volume"] == 20
