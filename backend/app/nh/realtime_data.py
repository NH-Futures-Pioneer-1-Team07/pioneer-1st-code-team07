"""실시간 메시지를 변환한 결과. 계좌번호는 읽지 않는다."""

from dataclasses import dataclass, field
from typing import Any

from app.nh.domestic.account import STATUS_CODES, OrderStatus
from app.nh.values import count, number, text
from strategy_base.models import Side

BOOK_LEVELS = 10


@dataclass(frozen=True)
class Feed:
    """구독 하나. 시세는 종목이 필요하고 주문/체결 알림은 종목이 없다."""

    action_code: str
    symbol: str | None = None

    def __post_init__(self) -> None:
        if self.action_code in ("KA", "KB"):
            if not self.symbol:
                raise ValueError(f"{self.action_code} 구독에는 종목코드가 필요합니다")
        elif self.action_code == "O1":
            if self.symbol:
                raise ValueError("O1(주문/체결) 구독에는 종목코드를 쓰지 않습니다")
        else:
            raise ValueError(f"지원하지 않는 실시간 구분: {self.action_code}")


@dataclass(frozen=True)
class Trade:
    """체결(KA). `tick`이 `1`인 것만 실제 체결이고, `0`은 체결량이 0인 기타 데이터다."""

    code: str
    time: str
    price: float | None
    quantity: int | None
    cum_volume: int | None
    open: float | None
    high: float | None
    low: float | None
    best_ask: float | None
    best_bid: float | None
    tick: str

    @property
    def is_trade(self) -> bool:
        return self.tick == "1"


@dataclass(frozen=True)
class BookLevel:
    ask_price: float | None
    ask_quantity: int | None
    bid_price: float | None
    bid_quantity: int | None


@dataclass(frozen=True)
class OrderBook:
    """호가(KB). `levels[0]`이 1단계(최우선)다."""

    code: str
    time: str
    total_ask_quantity: int | None
    total_bid_quantity: int | None
    levels: list[BookLevel] = field(default_factory=list)


@dataclass(frozen=True)
class OrderEvent:
    """주문/체결 알림(O1)."""

    order_no: str
    original_order_no: str
    code: str
    side: Side | None
    status: OrderStatus
    quantity: int | None
    filled_quantity: int | None
    price: float | None
    filled_price: float | None
    execution_quantity: int | None
    remaining_quantity: int | None
    error_code: str
    received_time: str
    executed_time: str


@dataclass(frozen=True)
class SubscriptionFailed:
    """서버가 거절한 구독. 어느 구독인지 알 수 없으면 `feed`가 `None`이다."""

    feed: Feed | None
    code: str
    message: str


@dataclass(frozen=True)
class Reconnected:
    """끊겼다가 다시 연결됐다. 끊긴 동안의 값은 오지 않으므로 조회로 채워야 한다."""


def parse_trade(body: dict[str, Any], symbol: str = "") -> Trade:
    return Trade(
        code=text(body.get("sym")) or symbol,
        time=text(body.get("exch_tm")),
        price=number(body.get("last_pric")),
        quantity=count(body.get("exec_qty")),
        cum_volume=count(body.get("cum_trd_qty")),
        open=number(body.get("open_pric")),
        high=number(body.get("high_pric")),
        low=number(body.get("low_pric")),
        best_ask=number(body.get("ask_best_pric")),
        best_bid=number(body.get("bid_best_pric")),
        tick=text(body.get("tick_div")),
    )


def parse_order_book(body: dict[str, Any], symbol: str = "") -> OrderBook:
    levels = []
    for step in range(1, BOOK_LEVELS + 1):
        level = BookLevel(
            ask_price=number(body.get(f"ask_pric_{step}")),
            ask_quantity=count(body.get(f"ask_qty_{step}")),
            bid_price=number(body.get(f"bid_pric_{step}")),
            bid_quantity=count(body.get(f"bid_qty_{step}")),
        )
        if level.ask_price is not None or level.bid_price is not None:
            levels.append(level)
    return OrderBook(
        code=text(body.get("sym")) or symbol,
        time=text(body.get("exch_tm")),
        total_ask_quantity=count(body.get("ask_qty")),
        total_bid_quantity=count(body.get("bid_qty")),
        levels=levels,
    )


def parse_order_event(body: dict[str, Any]) -> OrderEvent:
    return OrderEvent(
        order_no=text(body.get("ord_no")),
        original_order_no=text(body.get("org_ord_no")),
        code=text(body.get("sym")),
        side={"1": Side.BUY, "2": Side.SELL}.get(text(body.get("trd_div"))),
        status=STATUS_CODES.get(text(body.get("ord_sts")), OrderStatus.UNKNOWN),
        quantity=count(body.get("ord_qty")),
        filled_quantity=count(body.get("exec_qty")),
        price=number(body.get("ord_pric")),
        filled_price=number(body.get("exec_pric")),
        execution_quantity=count(body.get("per_exec_qty")),
        remaining_quantity=count(body.get("rem_ord_qty")),
        error_code=text(body.get("err_cd")),
        received_time=text(body.get("rcv_tm")),
        executed_time=text(body.get("exec_tm")),
    )
