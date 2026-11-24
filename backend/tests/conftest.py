import pytest

from app.data import vix


@pytest.fixture(autouse=True)
def no_fred(monkeypatch, tmp_path):
    """테스트가 FRED를 부르거나 개발자의 VIX 캐시를 읽고 쓰지 않게 한다. 받기는 실패로 처리한다."""

    def blocked(client=None):
        raise vix.VixError("테스트에서는 FRED를 부르지 않습니다")

    real = vix.download
    monkeypatch.setattr(vix, "download", blocked)
    monkeypatch.setattr(vix, "CACHE_FILE", tmp_path / "vix_cache.csv")
    return real
