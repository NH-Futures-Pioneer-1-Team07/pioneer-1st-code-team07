from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.records.store import KST, RunStore

STARTED = datetime(2026, 10, 28, 9, 30, 12, tzinfo=KST)


@pytest.fixture
def setup(tmp_path):
    runs = tmp_path / "runs"
    store = RunStore(runs)
    recorder = store.start_run(
        strategy_id="week02_sample",
        strategy_name="샘플 전략",
        mode="backtest",
        instrument={"name": "삼성전자선물", "code": "A116B000"},
        params={"quantity": 5},
        started_at=STARTED,
        period={"start": "2026-10-20", "end": "2026-10-27"},
        initial_capital=1e8,
    )
    recorder.record("decision", time=datetime(2026, 10, 27, 10, 3), result="buy", reason="돌파")
    recorder.record("fill", time=datetime(2026, 10, 27, 10, 4), side="buy", price=70500)
    recorder.finish({"net_pnl": 1250000})
    settings = Settings(trading_env="mock", strategies_dir=tmp_path / "strategies", runs_dir=runs)
    return TestClient(create_app(settings)), recorder


def test_이력_목록을_돌려준다(setup):
    client, recorder = setup

    response = client.get("/api/runs")

    assert response.status_code == 200
    [run] = response.json()
    assert run["run_id"] == recorder.run_id
    assert run["net_pnl"] == 1250000
    assert run["period"] == {"start": "2026-10-20", "end": "2026-10-27"}


def test_이력_목록을_모드와_전략으로_거른다(setup):
    client, _ = setup

    assert client.get("/api/runs", params={"mode": "paper"}).json() == []
    assert len(client.get("/api/runs", params={"mode": "backtest", "strategy_id": "week02_sample"}).json()) == 1
    assert client.get("/api/runs", params={"strategy_id": "other"}).json() == []
    assert client.get("/api/runs", params={"mode": "live"}).status_code == 422


def test_이력_상세를_돌려준다(setup):
    client, recorder = setup

    response = client.get(f"/api/runs/week02_sample/backtest/{recorder.run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["params"] == {"quantity": 5}
    assert body["result"] == {"net_pnl": 1250000}


def test_없는_이력은_404다(setup):
    client, _ = setup

    assert client.get("/api/runs/week02_sample/backtest/20990101_000000").status_code == 404
    assert client.get("/api/runs/week02_sample/live/20261028_093012").status_code == 404
    assert client.get("/api/runs/week02_sample/backtest/20990101_000000/journal").status_code == 404


def test_기록을_종류와_구간으로_거르고_나눠서_조회한다(setup):
    client, recorder = setup
    url = f"/api/runs/week02_sample/backtest/{recorder.run_id}/journal"

    everything = client.get(url).json()
    fills = client.get(url, params={"kind": "fill"}).json()
    ranged = client.get(url, params={"start": "2026-10-27T10:04:00", "end": "2026-10-27T11:00:00"}).json()
    paged = client.get(url, params={"offset": 1, "limit": 1}).json()

    assert everything["total"] == 2
    assert [line["kind"] for line in fills["items"]] == ["fill"]
    assert [line["kind"] for line in ranged["items"]] == ["fill"]
    assert [line["kind"] for line in paged["items"]] == ["fill"]
    assert client.get(url, params={"kind": "memo"}).status_code == 422
    assert client.get(url, params={"limit": 0}).status_code == 422


def test_서버를_다시_시작하면_실행_중이던_기록은_중단으로_조회된다(tmp_path):
    runs = tmp_path / "runs"
    recorder = RunStore(runs).start_run(
        strategy_id="week02_sample",
        strategy_name="샘플",
        mode="paper",
        instrument={"name": "삼성전자선물"},
        params={},
        started_at=STARTED,
    )
    settings = Settings(trading_env="mock", strategies_dir=tmp_path / "strategies", runs_dir=runs)

    client = TestClient(create_app(settings))

    [run] = client.get("/api/runs").json()
    assert (run["run_id"], run["status"]) == (recorder.run_id, "interrupted")
