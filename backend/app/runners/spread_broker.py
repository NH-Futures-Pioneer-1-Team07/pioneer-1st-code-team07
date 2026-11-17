"""스프레드 종목을 모의매매하는 NH 호출 묶음.

두 종목의 `Broker`를 묶어 스프레드 종목 하나처럼 보이게 한다. 세션은 이 클래스를 일반 `Broker`로 쓴다.

- 주문: 스프레드 주문 하나를 두 종목의 시장가 주문으로 풀어 낸다. 세션에는 `S000001` 같은 스프레드 주문번호를 돌려준다.
- 체결: 두 종목이 모두 체결된 세트 수만 스프레드 체결로 센다.
- 한쪽만 체결된 진입: 체결 확인 제한 시간이 지나면 미체결 주문을 취소하고, 체결된 종목은 시장가로 반대 매매해 원상복구한다.
- 포지션: 두 종목 포지션에서 완성된 세트 수를 스프레드 포지션으로 돌려준다.

취소와 원상복구는 세션이 주문·포지션을 조회할 때 함께 진행한다(별도 스레드가 없다).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.nh.auth import KST
from app.nh.domestic.account import (
    OPEN_STATUSES,
    Deposit,
    OrderableQuantity,
    OrderRecord,
    OrderStatus,
    Position,
)
from app.nh.domestic.quotes import Quote
from app.nh.errors import NHError
from app.nh.realtime_data import Trade
from app.runners.broker import Broker
from app.runners.spread import pair_bars
from strategy_base.manifest import SpreadLeg
from strategy_base.models import Bar, Side

DEFAULT_ENTRY_CONFIRM_SECONDS = 30.0


def _kst_now() -> datetime:
    return datetime.now(KST).replace(tzinfo=None)


def _key(order_no: str) -> str:
    return order_no.strip().lstrip("0")


def _leg_side(side: Side, ratio: int) -> Side:
    """스프레드 주문 방향에서 한 종목의 주문 방향. 비율이 음수인 종목은 반대 방향이다."""
    return side if ratio > 0 else (Side.SELL if side == Side.BUY else Side.BUY)


def _opposite(side: Side) -> Side:
    return Side.SELL if side == Side.BUY else Side.BUY


@dataclass
class _LegOrder:
    index: int
    side: Side
    quantity: int
    order_no: str


@dataclass
class _SpreadOrder:
    number: str
    side: Side
    quantity: int
    entry: bool
    placed_at: datetime
    legs: list[_LegOrder] = field(default_factory=list)
    cancel_requested: bool = False
    unwound: bool = False
    unwind: list[_LegOrder] = field(default_factory=list)
    done: bool = False


class SpreadBroker:
    environment: str

    def __init__(
        self,
        brokers: Sequence[Broker],
        legs: Sequence[SpreadLeg],
        code: str,
        *,
        name: str = "",
        entry_confirm_seconds: float = DEFAULT_ENTRY_CONFIRM_SECONDS,
        clock: Callable[[], datetime] = _kst_now,
    ):
        self.brokers = list(brokers)
        self.legs = list(legs)
        self.code = code
        self.name = name
        self.entry_confirm_seconds = entry_confirm_seconds
        self.clock = clock
        self.environment = self.brokers[0].environment
        self._orders: dict[str, _SpreadOrder] = {}
        self._count = 0

    # ---- 시세와 분봉 ----

    def fetch_bars(self, day) -> list[Bar]:
        first, second = (broker.fetch_bars(day) for broker in self.brokers)
        return pair_bars(first, second, (self.legs[0].price_weight, self.legs[1].price_weight))

    def fetch_quote(self) -> Quote:
        quotes = [broker.fetch_quote() for broker in self.brokers]
        prices = [quote.last_price for quote in quotes]
        price = None if None in prices else sum(leg.price_weight * p for leg, p in zip(self.legs, prices))
        return Quote(self.code, price, None)

    def notional_price(self) -> float | None:
        """두 종목 현재가 × |가중치|의 합. 수수료를 어림하는 데 쓴다."""
        prices = [broker.fetch_quote().last_price for broker in self.brokers]
        if None in prices:
            return None
        return sum(abs(leg.price_weight) * p for leg, p in zip(self.legs, prices))

    # ---- 계좌 ----

    def deposit(self) -> Deposit:
        return self.brokers[0].deposit()

    def orderable(self, side: Side, price: float) -> OrderableQuantity:
        """두 종목의 주문 가능 수량에서 만들 수 있는 세트 수. 스프레드 가격은 종목 가격이 아니므로 시장가 기준(0)으로 묻는다."""
        found = [
            broker.orderable(_leg_side(side, leg.ratio), 0) for broker, leg in zip(self.brokers, self.legs)
        ]

        def sets(values: list[int | None]) -> int:
            return min((value or 0) // abs(leg.ratio) for value, leg in zip(values, self.legs))

        return OrderableQuantity(
            order_quantity=sets([f.order_quantity for f in found]),
            closable_quantity=sets([f.closable_quantity for f in found]),
            total_quantity=sets([f.total_quantity for f in found]),
            order_amount=found[0].order_amount,
        )

    def positions(self) -> list[Position]:
        """완성된 세트를 스프레드 포지션으로, 세트를 이루지 못한 나머지는 종목 포지션 그대로 돌려준다."""
        self._settle()
        found = [self._signed_positions(broker, leg) for broker, leg in zip(self.brokers, self.legs)]
        sets = self._complete_sets([signed for signed, _ in found])
        result: list[Position] = []
        if sets:
            rows = [row for _, row in found]
            avg = [row.avg_price for row in rows]
            last = [row.last_price for row in rows]
            pnl = [row.pnl for row in rows]
            result.append(
                Position(
                    code=self.code,
                    name=self.name,
                    side=Side.BUY if sets > 0 else Side.SELL,
                    quantity=abs(sets),
                    closable_quantity=abs(sets),
                    avg_price=None if None in avg else sum(leg.price_weight * a for leg, a in zip(self.legs, avg)),
                    last_price=None if None in last else sum(leg.price_weight * p for leg, p in zip(self.legs, last)),
                    pnl=None if None in pnl else sum(pnl),
                    pnl_rate=None,
                )
            )
        for (signed, row), leg in zip(found, self.legs):
            rest = abs(signed) - abs(sets) * abs(leg.ratio)
            if row is not None and rest > 0:
                result.append(
                    Position(
                        code=leg.code,
                        name=row.name,
                        side=row.side,
                        quantity=rest,
                        closable_quantity=rest,
                        avg_price=row.avg_price,
                        last_price=row.last_price,
                        pnl=row.pnl,
                        pnl_rate=None,
                    )
                )
        return result

    def _signed_positions(self, broker: Broker, leg: SpreadLeg) -> tuple[int, Any]:
        rows = [row for row in broker.positions() if row.code == leg.code and (row.quantity or 0) != 0]
        signed = sum((row.quantity or 0) * (1 if row.side == Side.BUY else -1) for row in rows)
        return signed, (rows[0] if rows else None)

    def _complete_sets(self, signed: list[int]) -> int:
        """종목별 보유량을 비율로 나눈 값이 모두 같은 방향이면 그중 작은 수가 완성된 세트 수다. 방향은 부호다."""
        units = [value / leg.ratio for value, leg in zip(signed, self.legs)]
        if all(unit > 0 for unit in units):
            return int(min(units))
        if all(unit < 0 for unit in units):
            return -int(min(-unit for unit in units))
        return 0

    # ---- 주문 ----

    def place(self, side: Side, quantity: int) -> str:
        net = self._complete_sets([self._signed_positions(b, leg)[0] for b, leg in zip(self.brokers, self.legs)])
        entry = net == 0 or (net > 0) == (side == Side.BUY)
        self._count += 1
        order = _SpreadOrder(f"S{self._count:06d}", side, quantity, entry, self.clock())
        self._orders[order.number] = order
        try:
            for index, (broker, leg) in enumerate(zip(self.brokers, self.legs)):
                leg_side, leg_quantity = _leg_side(side, leg.ratio), abs(leg.ratio) * quantity
                order_no = broker.place(leg_side, leg_quantity)
                order.legs.append(_LegOrder(index, leg_side, leg_quantity, order_no))
        except BaseException:
            # 일부 종목만 주문됐다. 취소하고 원상복구한 뒤 오류를 그대로 알린다.
            order.cancel_requested = True
            self._settle()
            raise
        return order.number

    def cancel(self, side: Side, quantity: int, order_no: str) -> str:
        order = self._orders.get(order_no)
        if order is None:
            return ""
        self._cancel_legs(order, self._records())
        return f"{order.number}-C"

    def open_orders(self) -> list[OrderRecord]:
        self._settle()
        records = self._records()
        result = [self._spread_record(order, records) for order in self._orders.values() if not order.done]
        known = {
            (leg.index, _key(leg.order_no)) for order in self._orders.values() for leg in order.legs + order.unwind
        }
        for index, broker in enumerate(self.brokers):
            for row in broker.open_orders():
                if (index, _key(row.order_no)) not in known:
                    result.append(row)
        return result

    def orders(self) -> list[OrderRecord]:
        self._settle()
        records = self._records()
        return [self._spread_record(order, records) for order in self._orders.values()]

    # ---- 내부: 주문 상태 ----

    def _records(self) -> list[dict[str, OrderRecord]]:
        return [
            {_key(row.order_no): row for row in broker.orders() if row.kind == "new"} for broker in self.brokers
        ]

    @staticmethod
    def _is_open(record: OrderRecord | None) -> bool:
        return record is not None and record.status in OPEN_STATUSES

    @staticmethod
    def _leg_status(leg: _LegOrder, records: list[dict[str, OrderRecord]]) -> OrderStatus | None:
        record = records[leg.index].get(_key(leg.order_no))
        return record.status if record else None

    def _leg_fill(self, leg: _LegOrder, records: list[dict[str, OrderRecord]]) -> tuple[int, float | None]:
        record = records[leg.index].get(_key(leg.order_no))
        if record is None:
            return 0, None
        return record.filled_quantity or 0, record.filled_price

    def _filled_sets(self, order: _SpreadOrder, records: list[dict[str, OrderRecord]]) -> int:
        if len(order.legs) < len(self.legs):
            return 0
        return min(
            self._leg_fill(leg, records)[0] // abs(spec.ratio) for leg, spec in zip(order.legs, self.legs)
        )

    def _any_open(self, order: _SpreadOrder, records: list[dict[str, OrderRecord]]) -> bool:
        return any(self._is_open(records[leg.index].get(_key(leg.order_no))) for leg in order.legs + order.unwind)

    def _spread_record(self, order: _SpreadOrder, records: list[dict[str, OrderRecord]]) -> OrderRecord:
        filled = self._filled_sets(order, records)
        fills = [self._leg_fill(leg, records) for leg in order.legs]
        price = None
        if filled and len(fills) == len(self.legs) and all(p is not None for _, p in fills):
            price = sum(spec.price_weight * p for spec, (_, p) in zip(self.legs, fills))
        open_now = self._any_open(order, records)
        if filled >= order.quantity:
            status = OrderStatus.FILLED
        elif open_now:
            status = OrderStatus.PARTIAL if filled else OrderStatus.CONFIRMED
        elif order.legs and all(self._leg_status(leg, records) == OrderStatus.REJECTED for leg in order.legs):
            status = OrderStatus.REJECTED
        else:
            status = OrderStatus.AUTO_CANCELLED
        return OrderRecord(
            order_no=order.number,
            original_order_no="0",
            code=self.code,
            side=order.side,
            status=status,
            kind="new",
            quantity=order.quantity,
            price=0.0,
            filled_quantity=filled,
            filled_price=price,
            remaining_quantity=order.quantity - filled if open_now else 0,
            received_time=order.placed_at.strftime("%H%M%S"),
            reject_reason="",
        )

    # ---- 내부: 취소와 원상복구 ----

    def _pending(self) -> list[_SpreadOrder]:
        return [order for order in self._orders.values() if not order.done]

    def _cancel_legs(self, order: _SpreadOrder, records: list[dict[str, OrderRecord]]) -> None:
        order.cancel_requested = True
        for leg in order.legs:
            record = records[leg.index].get(_key(leg.order_no))
            if self._is_open(record):
                try:
                    self.brokers[leg.index].cancel(leg.side, record.remaining_quantity or leg.quantity, leg.order_no)
                except NHError:
                    # 이미 처리 중이거나 거부됐다. 다음 조회에서 상태를 다시 본다.
                    pass

    def _settle(self) -> None:
        """제한 시간이 지난 진입을 취소하고, 취소된 주문의 한쪽만 체결된 종목을 반대 매매한다."""
        pending = self._pending()
        if not pending:
            return
        records = self._records()
        now = self.clock()
        for order in pending:
            if (
                order.entry
                and not order.cancel_requested
                and self._filled_sets(order, records) < order.quantity
                and (now - order.placed_at) >= timedelta(seconds=self.entry_confirm_seconds)
            ):
                self._cancel_legs(order, records)
                records = self._records()
            if not order.cancel_requested:
                if self._filled_sets(order, records) >= order.quantity and not self._any_open(order, records):
                    order.done = True
                continue
            if any(self._is_open(records[leg.index].get(_key(leg.order_no))) for leg in order.legs):
                self._cancel_legs(order, records)
                continue
            if not order.unwound:
                self._unwind(order, records)
            elif not self._any_open(order, records):
                order.done = True

    def _unwind(self, order: _SpreadOrder, records: list[dict[str, OrderRecord]]) -> None:
        sets = self._filled_sets(order, records)
        for leg, spec in zip(order.legs, self.legs):
            excess = self._leg_fill(leg, records)[0] - sets * abs(spec.ratio)
            if excess <= 0:
                continue
            side = _opposite(leg.side)
            try:
                order_no = self.brokers[leg.index].place(side, excess)
            except NHError:
                return  # 다음 조회에서 다시 시도한다.
            order.unwind.append(_LegOrder(leg.index, side, excess, order_no))
        order.unwound = True
        if not order.unwind:
            order.done = True


class SpreadPriceMux:
    """두 종목의 실시간 체결을 받아 스프레드 체결로 바꿔 세션에 전달한다. 다른 이벤트는 그대로 전달한다."""

    def __init__(self, code: str, legs: Sequence[SpreadLeg], post: Callable[[Any], None]):
        self.code = code
        self.legs = list(legs)
        self.post = post
        self.last: dict[str, float] = {}

    def __call__(self, event: Any) -> None:
        if isinstance(event, Trade) and event.code in {leg.code for leg in self.legs}:
            if event.is_trade and event.price is not None:
                self.last[event.code] = event.price
                if len(self.last) == len(self.legs):
                    price = sum(leg.price_weight * self.last[leg.code] for leg in self.legs)
                    self.post(
                        Trade(
                            code=self.code,
                            time=event.time,
                            price=price,
                            quantity=event.quantity,
                            cum_volume=None,
                            open=None,
                            high=None,
                            low=None,
                            best_ask=None,
                            best_bid=None,
                            tick=event.tick,
                        )
                    )
            return
        self.post(event)
