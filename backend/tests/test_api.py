import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.test_registry import make_folder


@pytest.fixture
def client(tmp_path):
    make_folder(tmp_path, "week02_sample")
    make_folder(tmp_path, "broken", manifest=None)
    settings = Settings(trading_env="mock", strategies_dir=tmp_path, runs_dir=tmp_path / "runs")
    return TestClient(create_app(settings))


def test_헬스체크가_응답한다(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "trading_env": "mock"}


def test_전략_목록에는_등록된_전략만_나온다(client):
    response = client.get("/api/strategies")

    assert response.status_code == 200
    assert response.json() == [{"id": "week02_sample", "name": "테스트 전략", "description": "테스트용"}]


def test_전략_상세가_매니페스트_내용을_돌려준다(client):
    response = client.get("/api/strategies/week02_sample")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "테스트 전략"
    assert body["instruments"] == [{"name": "삼성전자선물", "code": "A116B000", "multiplier": None}]
    assert body["bar"] == {"unit": "minute", "size": 3}
    assert body["parameters"] == {"quantity": {"default": 5, "description": "수량"}}


def test_없는_전략은_404다(client):
    assert client.get("/api/strategies/unknown").status_code == 404
