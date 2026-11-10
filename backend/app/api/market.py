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
LegsParam = Annotated[
    str | None, Query(description="스프레드 종목의 구성. `종목코드:비율,종목코드:비율` 예: ZFZ26:3,ZNZ26:-2")
]


def _service(request: Request, market: str) -> MarketService:
    service: MarketService = request.app.state.market
    if not service.has_credentials(market):
        raise HTTPException(status_code=503, detail=f"{KEY_NAMES[market]} 환경변수를 설정하세요")
    return service


def _code(code: str, market: str, exchange: str | None, spread: bool = False) -> str:
    """종목코드를 확인한다. 스프레드 종목코드는 두 종목코드를 `-`로 이은 형식(예 ZFZ26-ZNZ26)이라 `-`를 허용한다."""
    if not CODE_PATTERNS[market].match(code.replace("-", "") if spread else code):
        raise HTTPException(status_code=422, detail="종목코드 형식이 올바르지 않습니다")
    if market == "overseas" and not (exchange and EXCHANGE_PATTERN.match(exchange)):
        raise HTTPException(status_code=422, detail="해외 종목에는 거래소 코드(exchange)가 필요합니다")
    return code


def _legs(legs: str | None, market: str, exchange: str | None) -> list[tuple[str, int]] | None:
    """스프레드 구성 문자열을 (종목코드, 비율) 두 개로 바꾼다. 없으면 `None`."""
    if not legs:
        return None
    if market != "overseas" or not (exchange and EXCHANGE_PATTERN.match(exchange)):
        raise HTTPException(status_code=422, detail="스프레드는 거래소 코드가 있는 해외 종목에만 쓸 수 있습니다")
    parsed = []
    for part in legs.split(","):
        code, _, ratio = part.partition(":")
        if not CODE_PATTERNS["overseas"].match(code) or not re.fullmatch(r"-?[1-9][0-9]{0,2}", ratio):
            raise HTTPException(status_code=422, detail="스프레드 구성 형식이 올바르지 않습니다")
        parsed.append((code, int(ratio)))
    if len(parsed) != 2 or parsed[0][0] == parsed[1][0]:
        raise HTTPException(status_code=422, detail="스프레드 구성은 서로 다른 종목 2개여야 합니다")
    return parsed


def _fetch(call: Any) -> Any:
    try:
        return call()
    except NHConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except NHError as error:
        raise HTTPException(status_code=502, detail=f"NH 시세를 조회하지 못했습니다: {type(error).__name__}") from error


@router.get("/{code}/quote")
def quote(
    code: str, request: Request, market: MarketParam = "domestic", exchange: ExchangeParam = None, legs: LegsParam = None
) -> dict[str, Any]:
    """현재가, 전일대비, 등락률, 거래량, 월물, 만기 등. 해외 종목은 월물·만기·가격 제한이 `null`이다."""
    pair = _legs(legs, market, exchange)
    code = _code(code, market, exchange, spread=bool(pair))
    service = _service(request, market)
    if pair:
        return _fetch(lambda: service.spread_quote(code, pair, exchange))
    return _fetch(lambda: service.quote(code, market, exchange))


@router.get("/{code}/candles")
def candles(
    code: str,
    request: Request,
    interval: str = "5",
    count: Annotated[int, Query(ge=1, le=1000)] = 200,
    market: MarketParam = "domestic",
    exchange: ExchangeParam = None,
    legs: LegsParam = None,
) -> list[dict[str, Any]]:
    """분봉(`1`, `3`, `5`, `10`, `15`, `30`, `60`) 또는 일봉(`day`)을 오래된 순서로 돌려준다. 국내 종목은 주간 분봉이다."""
    if interval not in INTERVALS:
        raise HTTPException(status_code=422, detail=f"interval은 {', '.join(INTERVALS)} 중 하나여야 합니다")
    pair = _legs(legs, market, exchange)
    code = _code(code, market, exchange, spread=bool(pair))
    service = _service(request, market)
    if pair:
        return _fetch(lambda: service.spread_candles(pair, interval, count, exchange))
    return _fetch(lambda: service.candles(code, interval, count, market, exchange))


@router.get("/{code}/orderbook")
def orderbook(
    code: str, request: Request, market: MarketParam = "domestic", exchange: ExchangeParam = None, legs: LegsParam = None
) -> dict[str, Any]:
    """호가. 국내 종목은 10단계, 해외 종목은 5단계다."""
    pair = _legs(legs, market, exchange)
    code = _code(code, market, exchange, spread=bool(pair))
    service = _service(request, market)
    if pair:
        return service.spread_orderbook(code)
    return _fetch(lambda: service.orderbook(code, market, exchange))
