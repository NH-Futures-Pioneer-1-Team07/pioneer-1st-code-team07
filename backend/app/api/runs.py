from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.records.store import RunNotFound, RunStore

router = APIRouter(prefix="/api/runs")

Mode = Literal["backtest", "paper"]
Kind = Literal["decision", "order", "fill", "trade", "event"]


def _store(request: Request) -> RunStore:
    return request.app.state.run_store


@router.get("")
def list_runs(request: Request, mode: Mode | None = None, strategy_id: str | None = None) -> list[dict[str, Any]]:
    return _store(request).list_runs(mode=mode, strategy_id=strategy_id)


@router.get("/{strategy_id}/{mode}/{run_id}")
def get_run(strategy_id: str, mode: str, run_id: str, request: Request) -> dict[str, Any]:
    try:
        return _store(request).get_run(strategy_id, mode, run_id)
    except RunNotFound as error:
        raise HTTPException(status_code=404, detail="실행 기록을 찾을 수 없습니다") from error


@router.get("/{strategy_id}/{mode}/{run_id}/journal")
def get_journal(
    strategy_id: str,
    mode: str,
    run_id: str,
    request: Request,
    kind: Kind | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> dict[str, Any]:
    """기록을 시간순으로 돌려준다. `end`는 포함하지 않는다."""
    try:
        page = _store(request).read_journal(
            strategy_id, mode, run_id, kind=kind, start=start, end=end, offset=offset, limit=limit
        )
    except RunNotFound as error:
        raise HTTPException(status_code=404, detail="실행 기록을 찾을 수 없습니다") from error
    return {"items": page.items, "total": page.total, "offset": page.offset, "limit": page.limit}
