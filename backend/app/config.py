from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    """필수 환경변수가 없거나 값이 잘못됐을 때 발생한다."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    trading_env: Literal["mock", "real"]
    strategies_dir: Path = BACKEND_DIR / "strategies"
    runs_dir: Path = BACKEND_DIR / "runs"
    nh_app_key: SecretStr | None = None
    nh_app_secret: SecretStr | None = None
    backtest_fee_rate: float = Field(default=0.000085, ge=0)
    backtest_slippage_ticks: int = Field(default=1, ge=0)


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
