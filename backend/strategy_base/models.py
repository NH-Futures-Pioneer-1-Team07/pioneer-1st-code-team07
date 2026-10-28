"""전략이 받는 입력과 돌려주는 출력의 형식.

전략은 시세 수신·주문 전송·계좌 조회·파일 저장을 직접 하지 않는다.
`Context`를 읽고 `StrategyOutput`을 돌려주는 것이 전략이 하는 일의 전부다.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"


class IntentKind(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"


class DecisionResult(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    SKIP = "skip"


@dataclass(frozen=True)
class Bar:
    """완성된 봉. `time`은 봉이 시작한 시각(한국 시간)이다."""

    time: datetime
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class Lot:
    """한 번의 진입으로 생긴 보유분(진입분)."""

    entry_id: str
    side: Side
    quantity: int
    entry_price: float


@dataclass(frozen=True)
class OpenOrder:
    """아직 체결이 끝나지 않은 주문."""

    order_id: str
    side: Side
    quantity: int
    filled_quantity: int
    kind: IntentKind
    entry_id: str | None
    placed_at: datetime


@dataclass(frozen=True)
class Context:
    """전략이 판단할 때 받는 입력.

    - `bars`: 완성된 봉, 오래된 것부터. 판단 대상 봉이 마지막이다.
    - `price`: 장중 가격 갱신 때의 현재가. 봉 마감 호출에서는 `None`이다.
    - `state`: 전략이 직전 호출에서 돌려준 상태.
    """

    now: datetime
    bars: Sequence[Bar]
    params: Mapping[str, Any]
    last_trading_day: date | None = None
    price: float | None = None
    lots: Sequence[Lot] = ()
    open_orders: Sequence[OpenOrder] = ()
    state: Mapping[str, Any] = field(default_factory=dict)

    @property
    def net_quantity(self) -> int:
        """보유 순수량. 매수는 양수, 매도는 음수다."""
        return sum(lot.quantity if lot.side == Side.BUY else -lot.quantity for lot in self.lots)


@dataclass(frozen=True)
class OrderIntent:
    """전략이 내는 주문 의도.

    - `kind`: 진입이면 `entry`, 보유분 청산이면 `exit`.
    - `valid_bars`: 주문 유효 시한(봉 개수). `None`이면 시한이 없다.
    - `entry_id`: 진입이면 새 진입분 id, 청산이면 청산할 진입분 id.
    """

    side: Side
    quantity: int
    kind: IntentKind
    entry_id: str
    reason: str
    order_type: OrderType = OrderType.MARKET
    valid_bars: int | None = None


@dataclass(frozen=True)
class CancelRequest:
    order_id: str
    reason: str


@dataclass(frozen=True)
class Decision:
    """매매 판단 기록. 이력의 "매매 판단"으로 표시된다."""

    time: datetime
    result: DecisionResult
    reason: str
    score: float | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyOutput:
    """전략이 돌려주는 출력. 아무것도 하지 않으면 빈 출력을 돌려준다.

    `state`가 `None`이면 상태를 바꾸지 않는다.
    """

    orders: Sequence[OrderIntent] = ()
    cancels: Sequence[CancelRequest] = ()
    decisions: Sequence[Decision] = ()
    state: Mapping[str, Any] | None = None
