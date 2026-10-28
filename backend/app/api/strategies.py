from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from strategy_base.manifest import BarSpec, Instrument, ParameterSpec

router = APIRouter(prefix="/api/strategies")


class StrategySummary(BaseModel):
    id: str
    name: str
    description: str


class StrategyDetail(StrategySummary):
    instruments: list[Instrument]
    bar: BarSpec
    parameters: dict[str, ParameterSpec]


@router.get("")
def list_strategies(request: Request) -> list[StrategySummary]:
    registry = request.app.state.registry
    return [
        StrategySummary(id=item.id, name=item.manifest.name, description=item.manifest.description)
        for item in registry.all()
    ]


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str, request: Request) -> StrategyDetail:
    item: Any = request.app.state.registry.get(strategy_id)
    if item is None:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    manifest = item.manifest
    return StrategyDetail(
        id=item.id,
        name=manifest.name,
        description=manifest.description,
        instruments=manifest.instruments,
        bar=manifest.bar,
        parameters=manifest.parameters,
    )
