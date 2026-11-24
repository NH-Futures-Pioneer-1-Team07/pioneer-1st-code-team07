from datetime import date, datetime

import httpx
import pytest

from app.data import vix
from app.data.vix import VixError, VixHistory
from app.runners.inputs import ExtraInputs

CSV = "observation_date,VIXCLS\n2026-10-29,19.5\n2026-10-30,\n2026-11-02,21.15\n2026-11-03,.\n"


def test_빈_값과_점은_건너뛰고_종가를_읽는다():
    history = vix.parse(CSV)

    assert len(history) == 2
    assert history.last_day == date(2026, 11, 2)


def test_직전_거래일_종가를_돌려준다():
    history = VixHistory({date(2026, 10, 29): 19.5, date(2026, 11, 2): 21.15})

    assert history.previous_close(date(2026, 11, 2)) == 19.5  # 당일 값은 쓰지 않는다
    assert history.previous_close(date(2026, 11, 3)) == 21.15
    assert history.previous_close(date(2026, 10, 30)) == 19.5  # 휴장일 사이는 직전 값
    assert history.previous_close(date(2026, 10, 29)) is None


def test_읽을_값이_없으면_오류다():
    with pytest.raises(VixError):
        vix.parse("observation_date,VIXCLS\n2026-11-03,.\n")


def test_파일이_없으면_None이고_있으면_읽는다(tmp_path):
    path = tmp_path / "vix.csv"
    assert vix.load(path) is None

    path.write_text(CSV, encoding="utf-8")
    assert vix.load(path).previous_close(date(2026, 11, 3)) == 21.15


def test_갱신하면_받은_내용으로_파일을_바꾼다(tmp_path, monkeypatch, no_fred):
    monkeypatch.setattr(vix, "download", no_fred)
    path = tmp_path / "data" / "vix.csv"
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=CSV)))

    history = vix.update(path, client)

    assert path.read_text(encoding="utf-8").startswith("observation_date")
    assert history.last_day == date(2026, 11, 2)


def test_받기에_실패하면_기존_파일을_그대로_둔다(tmp_path, monkeypatch, no_fred):
    monkeypatch.setattr(vix, "download", no_fred)
    path = tmp_path / "vix.csv"
    path.write_text(CSV, encoding="utf-8")
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))

    with pytest.raises(VixError):
        vix.update(path, client)

    assert path.read_text(encoding="utf-8") == CSV


def test_저장소의_VIX_파일을_읽을_수_있다():
    history = vix.load()

    assert history is not None and len(history) > 1000


# ---- 실행할 때 최신 값 받기 ----

NEWER = CSV + "2026-11-04,25.0\n"


@pytest.fixture
def files(tmp_path, monkeypatch):
    """저장소 파일과 캐시의 위치. 저장소 파일에는 `CSV`가 들어 있다."""
    stored = tmp_path / "vixcls.csv"
    stored.write_text(CSV, encoding="utf-8")
    monkeypatch.setattr(vix, "VIX_FILE", stored)
    return stored, vix.CACHE_FILE


def test_최신_값을_받으면_그_값을_쓰고_캐시에만_저장한다(files, monkeypatch):
    stored, cache = files
    monkeypatch.setattr(vix, "download", lambda client=None: NEWER)

    found = vix.latest()

    assert found.error is None and found.history.last_day == date(2026, 11, 4)
    assert cache.read_text(encoding="utf-8") == NEWER
    assert stored.read_text(encoding="utf-8") == CSV
    assert [path.name for path in cache.parent.glob("*.tmp")] == []


def test_받지_못하면_캐시와_저장소_파일_중_더_최근_값을_쓴다(files):
    stored, cache = files
    assert vix.latest().history.last_day == date(2026, 11, 2)

    cache.write_text(NEWER, encoding="utf-8")
    found = vix.latest()

    assert found.history.last_day == date(2026, 11, 4)
    assert found.error and found.event()["level"] == "warning"


def test_캐시가_깨졌으면_저장소_파일을_쓴다(files):
    _, cache = files
    cache.write_text("깨짐", encoding="utf-8")

    assert vix.latest().history.last_day == date(2026, 11, 2)


def test_저장된_값도_없으면_VIX_없이_실행한다(files):
    files[0].unlink()

    found = vix.latest()

    assert found.history is None
    assert found.event(date(2026, 11, 3))["vix"] is None


def test_캐시에_쓰지_못해도_받은_값을_쓴다(files, monkeypatch):
    monkeypatch.setattr(vix, "download", lambda client=None: NEWER)
    monkeypatch.setattr(vix.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("쓰기 실패")))

    found = vix.latest()

    assert found.error is None and found.history.last_day == date(2026, 11, 4)
    assert list(files[1].parent.glob("*.tmp")) == []


def test_기록에는_그날_쓰는_종가와_날짜가_남는다(files):
    event = vix.latest().event(date(2026, 11, 3))

    assert (event["vix_day"], event["vix"], event["vix_last_day"]) == ("2026-11-02", 21.15, "2026-11-02")


def test_모의매매_입력은_첫_호출과_날짜가_바뀔_때만_VIX를_다시_받는다():
    days = []

    def loader(day):
        days.append(day)
        return VixHistory({date(2026, 11, len(days)): 10.0 + len(days)})

    extras = ExtraInputs(vix_loader=loader)
    for day in (3, 3, 4, 3, 4):  # 늦게 도착한 전날 봉은 다시 받지 않는다
        extras.prepare(date(2026, 11, day))

    assert days == [date(2026, 11, 3), date(2026, 11, 4)]
    assert extras.fields(datetime(2026, 11, 4, 9))["vix"] == 12.0
