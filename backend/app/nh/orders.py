"""모의계좌 주문과 취소. 실전 환경에서는 요청을 보내지 않는다.

주문은 시간 초과 같은 이유로 처리 여부를 알 수 없어도 다시 보내지 않는다.
다시 보내기 전에 주문 내역(`fetch_orders`)으로 확인해야 한다.
"""

from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.values import price_text, text
from strategy_base.models import OrderType, Side

ORDER_PATH = "/trade/v1/domestic/order"
CANCEL_PATH = "/trade/v1/domestic/cancel"

ORDER_TYPE_CODES = {OrderType.LIMIT: "1", OrderType.MARKET: "2"}
EXEC_FAS = "1"


class OrderBlocked(NHError):
    """모의 환경이 아니어서 주문하지 않았다."""


def _side_code(side: Side) -> str:
    return "1" if side == Side.BUY else "2"


def _require_mock(client: NHClient, what: str) -> None:
    if client.environment != "mock":
        raise OrderBlocked(f"{what}은(는) 모의 환경(TRADING_ENV=mock)에서만 낼 수 있습니다")


def place_order(
    client: NHClient,
    code: str,
    side: Side,
    quantity: int,
    *,
    order_type: OrderType = OrderType.MARKET,
    price: float | int | None = None,
) -> str:
    """신규 주문을 내고 주문번호를 돌려준다. 체결조건은 FAS다."""
    _require_mock(client, "주문")
    if quantity <= 0:
        raise ValueError("주문 수량은 1 이상이어야 합니다")
    if order_type == OrderType.LIMIT and (price is None or price <= 0):
        raise ValueError("지정가 주문에는 가격이 필요합니다")
    payload = {
        "sym": code,
        "trd_div": _side_code(side),
        "ord_tp_cd": ORDER_TYPE_CODES[order_type],
        "ord_qty": str(quantity),
        "ord_pric": price_text(price) if order_type == OrderType.LIMIT and price else "0",
        "exec_cnd_cd": EXEC_FAS,
    }
    return _order_no(client.call(ORDER_PATH, payload, Limit.ORDER), ORDER_PATH)


def cancel_order(client: NHClient, code: str, side: Side, quantity: int, original_order_no: str) -> str:
    """원주문을 취소하고 취소 주문번호를 돌려준다. `side`는 원주문의 매매구분이다."""
    _require_mock(client, "취소")
    if quantity <= 0:
        raise ValueError("취소 수량은 1 이상이어야 합니다")
    if not original_order_no.strip():
        raise ValueError("원주문번호가 필요합니다")
    payload = {
        "sym": code,
        "trd_div": _side_code(side),
        "ord_qty": str(quantity),
        "org_ord_no": original_order_no,
    }
    return _order_no(client.call(CANCEL_PATH, payload, Limit.ORDER), CANCEL_PATH)


def _order_no(body: dict, path: str) -> str:
    number = text(body.get("ord_no"))
    if not number:
        raise NHError(f"{path} 응답에 주문번호가 없습니다")
    return number
