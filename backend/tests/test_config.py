import pytest

from app.config import ConfigError, Settings, load_settings


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    monkeypatch.delenv("TRADING_ENV", raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)


def test_필수_환경변수가_없으면_어떤_변수인지_알려_준다():
    with pytest.raises(ConfigError, match="TRADING_ENV"):
        load_settings()


def test_허용하지_않는_값이면_변수_이름과_함께_오류가_난다(monkeypatch):
    monkeypatch.setenv("TRADING_ENV", "live")

    with pytest.raises(ConfigError, match="TRADING_ENV"):
        load_settings()


def test_환경변수가_있으면_읽는다(monkeypatch):
    monkeypatch.setenv("TRADING_ENV", "real")

    assert load_settings().trading_env == "real"
