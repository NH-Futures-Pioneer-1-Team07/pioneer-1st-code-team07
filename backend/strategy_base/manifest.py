import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

STRATEGY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SERIES_NAME_PATTERN = STRATEGY_ID_PATTERN


class Instrument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    market: Literal["domestic", "overseas"]
    code: str | None = None
    exchange: str | None = None
    multiplier: int | None = Field(default=None, gt=0)
    margin: float | None = Field(default=None, gt=0)


class BarSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unit: Literal["minute", "day"]
    size: int = Field(gt=0)


class ParameterSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: Any
    description: str = Field(min_length=1)
    # 화면에서 시작 전에 바꿀 수 있는 값이면 `editable`을 켠다. `percent`는 0.2를 20%로 보여 준다.
    editable: bool = False
    label: str | None = None
    unit: Literal["percent"] | None = None
    min: float | None = None
    max: float | None = None

    def problem(self, name: str, value: Any) -> str | None:
        """값이 허용 범위를 벗어나면 사유를 돌려준다. `min`·`max`가 있으면 숫자여야 한다."""
        if self.min is None and self.max is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int | float):
            return f"파라미터 {name}은(는) 숫자여야 합니다"
        shown = (lambda number: f"{number * 100:g}%") if self.unit == "percent" else (lambda number: f"{number:g}")
        if self.min is not None and value < self.min:
            return f"파라미터 {name}은(는) {shown(self.min)} 이상이어야 합니다"
        if self.max is not None and value > self.max:
            return f"파라미터 {name}은(는) {shown(self.max)} 이하여야 합니다"
        return None


class BacktestSpec(BaseModel):
    """별도 가격 봉 재현을 사용하는 전략의 선택적 실행 설정."""

    model_config = ConfigDict(extra="forbid")

    price_minutes: Literal[1] = 1
    tick_size: float = Field(gt=0)


class Manifest(BaseModel):
    """전략 폴더의 `manifest.json` 형식.

    - `bar`: 판단 기준 봉. 이 봉이 마감될 때마다 `on_bar`가 호출된다.
    - `series`: 판단에 함께 쓰는 추가 봉 계열(현재 일봉만). `Context.series[이름]`으로 받는다.
    - `history_bars`: 장이 열린 첫 봉에서도 판단할 수 있도록 전날까지의 `bar` 봉을 이만큼 앞에 이어 준다.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    instruments: list[Instrument] = Field(min_length=1)
    bar: BarSpec
    series: dict[str, BarSpec] = Field(default_factory=dict)
    history_bars: int = Field(default=0, ge=0)
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    backtest: BacktestSpec | None = None

    @field_validator("series")
    @classmethod
    def _series_are_daily(cls, series: dict[str, BarSpec]) -> dict[str, BarSpec]:
        for name, spec in series.items():
            if not SERIES_NAME_PATTERN.match(name):
                raise ValueError(f"계열 이름은 소문자 영문으로 시작하고 소문자·숫자·밑줄만 쓸 수 있습니다: {name}")
            if spec.unit != "day" or spec.size != 1:
                raise ValueError(f"추가 봉 계열은 일봉(unit=day, size=1)만 지원합니다: {name}")
        return series

    def override_problem(self, overrides: dict[str, Any] | None) -> str | None:
        """실행 요청의 파라미터에 문제가 있으면 사유를 돌려준다."""
        unknown = sorted(set(overrides or {}) - set(self.parameters))
        if unknown:
            return f"전략에 없는 파라미터입니다: {', '.join(unknown)}"
        for name, value in (overrides or {}).items():
            problem = self.parameters[name].problem(name, value)
            if problem:
                return problem
        return None

    def default_params(self) -> dict[str, Any]:
        return {key: spec.default for key, spec in self.parameters.items()}
