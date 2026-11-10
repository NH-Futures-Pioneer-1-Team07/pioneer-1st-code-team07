import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.reports.store import InvalidReport, split_front

FRONT = {
    "strategy_id": "week03_stub",
    "name": "민감도",
    "title": "민감도 보고서",
    "question": "무엇이 안정적인가?",
    "updated": "2026-11-10",
    "author": "테스트",
    "result_count": 4,
    "periods": [{"label": "전체", "start": "2026-10-01", "end": "2026-10-10", "kind": "full"}],
    "recommended": [{"label": "추천 조합", "role": "recommended", "params": {"a": 1}, "ids": {"전체": "abc"}}],
}


def write(root, strategy_id, name, front=FRONT, body="# 제목\n\n본문", table=None):
    folder = root / strategy_id / name
    folder.mkdir(parents=True)
    (folder / "report.md").write_text(f"---\n{json.dumps(front, ensure_ascii=False, indent=2)}\n---\n\n{body}\n", encoding="utf-8")
    if table is not None:
        (folder / "table.csv").write_text(table, encoding="utf-8")


@pytest.fixture
def make_client(tmp_path):
    def build():
        settings = Settings(trading_env="mock", strategies_dir=tmp_path / "strategies", runs_dir=tmp_path / "runs",
                            reports_dir=tmp_path / "reports")
        (tmp_path / "strategies").mkdir(exist_ok=True)
        return TestClient(create_app(settings)), tmp_path / "reports"

    return build


def test_보고서가_없으면_목록이_비어_있다(make_client):
    client, _ = make_client()

    assert client.get("/api/reports").json() == []


def test_목록은_갱신일이_최근인_순서이고_요약만_담는다(make_client):
    client, root = make_client()
    write(root, "week03_stub", "오래된", {**FRONT, "name": "오래된", "updated": "2026-11-01"})
    write(root, "week03_stub", "최근", {**FRONT, "name": "최근", "updated": "2026-11-10"})

    items = client.get("/api/reports").json()

    assert [item["name"] for item in items] == ["최근", "오래된"]
    assert items[0] == {"strategy_id": "week03_stub", "name": "최근", "title": "민감도 보고서", "question": "무엇이 안정적인가?",
                        "updated": "2026-11-10", "author": "테스트", "result_count": 4, "recommended": ["추천 조합"], "error": None}


def test_머리말이_깨진_보고서는_오류_사유와_함께_목록에_나온다(make_client):
    client, root = make_client()
    folder = root / "week03_stub" / "깨짐"
    folder.mkdir(parents=True)
    (folder / "report.md").write_text("---\n{json 아님\n---\n본문", encoding="utf-8")

    item = client.get("/api/reports").json()[0]

    assert item["name"] == "깨짐" and "JSON" in item["error"] and "title" not in item


def test_보고서_상세는_머리말_본문_비교표를_돌려준다(make_client):
    client, root = make_client()
    write(root, "week03_stub", "민감도", table="a,net_pnl[전체]\n0.3,100.5\n0.4,\n")

    body = client.get("/api/reports/week03_stub/민감도").json()

    assert body["meta"]["title"] == "민감도 보고서"
    assert body["body"] == "# 제목\n\n본문\n"
    assert body["table"] == {"columns": ["a", "net_pnl[전체]"], "rows": [[0.3, 100.5], [0.4, None]]}


def test_비교표가_없으면_table은_null이다(make_client):
    client, root = make_client()
    write(root, "week03_stub", "민감도")

    assert client.get("/api/reports/week03_stub/민감도").json()["table"] is None


def test_없는_보고서는_404다(make_client):
    client, _ = make_client()

    assert client.get("/api/reports/week03_stub/없음").status_code == 404


@pytest.mark.parametrize("strategy_id,name", [("..", "x"), ("week03_stub", "..%2F..%2Fsecret"), ("week03_stub", ".숨김"), ("../x", "y")])
def test_경로를_벗어나는_이름은_거절한다(make_client, strategy_id, name):
    client, root = make_client()
    write(root, "week03_stub", "민감도")
    (root.parent / "secret").mkdir(exist_ok=True)

    assert client.get(f"/api/reports/{strategy_id}/{name}").status_code in (404, 422)


def test_머리말이_깨진_보고서_상세는_422다(make_client):
    client, root = make_client()
    folder = root / "week03_stub" / "깨짐"
    folder.mkdir(parents=True)
    (folder / "report.md").write_text("본문뿐", encoding="utf-8")

    response = client.get("/api/reports/week03_stub/깨짐")

    assert response.status_code == 422 and "머리말" in response.json()["detail"]


def test_필수_필드가_빠지면_머리말_오류다():
    with pytest.raises(InvalidReport, match="title"):
        split_front('---\n{"strategy_id": "s"}\n---\n본문')
