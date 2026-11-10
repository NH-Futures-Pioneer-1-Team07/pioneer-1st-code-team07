"""조합 탐색 요청 파일(JSON)을 읽어 실행할 조합 목록으로 펼친다.

    {
      "strategy_id": "week03_zn_treasury_futures",
      "initial_capital": 100000,
      "slippage_ticks": 1,                         (생략하면 환경 설정 값)
      "periods": [{"start": "2026-08-11", "end": "2026-09-30"}],
      "params": [{"short_bars": 3}, {"short_bars": 8}],   (파라미터를 덮어쓰는 조합 목록)
      "grid": {"long_bars": [15, 20, 30]}          (값 목록의 모든 곱을 조합으로 추가)
    }

`params`와 `grid`가 모두 없으면 기본 파라미터 하나만 실행한다. 조합은 `params` × `periods`로 만든다.
"""

import itertools
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


class SpecError(Exception):
    pass


@dataclass(frozen=True)
class Period:
    start: date
    end: date


@dataclass(frozen=True)
class SweepSpec:
    strategy_id: str
    initial_capital: float
    slippage_ticks: int | None
    periods: tuple[Period, ...]
    overrides: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class Combo:
    overrides: dict[str, Any]
    period: Period


def _date(value: Any, name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise SpecError(f"{name}은(는) YYYY-MM-DD 형식이어야 합니다: {value!r}") from error


def parse_spec(raw: Any) -> SweepSpec:
    if not isinstance(raw, dict):
        raise SpecError("요청 파일의 최상위는 객체여야 합니다")
    strategy_id = raw.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise SpecError("strategy_id가 필요합니다")
    capital = raw.get("initial_capital")
    if isinstance(capital, bool) or not isinstance(capital, int | float) or capital <= 0:
        raise SpecError("initial_capital은 0보다 큰 숫자여야 합니다")
    slippage = raw.get("slippage_ticks")
    if slippage is not None and (isinstance(slippage, bool) or not isinstance(slippage, int) or slippage < 0):
        raise SpecError("slippage_ticks는 0 이상의 정수여야 합니다")

    periods = []
    for item in raw.get("periods") or []:
        if not isinstance(item, dict):
            raise SpecError("periods의 항목은 {start, end} 객체여야 합니다")
        period = Period(_date(item.get("start"), "periods.start"), _date(item.get("end"), "periods.end"))
        if period.start > period.end:
            raise SpecError(f"시작일이 종료일보다 늦습니다: {period.start} ~ {period.end}")
        if period not in periods:
            periods.append(period)
    if not periods:
        raise SpecError("periods에 기간이 하나 이상 필요합니다")

    overrides: list[dict[str, Any]] = []
    for item in raw.get("params") or []:
        if not isinstance(item, dict):
            raise SpecError("params의 항목은 파라미터 객체여야 합니다")
        overrides.append(dict(item))
    grid = raw.get("grid")
    if grid:
        if not isinstance(grid, dict) or not all(isinstance(v, list) and v for v in grid.values()):
            raise SpecError("grid는 파라미터 이름 → 값 목록(비어 있지 않음) 객체여야 합니다")
        names = list(grid)
        overrides.extend(dict(zip(names, values)) for values in itertools.product(*(grid[n] for n in names)))
    if not overrides:
        overrides = [{}]

    unique: list[dict[str, Any]] = []
    seen = set()
    for item in overrides:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return SweepSpec(strategy_id, float(capital), slippage, tuple(periods), tuple(unique))


def load_spec(path: Path) -> SweepSpec:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SpecError(f"요청 파일이 없습니다: {path}") from error
    except json.JSONDecodeError as error:
        raise SpecError(f"요청 파일이 JSON이 아닙니다: {error}") from error
    return parse_spec(raw)


def expand(spec: SweepSpec) -> list[Combo]:
    return [Combo(overrides, period) for overrides in spec.overrides for period in spec.periods]
