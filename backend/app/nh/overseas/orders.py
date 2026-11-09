"""해외 모의계좌 주문과 취소. 실전 환경에서는 요청을 보내지 않는다.

주문은 시간 초과 같은 이유로 처리 여부를 알 수 없어도 다시 보내지 않는다.
다시 보내기 전에 주문 내역(`fetch_orders`)으로 확인해야 한다.
"""

from app.nh.client import NHClient
from app.nh.domestic.orders import _order_no, _require_mock, _side_code
from app.nh.rate_limit import Limit
from app.nh.values import price_text
from strategy_base.models import OrderType, Side

ORDER_PATH = "/trade/v1/overseas/order"

NEW_ORDER = "1"
CANCEL_ORDER = "3"
ORDER_TYPE_CODES = {OrderType.MARKET: "1", OrderType.LIMIT: "2"}


def place_order(
    client: NHClient,
    code: str,
    side: Side,
    quantity: int,
    *,
    order_type: OrderType = OrderType.MARKET,
    price: float | int | None = None,
) -> str:
    """신규 주문을 내고 주문번호를 돌려준다."""
    _require_mock(client, "주문")
    if quantity <= 0:
        raise ValueError("주문 수량은 1 이상이어야 합니다")
    if order_type == OrderType.LIMIT and (price is None or price <= 0):
        raise ValueError("지정가 주문에는 가격이 필요합니다")
    payload = {
        "qt_div_cd": NEW_ORDER,
        "sym": code,
        "trd_div_cd": _side_code(side),
        "glb_ord_tp_cd": ORDER_TYPE_CODES[order_type],
        "ord_qty": str(quantity),
        "ord_pric": price_text(price) if order_type == OrderType.LIMIT and price else "0",
        "org_ord_no": "0",
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
        "qt_div_cd": CANCEL_ORDER,
        "sym": code,
        "trd_div_cd": _side_code(side),
        "glb_ord_tp_cd": ORDER_TYPE_CODES[OrderType.MARKET],
        "ord_qty": str(quantity),
        "ord_pric": "0",
        "org_ord_no": original_order_no,
    }
    return _order_no(client.call(ORDER_PATH, payload, Limit.ORDER), ORDER_PATH)
