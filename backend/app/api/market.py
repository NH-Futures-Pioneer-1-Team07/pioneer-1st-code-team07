import re
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.nh.domestic.market import INTERVALS, MarketService
from app.nh.errors import NHConfigError, NHError

router = APIRouter(prefix="/api/market")

CODE_PATTERNS = {
    "domestic": re.compile(r"^[A-Za-z0-9]{6,16}$"),
    "overseas": re.compile(r"^[A-Za-z0-9]{2,20}$"),
}
EXCHANGE_PATTERN = re.compile(r"^[A-Za-z0-9]{2,8}$")
KEY_NAMES = {"domestic": "NH_APP_KEY, NH_APP_SECRET", "overseas": "NH_OVERSEAS_APP_KEY, NH_OVERSEAS_APP_SECRET"}

MarketParam = Annotated[Literal["domestic", "overseas"], Query(description="종목 시장")]
ExchangeParam = Annotated[str | None, Query(description="해외 종목의 거래소 코드. 예: FCME")]


def _service(request: Request, market: str) -> MarketService:
    service: MarketService = request.app.state.market
    if not service.has_credentials(market):
        raise HTTPException(status_code=503, detail=f"{KEY_NAMES[market]} 환경변수를 설정하세요")
    return service


def _code(code: str, market: str, exchange: str | None) -> str:
    if not CODE_PATTERNS[market].match(code):
        raise HTTPException(status_code=422, detail="종목코드 형식이 올바르지 않습니다")
    if market == "overseas" and not (exchange and EXCHANGE_PATTERN.match(exchange)):
        raise HTTPException(status_code=422, detail="해외 종목에는 거래소 코드(exchange)가 필요합니다")
    return code


def _fetch(call: Any) -> Any:
    try:
        return call()
    except NHConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except NHError as error:
        raise HTTPException(status_code=502, detail=f"NH 시세를 조회하지 못했습니다: {type(error).__name__}") from error


@router.get("/{code}/quote")
def quote(code: str, request: Request, market: MarketParam = "domestic", exchange: ExchangeParam = None) -> dict[str, Any]:
    """현재가, 전일대비, 등락률, 거래량, 월물, 만기 등. 해외 종목은 월물·만기·가격 제한이 `null`이다."""
    code = _code(code, market, exchange)
    service = _service(request, market)
    return _fetch(lambda: service.quote(code, market, exchange))


@router.get("/{code}/candles")
def candles(
    code: str,
    request: Request,
    interval: str = "5",
    count: Annotated[int, Query(ge=1, le=1000)] = 200,
    market: MarketParam = "domestic",
    exchange: ExchangeParam = None,
) -> list[dict[str, Any]]:
    """분봉(`1`, `3`, `5`, `10`, `15`, `30`, `60`) 또는 일봉(`day`)을 오래된 순서로 돌려준다. 국내 종목은 주간 분봉이다."""
    if interval not in INTERVALS:
        raise HTTPException(status_code=422, detail=f"interval은 {', '.join(INTERVALS)} 중 하나여야 합니다")
    code = _code(code, market, exchange)
    service = _service(request, market)
    return _fetch(lambda: service.candles(code, interval, count, market, exchange))


@router.get("/{code}/orderbook")
def orderbook(code: str, request: Request, market: MarketParam = "domestic", exchange: ExchangeParam = None) -> dict[str, Any]:
    """호가. 국내 종목은 10단계, 해외 종목은 5단계다."""
    code = _code(code, market, exchange)
    service = _service(request, market)
    return _fetch(lambda: service.orderbook(code, market, exchange))
