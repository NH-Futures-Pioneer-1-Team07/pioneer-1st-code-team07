import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

STRATEGY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class Instrument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    code: str | None = None
    multiplier: int | None = Field(default=None, gt=0)


class BarSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unit: Literal["minute", "day"]
    size: int = Field(gt=0)


class ParameterSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: Any
    description: str = Field(min_length=1)


class BacktestSpec(BaseModel):
    """별도 가격 봉 재현을 사용하는 전략의 선택적 실행 설정."""

    model_config = ConfigDict(extra="forbid")

    price_minutes: Literal[1] = 1
    tick_size: float = Field(gt=0)


class Manifest(BaseModel):
    """전략 폴더의 `manifest.json` 형식."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    instruments: list[Instrument] = Field(min_length=1)
    bar: BarSpec
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    backtest: BacktestSpec | None = None

    def default_params(self) -> dict[str, Any]:
        return {key: spec.default for key, spec in self.parameters.items()}
