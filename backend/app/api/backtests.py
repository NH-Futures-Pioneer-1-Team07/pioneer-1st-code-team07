from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.runners.service import BacktestRejected, BacktestService

router = APIRouter(prefix="/api/backtests")


class BacktestRequest(BaseModel):
    strategy_id: str
    start_date: date
    end_date: date
    initial_capital: float = Field(gt=0)
    params: dict[str, Any] | None = None


def _service(request: Request) -> BacktestService:
    return request.app.state.backtests


@router.post("", status_code=202)
def start_backtest(body: BacktestRequest, request: Request) -> dict[str, str]:
    """백테스트를 시작하고 실행 식별자를 돌려준다. 진행 상황은 실행 상세의 `meta.progress`로 읽는다."""
    try:
        return _service(request).start(
            body.strategy_id, body.start_date, body.end_date, body.initial_capital, body.params
        )
    except BacktestRejected as rejected:
        raise HTTPException(status_code=rejected.status_code, detail=rejected.message) from rejected


@router.get("/assumptions")
def assumptions(request: Request) -> dict[str, Any]:
    """시작 전에 보여 줄 비용·체결 가정."""
    return _service(request).assumptions()


@router.get("/current")
def current(request: Request) -> dict[str, Any]:
    """실행 중인 백테스트. 없으면 `run`이 `null`이다."""
    return {"run": _service(request).current()}
