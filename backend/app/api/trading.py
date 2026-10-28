from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.runners.paper_service import PaperService, TradingRejected

router = APIRouter(prefix="/api/trading")


class StartRequest(BaseModel):
    strategy_id: str
    params: dict[str, Any] | None = None


def _service(request: Request) -> PaperService:
    return request.app.state.trading


@router.post("/start", status_code=202)
def start(body: StartRequest, request: Request) -> dict[str, str]:
    """모의매매를 시작하고 실행 식별자를 돌려준다."""
    try:
        return _service(request).start(body.strategy_id, body.params)
    except TradingRejected as rejected:
        raise HTTPException(status_code=rejected.status_code, detail=rejected.message) from rejected


@router.post("/stop", status_code=202)
def stop(request: Request) -> dict[str, str]:
    """정상 종료를 시작한다: 신규 판단 중단, 미체결 취소, 보유 청산, 확인."""
    try:
        return _service(request).stop()
    except TradingRejected as rejected:
        raise HTTPException(status_code=rejected.status_code, detail=rejected.message) from rejected


@router.get("/status")
def status(request: Request) -> dict[str, Any]:
    """운용 단계, 시세 상태, 신규 주문 차단 사유, 현재 운용의 손익."""
    return _service(request).status()
