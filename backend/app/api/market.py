import re
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.nh.domestic.market import INTERVALS, MarketService
from app.nh.errors import NHConfigError, NHError

router = APIRouter(prefix="/api/market")

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{6,16}$")


def _service(request: Request) -> MarketService:
    service: MarketService = request.app.state.market
    if not service.has_credentials():
        raise HTTPException(status_code=503, detail="NH_APP_KEY, NH_APP_SECRET 환경변수를 설정하세요")
    return service


def _code(code: str) -> str:
    if not CODE_PATTERN.match(code):
        raise HTTPException(status_code=422, detail="종목코드 형식이 올바르지 않습니다")
    return code


def _fetch(call: Any) -> Any:
    try:
        return call()
    except NHConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except NHError as error:
        raise HTTPException(status_code=502, detail=f"NH 시세를 조회하지 못했습니다: {type(error).__name__}") from error


@router.get("/{code}/quote")
def quote(code: str, request: Request) -> dict[str, Any]:
    """현재가, 전일대비, 등락률, 거래량, 월물, 만기 등."""
    service, code = _service(request), _code(code)
    return _fetch(lambda: service.quote(code))


@router.get("/{code}/candles")
def candles(
    code: str,
    request: Request,
    interval: str = "5",
    count: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[dict[str, Any]]:
    """주간 분봉(`1`, `3`, `5`, `10`, `15`, `30`, `60`) 또는 일봉(`day`)을 오래된 순서로 돌려준다."""
    if interval not in INTERVALS:
        raise HTTPException(status_code=422, detail=f"interval은 {', '.join(INTERVALS)} 중 하나여야 합니다")
    service, code = _service(request), _code(code)
    return _fetch(lambda: service.candles(code, interval, count))


@router.get("/{code}/orderbook")
def orderbook(code: str, request: Request) -> dict[str, Any]:
    """10단계 호가."""
    service, code = _service(request), _code(code)
    return _fetch(lambda: service.orderbook(code))
