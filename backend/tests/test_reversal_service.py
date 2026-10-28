import shutil
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.config import BACKEND_DIR, Settings
from app.main import create_app
from app.runners.service import LoadedData
from strategy_base.models import Bar
from tests.test_backtest_service import FakeProbe
from tests.test_reversal_strategy import BUY_ROWS


ID = "week02_samsung_futures_reversal"
DAY = date(2026, 10, 27)


def test_frontend_backtest_api_uses_new_strategy_and_one_minute_execution(tmp_path):
    strategies = tmp_path/"strategies"
    shutil.copytree(BACKEND_DIR/"strategies"/ID, strategies/ID)
    start = datetime(2026, 10, 27, 9)
    bars = [Bar(start+timedelta(minutes=i*3), 200000+h*500, 200000+l*500,
                200000+c*500, v, 200000+c*500) for i,(h,l,c,v) in enumerate(BUY_ROWS)]
    bars.extend([Bar(start+timedelta(minutes=36), 210000, 207000, 209000, 90, 208000),
                 Bar(start+timedelta(minutes=39), 213000, 208000, 212000, 90, 209000),
                 Bar(start.replace(hour=15, minute=30), 212000, 212000, 212000, 90, 212000)])
    minute_bars = []
    for b in bars:
        minute_bars.extend([Bar(b.time, b.high, b.low, b.close, b.volume, b.open),
                           Bar(b.time+timedelta(minutes=1), b.close, b.close, b.close, 0, b.close),
                           Bar(b.time+timedelta(minutes=2), b.close, b.close, b.close, 0, b.close)])
    calls = []
    def loader(code, minutes, first, last, progress):
        calls.append(minutes)
        progress(1,1)
        return LoadedData({DAY: bars if minutes == 3 else minute_bars}, date(2026,11,12))
    app = create_app(Settings(trading_env="mock", nh_app_key="test", nh_app_secret="test",
                              strategies_dir=strategies, runs_dir=tmp_path/"runs"))
    service = app.state.backtests
    service._loader_factory = lambda: loader
    service._probe_factory = lambda code, minutes: FakeProbe()
    with TestClient(app) as client:
        assert client.get("/api/strategies").json()[0]["id"] == ID
        response = client.post("/api/backtests", json=dict(strategy_id=ID, start_date=str(DAY), end_date=str(DAY),
                              initial_capital=50000000, slippage_ticks=1))
        assert response.status_code == 202
        service.join(10)
        r = response.json()
        detail = client.get(f"/api/runs/{ID}/backtest/{r['run_id']}").json()
        assert detail["meta"]["status"] == "completed"
        assert detail["result"]["trade_count"] == 1
        assert detail["meta"]["assumptions"]["fill"]["price_minutes"] == 1
        assert detail["meta"]["assumptions"]["slippage"]["tick_size"] == 500
        assert calls == [3,1]
