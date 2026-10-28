from pathlib import Path
from typing import Literal

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    """필수 환경변수가 없거나 값이 잘못됐을 때 발생한다."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    trading_env: Literal["mock", "real"]
    strategies_dir: Path = BACKEND_DIR / "strategies"


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        problems = []
        for item in error.errors():
            name = ".".join(str(part) for part in item["loc"]).upper()
            reason = "없음" if item["type"] == "missing" else item["msg"]
            problems.append(f"{name}: {reason}")
        raise ConfigError("환경변수를 확인하세요 — " + ", ".join(problems)) from error
