from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.reports.store import InvalidReport, ReportNotFound, ReportStore

router = APIRouter(prefix="/api/reports")


def _store(request: Request) -> ReportStore:
    return request.app.state.reports


@router.get("")
def list_reports(request: Request) -> list[dict[str, Any]]:
    """검증 보고서 목록. 갱신일이 최근인 순서. 머리말이 깨진 보고서는 `error` 사유와 함께 담긴다."""
    return _store(request).list_reports()


@router.get("/{strategy_id}/{name}")
def get_report(strategy_id: str, name: str, request: Request) -> dict[str, Any]:
    """보고서 하나. `meta`(머리말), `body`(마크다운 본문), `table`(비교표 `{columns, rows}`, 없으면 `null`)."""
    try:
        return _store(request).get(strategy_id, name)
    except ReportNotFound as error:
        raise HTTPException(404, str(error)) from error
    except InvalidReport as error:
        raise HTTPException(422, f"보고서를 읽을 수 없습니다: {error}") from error
