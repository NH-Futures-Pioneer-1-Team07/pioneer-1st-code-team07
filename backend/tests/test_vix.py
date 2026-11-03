from datetime import date

import httpx
import pytest

from app.data import vix
from app.data.vix import VixError, VixHistory

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


def test_갱신하면_받은_내용으로_파일을_바꾼다(tmp_path):
    path = tmp_path / "data" / "vix.csv"
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=CSV)))

    history = vix.update(path, client)

    assert path.read_text(encoding="utf-8").startswith("observation_date")
    assert history.last_day == date(2026, 11, 2)


def test_받기에_실패하면_기존_파일을_그대로_둔다(tmp_path):
    path = tmp_path / "vix.csv"
    path.write_text(CSV, encoding="utf-8")
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))

    with pytest.raises(VixError):
        vix.update(path, client)

    assert path.read_text(encoding="utf-8") == CSV


def test_저장소의_VIX_파일을_읽을_수_있다():
    history = vix.load()

    assert history is not None and len(history) > 1000
