import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

STRATEGY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SERIES_NAME_PATTERN = STRATEGY_ID_PATTERN


class SpreadLeg(BaseModel):
    """스프레드를 이루는 한 종목. `ratio`가 양수이면 매수 방향이고 음수이면 반대 방향이다. 절댓값이 한 세트의 계약 수다.

    `weight`는 스프레드 가격에 이 종목 가격을 더하는 가중치다. 없으면 `ratio`와 같다.
    두 종목의 거래승수가 다르면 `weight = ratio × 종목 승수 ÷ 스프레드 승수`로 적는다.
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    ratio: int
    weight: float | None = None

    @property
    def price_weight(self) -> float:
        return float(self.ratio) if self.weight is None else self.weight

    @model_validator(mode="after")
    def _weight_follows_ratio(self) -> "SpreadLeg":
        if self.weight is not None and (self.weight == 0 or (self.weight > 0) != (self.ratio > 0)):
            raise ValueError("스프레드 구성의 가격 가중치(weight)는 0이 아니고 계약 비율(ratio)과 부호가 같아야 합니다")
        return self

    @field_validator("ratio")
    @classmethod
    def _ratio_not_zero(cls, ratio: int) -> int:
        if ratio == 0:
            raise ValueError("스프레드 구성의 계약 비율은 0이 될 수 없습니다")
        return ratio


class Instrument(BaseModel):
    """전략이 매매하는 종목. `legs`가 있으면 두 종목의 가격을 비율대로 합친 스프레드 종목이다.

    스프레드 종목의 가격은 `sum(가중치 × 각 종목 가격)`이고 한 세트가 수량 1이다.
    `multiplier`·`margin`·`tick_size`는 스프레드 한 세트 기준으로 적는다. 두 종목은 같은 `market`·`exchange`에서 거래한다.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    market: Literal["domestic", "overseas"]
    code: str | None = None
    exchange: str | None = None
    multiplier: int | None = Field(default=None, gt=0)
    margin: float | None = Field(default=None, gt=0)
    tick_size: float | None = Field(default=None, gt=0)
    legs: list[SpreadLeg] | None = None

    @model_validator(mode="after")
    def _check_legs(self) -> "Instrument":
        if self.legs is None:
            return self
        if len(self.legs) != 2:
            raise ValueError("스프레드 구성은 종목 2개여야 합니다")
        if self.legs[0].code == self.legs[1].code:
            raise ValueError("스프레드 구성의 종목코드가 같습니다")
        return self


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


class ChartLine(BaseModel):
    """모의매매 차트에 그릴 판단용 선. `series`가 `bar`이면 판단 기준 봉(`bar`)의 차트에, `daily`이면 일봉 차트에 그린다.

    - `sma`: 종가의 단순이동평균. `period`개 봉을 쓴다.
    - `previous_close`: 직전 거래일 종가를 지나는 가로선(일봉 계열만).
    """

    model_config = ConfigDict(extra="forbid")

    series: Literal["bar", "daily"]
    kind: Literal["sma", "previous_close"]
    period: int | None = Field(default=None, gt=0)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self) -> "ChartLine":
        if self.kind == "sma" and self.period is None:
            raise ValueError(f"{self.label}: 이동평균 선에는 period가 필요합니다")
        if self.kind == "previous_close" and self.series != "daily":
            raise ValueError(f"{self.label}: 직전 거래일 종가선은 일봉 계열에만 그릴 수 있습니다")
        return self


class BacktestSpec(BaseModel):
    """별도 가격 봉 재현을 사용하는 전략의 선택적 실행 설정."""

    model_config = ConfigDict(extra="forbid")

    price_minutes: Literal[1] = 1
    tick_size: float = Field(gt=0)


class Manifest(BaseModel):
    """전략 폴더의 `manifest.json` 형식.

    - `bar`: 판단 기준 봉. 이 봉이 마감될 때마다 `on_bar`가 호출된다.
    - `series`: 판단에 함께 쓰는 추가 봉 계열(현재 일봉만). `Context.series[이름]`으로 받는다.
    - `chart_lines`: 모의매매 차트에 그릴 판단용 선과 마우스를 올렸을 때의 설명.
    - `history_bars`: 장이 열린 첫 봉에서도 판단할 수 있도록 전날까지의 `bar` 봉을 이만큼 앞에 이어 준다.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    instruments: list[Instrument] = Field(min_length=1)
    bar: BarSpec
    series: dict[str, BarSpec] = Field(default_factory=dict)
    history_bars: int = Field(default=0, ge=0)
    chart_lines: list[ChartLine] = Field(default_factory=list)
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
