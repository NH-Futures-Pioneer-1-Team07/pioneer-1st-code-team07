"""계좌 조회와 전체 정리. 운용 중인 전략이 있는지와 무관하게 계좌 전체를 대상으로 한다."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.nh.account import (
    Deposit,
    OrderRecord,
    Position,
    fetch_deposit,
    fetch_orders,
    fetch_positions,
)
from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.orders import cancel_order, place_order
from strategy_base.models import Side

logger = logging.getLogger(__name__)


class AccountGateway(Protocol):
    """계좌 전체에 대한 NH 호출. 모두 동기 호출이다."""

    environment: str

    def deposit(self) -> Deposit: ...

    def positions(self) -> list[Position]: ...

    def open_orders(self) -> list[OrderRecord]: ...

    def cancel(self, code: str, side: Side, quantity: int, order_no: str) -> str: ...

    def close(self, code: str, side: Side, quantity: int) -> str: ...


class NHAccountGateway:
    def __init__(self, client: NHClient):
        self._client = client
        self.environment = client.environment

    def deposit(self) -> Deposit:
        return fetch_deposit(self._client)

    def positions(self) -> list[Position]:
        return fetch_positions(self._client)

    def open_orders(self) -> list[OrderRecord]:
        return fetch_orders(self._client, open_only=True)

    def cancel(self, code: str, side: Side, quantity: int, order_no: str) -> str:
        return cancel_order(self._client, code, side, quantity, order_no)

    def close(self, code: str, side: Side, quantity: int) -> str:
        return place_order(self._client, code, side, quantity)


@dataclass(frozen=True)
class ClearConfig:
    poll: float = 1.0
    cancel_timeout: float = 30.0
    stop_timeout: float = 120.0
    flatten_timeout: float = 60.0
    flatten_retry: float = 5.0


def account_view(gateway: AccountGateway) -> dict[str, Any]:
    """화면에 보여 줄 계좌 상태. 계좌번호·계좌명은 읽지 않는다."""
    deposit = gateway.deposit()
    return {
        "deposit": {
            "cash": deposit.cash,
            "total_assets": deposit.total_assets,
            "order_available_total": deposit.order_available_total,
            "order_available_cash": deposit.order_available_cash,
            "initial_margin": deposit.initial_margin,
            "maintenance_margin": deposit.maintenance_margin,
            "futures_realized_pnl": deposit.futures_realized_pnl,
        },
        "positions": [_position(p) for p in gateway.positions() if (p.quantity or 0) != 0],
        "open_orders": [_order(o) for o in gateway.open_orders()],
    }


def _position(p: Position) -> dict[str, Any]:
    return {
        "code": p.code,
        "name": p.name,
        "side": p.side.value if p.side else None,
        "quantity": p.quantity,
        "closable_quantity": p.closable_quantity,
        "avg_price": p.avg_price,
        "last_price": p.last_price,
        "pnl": p.pnl,
        "pnl_rate": p.pnl_rate,
    }


def _order(o: OrderRecord) -> dict[str, Any]:
    return {
        "order_no": o.order_no,
        "code": o.code,
        "side": o.side.value if o.side else None,
        "status": o.status.value,
        "quantity": o.quantity,
        "filled_quantity": o.filled_quantity,
        "remaining_quantity": o.remaining_quantity,
        "price": o.price,
    }


def _remaining(order: OrderRecord) -> int:
    if order.remaining_quantity:
        return order.remaining_quantity
    return max((order.quantity or 0) - (order.filled_quantity or 0), 0)


def run_clear(
    gateway: AccountGateway,
    config: ClearConfig,
    *,
    report: Callable[[str, str], None],
    stop_run: Callable[[], None],
    run_active: Callable[[], bool],
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """미체결 취소 → 운용 종료 → 남은 포지션 청산 → 확인 순서로 계좌를 정리한다.

    `report(단계, 설명)`으로 진행을 알린다. 운용 중인 전략은 호출하기 전에 이미 판단을 멈췄다고 본다.
    """
    cancelled, closed, problems = 0, [], []

    report("cancel", "계좌 전체의 미체결 주문을 취소합니다")
    asked: set[str] = set()
    deadline = monotonic() + config.cancel_timeout
    while True:
        orders = gateway.open_orders()
        if not orders:
            break
        for order in orders:
            if order.order_no in asked or order.side is None:
                continue
            asked.add(order.order_no)
            try:
                gateway.cancel(order.code, order.side, _remaining(order), order.order_no)
                cancelled += 1
            except NHError as error:
                problems.append(f"주문 {order.order_no} 취소 실패: {type(error).__name__}")
        if monotonic() > deadline:
            problems.append("미체결 주문 취소가 시간 안에 끝나지 않았습니다")
            break
        sleep(config.poll)

    report("stop_run", "운용 중인 전략을 종료합니다")
    stop_run()
    deadline = monotonic() + config.stop_timeout
    while run_active():
        if monotonic() > deadline:
            problems.append("운용 종료가 시간 안에 끝나지 않았습니다")
            break
        sleep(config.poll)

    report("flatten", "남은 포지션을 청산합니다")
    deadline = monotonic() + config.flatten_timeout
    last_try: float | None = None
    while True:
        positions = [p for p in gateway.positions() if (p.quantity or 0) > 0 and p.side is not None]
        if not positions:
            break
        if monotonic() > deadline:
            problems.append("포지션 청산이 시간 안에 끝나지 않았습니다")
            break
        waiting = gateway.open_orders()
        due = last_try is None or monotonic() - last_try >= config.flatten_retry
        if due and not waiting:
            last_try = monotonic()
            for position in positions:
                side = Side.SELL if position.side == Side.BUY else Side.BUY
                quantity = position.closable_quantity or position.quantity or 0
                try:
                    gateway.close(position.code, side, quantity)
                    closed.append({"code": position.code, "side": side.value, "quantity": quantity})
                except NHError as error:
                    problems.append(f"{position.code} 청산 주문 실패: {type(error).__name__}")
        sleep(config.poll)

    report("verify", "정리 결과를 조회합니다")
    remaining_orders = [_order(o) for o in gateway.open_orders()]
    remaining_positions = [_position(p) for p in gateway.positions() if (p.quantity or 0) != 0]
    return {
        "status": "completed" if not remaining_orders and not remaining_positions else "incomplete",
        "open_orders": remaining_orders,
        "positions": remaining_positions,
        "cancelled": cancelled,
        "closed": closed,
        "problems": problems,
    }
