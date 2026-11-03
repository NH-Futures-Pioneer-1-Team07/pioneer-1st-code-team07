"""해외 모의계좌 조회: 예탁금, 보유 포지션, 주문 내역, 주문가능수량, 상품 정보.

응답에 실리는 계좌번호는 읽지 않는다. 요청에도 계좌번호를 넣지 않는다.
결과 형식은 국내(`app.nh.domestic.account`)와 같다.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.nh.auth import KST
from app.nh.client import NHClient
from app.nh.domestic.account import (
    STATUS_CODES,
    ORDER_KINDS,
    Deposit,
    OrderableQuantity,
    OrderRecord,
    OrderStatus,
    Position,
    _pages,
)
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.values import count, number, price_text, text
from strategy_base.models import Side

DEPOSIT_PATH = "/trade/v1/overseas/deposit"
POSITIONS_PATH = "/trade/v1/overseas/open-interest"
ORDER_HISTORY_PATH = "/trade/v1/overseas/order-history"
ORDERABLE_PATH = "/trade/v1/overseas/orderable-quantity"
PRODUCT_PATH = "/trade/v1/overseas/product-detail"

INDIVIDUAL = "1"  # 환산구분: 개별
ALL_ORDERS, OPEN_ORDERS = "0", "3"
MARKET_ORDER, LIMIT_ORDER = "1", "2"


@dataclass(frozen=True)
class Product:
    code: str
    name: str
    exchange: str
    currency: str
    tick_size: float | None
    tick_value: float | None


def _side(value: Any) -> Side | None:
    return {"1": Side.BUY, "2": Side.SELL}.get(text(value))


def fetch_deposit(client: NHClient, currency: str = "USD", business_day: date | None = None) -> Deposit:
    day = business_day or datetime.now(KST).date()
    payload = {"biz_dt": day.strftime("%Y%m%d"), "cur_cd": currency, "cvs_div": INDIVIDUAL}
    body = client.call(DEPOSIT_PATH, payload, Limit.ACCOUNT)
    return Deposit(
        cash=number(body.get("dps_csh_amt")),
        total_assets=number(body.get("dps_aset_amt")),
        order_available_total=number(body.get("ord_psb_amt")),
        order_available_cash=number(body.get("ord_psb_amt")),
        initial_margin=number(body.get("init_mrgn")),
        maintenance_margin=number(body.get("mtn_mrgn")),
        futures_realized_pnl=number(body.get("cls_pl_amt")),
        total_pnl=number(body.get("pl_amt")),
        fee=number(body.get("fee")),
    )


def fetch_positions(client: NHClient) -> list[Position]:
    rows = _pages(client, POSITIONS_PATH, {})
    return [
        Position(
            code=text(row.get("occurs1_sym")),
            name="",
            side=_side(row.get("occurs1_trd_tp")),
            quantity=count(row.get("occurs1_opint_qty")),
            closable_quantity=count(row.get("occurs1_cls_psb_qty")),
            avg_price=number(row.get("occurs1_avg_pric")),
            last_price=number(row.get("occurs1_last_pric")),
            pnl=number(row.get("occurs1_pl_amt")),
            pnl_rate=None,
        )
        for row in rows
    ]


def fetch_orders(client: NHClient, *, open_only: bool = False) -> list[OrderRecord]:
    """주문 내역. `open_only`이면 미체결 주문만 조회한다."""
    payload = {"inq_div": OPEN_ORDERS if open_only else ALL_ORDERS, "trd_div_cd": "0"}
    return [_order(row) for row in _pages(client, ORDER_HISTORY_PATH, payload)]


def fetch_orderable_quantity(client: NHClient, code: str, side: Side, price: float | int) -> OrderableQuantity:
    """시장가 기준이면 `price`에 0을 넣는다."""
    order_type = MARKET_ORDER if not price else LIMIT_ORDER
    payload = {"sym": code, "glb_ord_tp_cd": order_type, "ord_pric": price_text(price)}
    body = client.call(ORDERABLE_PATH, payload, Limit.ACCOUNT)
    prefix = "buy" if side == Side.BUY else "sel"
    return OrderableQuantity(
        order_quantity=count(body.get(f"new_{prefix}_ord_psb_qty")),
        closable_quantity=count(body.get(f"{prefix}_cls_psb_qty")),
        total_quantity=count(body.get(f"{prefix}_ord_psb_qty")),
        order_amount=number(body.get("ord_psb_amt")),
    )


def fetch_product(client: NHClient, product_code: str, exchange: str = "") -> Product | None:
    """품목코드(예: `ZN`)의 상품 정보. 없으면 `None`이다."""
    payload = {"fut_opt_div_cd": "F", "exch_cd": exchange, "prd_cd": "2", "prd_nm": product_code}
    body = client.call(PRODUCT_PATH, payload, Limit.ACCOUNT)
    rows = body.get("Occurs1") or []
    if not isinstance(rows, list):
        raise NHError(f"{PRODUCT_PATH} 응답의 Occurs1 형식이 올바르지 않습니다")
    for row in rows:
        if text(row.get("occurs1_prd_cd")) == product_code:
            return Product(
                code=product_code,
                name=text(row.get("occurs1_ko_prd_nm")),
                exchange=text(row.get("occurs1_exch_cd")),
                currency=text(row.get("occurs1_cur_cd")),
                tick_size=number(row.get("occurs1_tick_unt")),
                tick_value=number(row.get("occurs1_tick_val")),
            )
    return None


def _order(row: dict[str, Any]) -> OrderRecord:
    return OrderRecord(
        order_no=text(row.get("occurs1_ord_no")),
        original_order_no=text(row.get("occurs1_org_ord_no")),
        code=text(row.get("occurs1_sym")),
        side=_side(row.get("occurs1_trd_tp")),
        status=STATUS_CODES.get(text(row.get("occurs1_ord_sts")), OrderStatus.UNKNOWN),
        kind=ORDER_KINDS.get(text(row.get("occurs1_qt_tp")), "unknown"),
        quantity=count(row.get("occurs1_ord_qty")),
        price=number(row.get("occurs1_ord_pric")),
        filled_quantity=count(row.get("occurs1_exec_qty")),
        filled_price=number(row.get("occurs1_exec_pric")),
        remaining_quantity=count(row.get("occurs1_ord_rem_qty")),
        received_time=text(row.get("occurs1_ord_rcv_tm"))[-6:],  # YYYYMMDDHHMMSS → HHMMSS
        reject_reason=text(row.get("occurs1_rejt_rsn")),
    )
