import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.sweep.store import SweepStore

ID_A, ID_B, ID_MISSING = "a" * 16, "b" * 16, "c" * 16


def result(result_id, net):
    return {"id": result_id, "strategy_id": "week03_stub", "params": {"a": 1}, "start": "2026-10-01", "end": "2026-10-10",
            "slippage_ticks": 1, "initial_capital": 1000, "summary": {"net_pnl": net}, "daily_equity": [{"time": "2026-10-02T00:00:00", "equity": 1000 + net}]}


TRADE = {"kind": "trade", "entry_id": "e1", "net_pnl": 5, "exit_reason": "청산"}
FILL = {"kind": "fill", "entry_id": "e1", "price": 1.0}


@pytest.fixture
def client(tmp_path):
    settings = Settings(trading_env="mock", strategies_dir=tmp_path / "strategies", runs_dir=tmp_path / "runs",
                        sweeps_dir=tmp_path / "sweeps", reports_dir=tmp_path / "reports")
    (tmp_path / "strategies").mkdir()
    store = SweepStore(settings.sweeps_dir)
    store.append("week03_stub", result(ID_A, 10), [TRADE, FILL, FILL])
    store.append("week03_stub", result(ID_B, -5), [])
    return TestClient(create_app(settings))


def test_결과는_요청한_순서로_돌려주고_없는_id는_뺀다(client):
    rows = client.get(f"/api/sweeps/week03_stub/results?ids={ID_B},{ID_MISSING},{ID_A}").json()

    assert [row["id"] for row in rows] == [ID_B, ID_A]
    assert rows[1]["summary"] == {"net_pnl": 10} and rows[1]["daily_equity"][0]["equity"] == 1010


def test_결과를_찾는_전략이_없으면_빈_목록이다(client):
    assert client.get(f"/api/sweeps/week03_none/results?ids={ID_A}").json() == []


@pytest.mark.parametrize("ids", ["", "abc", f"{ID_A},../x", "A" * 16, ",".join(f"{n:016x}" for n in range(61))])
def test_잘못된_ids는_422다(client, ids):
    assert client.get(f"/api/sweeps/week03_stub/results?ids={ids}").status_code == 422


def test_거래_기록은_거래와_체결로_나눠_돌려준다(client):
    body = client.get(f"/api/sweeps/week03_stub/trades/{ID_A}").json()

    assert body == {"trades": [TRADE], "fills": [FILL, FILL]}


def test_없는_거래_기록과_잘못된_id와_전략은_404다(client):
    assert client.get(f"/api/sweeps/week03_stub/trades/{ID_MISSING}").status_code == 404
    assert client.get(f"/api/sweeps/week03_stub/trades/{ID_B}").status_code == 404  # 거래가 하나도 없는 조합
    assert client.get("/api/sweeps/week03_stub/trades/..%2Fsecret").status_code == 404
    assert client.get(f"/api/sweeps/Bad-Name/trades/{ID_A}").status_code == 404
    assert client.get(f"/api/sweeps/Bad-Name/results?ids={ID_A}").status_code == 404
