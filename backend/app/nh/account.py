"""모의계좌 조회: 예탁금, 보유 포지션, 주문 내역, 주문가능수량.

응답에 실리는 계좌번호·계좌명은 읽지 않는다. 요청에도 계좌번호를 넣지 않는다.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from app.nh.auth import KST
from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.values import count, number, price_text, text
from strategy_base.models import Side

DEPOSIT_PATH = "/trade/v1/domestic/deposit"
POSITIONS_PATH = "/trade/v1/domestic/open-interest"
ORDER_HISTORY_PATH = "/trade/v1/domestic/order-history"
ORDERABLE_PATH = "/trade/v1/domestic/orderable-quantity"

MAX_PAGES = 50
DAY_NORMAL = "1"  # 처리구분: 주간 일반


@dataclass(frozen=True)
class Deposit:
    cash: float | None
    total_assets: float | None
    order_available_total: float | None
    order_available_cash: float | None
    initial_margin: float | None
    maintenance_margin: float | None
    futures_realized_pnl: float | None
    total_pnl: float | None
    fee: float | None = None


@dataclass(frozen=True)
class Position:
    code: str
    name: str
    side: Side | None
    quantity: int | None
    closable_quantity: int | None
    avg_price: float | None
    last_price: float | None
    pnl: float | None
    pnl_rate: float | None


class OrderStatus(StrEnum):
    ACCEPTED = "accepted"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    FILLED = "filled"
    AUTO_CANCELLED = "auto_cancelled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


STATUS_CODES = {
    "1": OrderStatus.ACCEPTED,
    "3": OrderStatus.CONFIRMED,
    "4": OrderStatus.PARTIAL,
    "6": OrderStatus.FILLED,
    "8": OrderStatus.AUTO_CANCELLED,
    "9": OrderStatus.REJECTED,
}
OPEN_STATUSES = {OrderStatus.ACCEPTED, OrderStatus.CONFIRMED, OrderStatus.PARTIAL}

ORDER_KINDS = {"1": "new", "2": "modify", "3": "cancel"}


@dataclass(frozen=True)
class OrderRecord:
    order_no: str
    original_order_no: str
    code: str
    side: Side | None
    status: OrderStatus
    kind: str
    quantity: int | None
    price: float | None
    filled_quantity: int | None
    filled_price: float | None
    remaining_quantity: int | None
    received_time: str
    reject_reason: str

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES


@dataclass(frozen=True)
class OrderableQuantity:
    order_quantity: int | None
    closable_quantity: int | None
    total_quantity: int | None
    order_amount: float | None


def _side(value: Any) -> Side | None:
    return {"1": Side.BUY, "2": Side.SELL}.get(text(value))


def fetch_deposit(client: NHClient, business_day: date | None = None) -> Deposit:
    day = business_day or datetime.now(KST).date()
    body = client.call(DEPOSIT_PATH, {"biz_dt": day.strftime("%Y%m%d")}, Limit.ACCOUNT)
    return Deposit(
        cash=number(body.get("dps_csh_amt")),
        total_assets=number(body.get("dps_aset_tot_amt")),
        order_available_total=number(body.get("ord_psb_tot_amt")),
        order_available_cash=number(body.get("ord_psb_csh_amt")),
        initial_margin=number(body.get("init_mrgn_tot_amt")),
        maintenance_margin=number(body.get("mtn_mrgn_tam_amt")),
        futures_realized_pnl=number(body.get("fut_rez_pl_amt")),
        total_pnl=number(body.get("pl_tot_pric")),
        fee=number(body.get("fee")),
    )


def fetch_positions(client: NHClient) -> list[Position]:
    rows = _pages(client, POSITIONS_PATH, {})
    return [
        Position(
            code=text(row.get("occurs1_sym")),
            name=text(row.get("occurs1_ko_sym_nm")),
            side=_side(row.get("occurs1_trd_div")),
            quantity=count(row.get("occurs1_opint_qty")),
            closable_quantity=count(row.get("occurs1_cls_psb_qty")),
            avg_price=number(row.get("occurs1_avg_pric")),
            last_price=number(row.get("occurs1_close_pric")),
            pnl=number(row.get("occurs1_pl_amt")),
            pnl_rate=number(row.get("occurs1_pl_rt")),
        )
        for row in rows
    ]


def fetch_orders(client: NHClient, *, open_only: bool = False) -> list[OrderRecord]:
    """오늘의 주문 내역. `open_only`이면 미체결 주문만 조회한다."""
    payload = {"trd_div": "0", "exec_div": "2" if open_only else "0", "trd_tm_div_cd": "0", "ord_div_cd": "0"}
    return [_order(row) for row in _pages(client, ORDER_HISTORY_PATH, payload)]


def fetch_orderable_quantity(
    client: NHClient, code: str, side: Side, price: float | int
) -> OrderableQuantity:
    payload = {
        "ord_sts": DAY_NORMAL,
        "sym": code,
        "trd_div": "1" if side == Side.BUY else "2",
        "ord_pric": price_text(price),
    }
    body = client.call(ORDERABLE_PATH, payload, Limit.ACCOUNT)
    return OrderableQuantity(
        order_quantity=count(body.get("ord_psb_qty")),
        closable_quantity=count(body.get("cls_psb_qty")),
        total_quantity=count(body.get("tot_psb_qty")),
        order_amount=number(body.get("ord_psb_amt")),
    )


def _order(row: dict[str, Any]) -> OrderRecord:
    return OrderRecord(
        order_no=text(row.get("occurs1_ord_no")),
        original_order_no=text(row.get("occurs1_org_ord_no")),
        code=text(row.get("occurs1_sym")),
        side=_side(row.get("occurs1_trd_div")),
        status=STATUS_CODES.get(text(row.get("occurs1_ord_sts")), OrderStatus.UNKNOWN),
        kind=ORDER_KINDS.get(text(row.get("occurs1_ord_div_cd")), "unknown"),
        quantity=count(row.get("occurs1_ord_qty")),
        price=number(row.get("occurs1_ord_pric")),
        filled_quantity=count(row.get("occurs1_exec_qty")),
        filled_price=number(row.get("occurs1_exec_pric")),
        remaining_quantity=count(row.get("occurs1_rem_ord_qty")),
        received_time=text(row.get("occurs1_exch_rcv_tm")),
        reject_reason=text(row.get("occurs1_ord_rejt_rsn")),
    )


def _pages(client: NHClient, path: str, payload: dict[str, str]) -> list[dict[str, Any]]:
    """다음 데이터 키가 있으면 이어받아 모든 줄을 합친다. 같은 키가 반복되면 멈춘다."""
    rows: list[dict[str, Any]] = []
    key = ""
    seen: set[str] = set()
    for _ in range(MAX_PAGES):
        body = client.call(path, {**payload, "nxt_key": key}, Limit.ACCOUNT)
        page = body.get("Occurs1") or []
        if not isinstance(page, list):
            raise NHError(f"{path} 응답의 Occurs1 형식이 올바르지 않습니다")
        rows.extend(page)
        key = text(body.get("nxt_key"))
        if not key or key in seen:
            return rows
        seen.add(key)
    raise NHError(f"{path} 응답이 {MAX_PAGES}쪽을 넘어 이어집니다")
