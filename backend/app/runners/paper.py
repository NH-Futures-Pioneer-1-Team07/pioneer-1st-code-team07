"""모의매매 세션. 전략을 NH 모의계좌로 운용한다.

모든 처리는 하나의 흐름에서 순서대로 한다(`run`이 큐의 이벤트와 1초 주기 `tick`을 번갈아 처리한다).

- 분봉: `poll_interval`마다 분봉을 조회해 마감된 봉을 한 번씩 `on_bar`에 전달한다.
  운용을 시작한 뒤에 시작한 당일 봉만 쓴다.
- 가격: 실시간 체결을 `on_price`에 전달한다. 실시간이 끊기면 현재가 조회로 대신한다.
- 주문: 전략의 주문 의도를 시장가 주문으로 보낸다. 거부된 주문과 처리 여부를 모르는 주문은 다시 보내지 않는다.
- 원장: 체결 알림으로 갱신한다. 알림이 없어도 주문 내역 조회로 맞춘다.
- 안전: 계좌와 원장이 어긋나거나 주문 상태를 모르거나 시세·분봉이 끊기면 신규 진입을 막는다. 청산은 막지 않는다.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from app.nh.account import OrderRecord, OrderStatus
from app.nh.auth import KST
from app.nh.errors import BusinessError, NHConfigError, NHError
from app.nh.orders import OrderBlocked
from app.nh.realtime_data import OrderEvent, Reconnected, SubscriptionFailed, Trade
from app.records.store import RunRecorder
from app.runners.broker import Broker
from app.runners.ledger import ClosedTrade, Ledger
from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Bar,
    CancelRequest,
    Context,
    IntentKind,
    OpenOrder,
    OrderIntent,
    OrderType,
    Side,
    StrategyOutput,
)

logger = logging.getLogger(__name__)

RUNNING, CLEARING, STOPPING, STOPPED = "running", "clearing", "stopping", "stopped"
TICK_SECONDS = 1.0


@dataclass(frozen=True)
class PaperConfig:
    code: str
    name: str
    multiplier: int
    minutes: int
    fee_rate: float
    poll_interval: float = 5.0
    reconcile_interval: float = 10.0
    stop_reconcile_interval: float = 2.0
    stale_after: float = 30.0
    bar_grace: float = 2.0
    stop_timeout: float = 90.0
    flatten_retry: float = 5.0
    unknown_checks: int = 3
    price_throttle: float = 1.0
    session_anchor: time = time(8, 45)


@dataclass(frozen=True)
class StopRequest:
    """종료 요청. `account_wide`이면 계좌 전체 확인은 하지 않는다(계좌 전체 정리가 맡는다)."""

    account_wide: bool = False


@dataclass(frozen=True)
class PauseRequest:
    """계좌 전체 정리를 시작한다. 전략 판단과 신규 주문을 멈추고 상태만 따라간다."""


@dataclass(frozen=True)
class StateChange:
    state: str
    detail: str = ""


@dataclass
class Tracked:
    """우리가 낸 주문 하나."""

    order_no: str
    intent: OrderIntent
    quantity: int
    placed_at: datetime
    expires_at: datetime | None
    score: float | None = None
    filled: int = 0
    status: str = "open"  # open, filled, closed, rejected
    cancel_requested: bool = False

    @property
    def remaining(self) -> int:
        return self.quantity - self.filled


@dataclass
class Unknown:
    """보낸 뒤 처리 여부를 알 수 없는 주문."""

    number: int
    intent: OrderIntent
    quantity: int
    placed_at: datetime
    score: float | None
    checks: int = 0


def kst_now() -> datetime:
    return datetime.now(KST).replace(tzinfo=None)


def _same_order(left: str, right: str) -> bool:
    return left.strip().lstrip("0") == right.strip().lstrip("0")


class PaperSession:
    def __init__(
        self,
        strategy: BaseStrategy,
        config: PaperConfig,
        broker: Broker,
        recorder: RunRecorder,
        *,
        started_at: datetime,
        last_trading_day: date | None,
        deposit_before: dict[str, Any] | None = None,
        clock: Callable[[], datetime] = kst_now,
    ):
        self.strategy = strategy
        self.config = config
        self.broker = broker
        self.recorder = recorder
        self.started_at = started_at
        self.last_trading_day = last_trading_day
        self.deposit_before = deposit_before
        self.clock = clock

        self.ledger = Ledger(multiplier=config.multiplier, fee_rate=config.fee_rate)
        self.state: dict[str, Any] = {}
        self.bars: list[Bar] = []
        self.seen_bars: set[datetime] = set()
        self.tracked: dict[str, Tracked] = {}
        self.unknown: list[Unknown] = []
        self._unknown_count = 0

        self.queue: asyncio.Queue[Any] = asyncio.Queue()
        self.done = asyncio.Event()
        self.phase = RUNNING
        self.verify_account = True
        self.final_status: str | None = None

        self.feed_state = "connecting"
        self.last_price: float | None = None
        self.price_at: datetime | None = None
        self.last_bar_time: datetime | None = None
        self.last_bar_ok: datetime = started_at
        self.last_called_price: tuple[float, datetime] | None = None
        self.mismatch: str | None = None
        self.mismatch_streak = 0
        self.account_net: int | None = None
        self.account_open: list[OrderRecord] = []
        self.account_clean = False

        self.next_poll = started_at
        self.next_quote = started_at
        self.next_reconcile = started_at + timedelta(seconds=config.reconcile_interval)
        self.stop_started: datetime | None = None
        self.last_flatten_try: datetime | None = None
        self.scores: dict[str, float | None] = {}
        self.logged_errors: dict[str, datetime] = {}
        self.snapshot: dict[str, Any] = {}
        self._notified_pnl: float | None = None

    # ---- 실행 ----

    def post(self, item: Any) -> None:
        self.queue.put_nowait(item)

    def begin_stop(self, account_wide: bool = False) -> None:
        self.post(StopRequest(account_wide))

    def begin_pause(self) -> None:
        self.post(PauseRequest())

    async def run(self) -> None:
        self._note("운용 시작", strategy=self.config.name, code=self.config.code)
        while not self.done.is_set():
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=TICK_SECONDS)
            except TimeoutError:
                item = None
            try:
                if item is not None:
                    await self.handle(item)
                await self.tick(self.clock())
            except Exception as error:
                await self._fail(error)
            self.publish()

    async def handle(self, item: Any) -> None:
        now = self.clock()
        if isinstance(item, Trade):
            await self._on_trade(item, now)
        elif isinstance(item, OrderEvent):
            await self._on_order_event(item, now)
        elif isinstance(item, StateChange):
            self.feed_state = item.state
            self._note("실시간 연결 상태", state=item.state, detail=item.detail)
        elif isinstance(item, Reconnected):
            self._note("실시간이 다시 연결되어 분봉과 계좌를 다시 조회합니다")
            self.next_poll = self.next_reconcile = now
        elif isinstance(item, SubscriptionFailed):
            self._note("실시간 구독이 거절되었습니다", level="warning", code=item.code, message=item.message)
        elif isinstance(item, PauseRequest):
            if self.phase == RUNNING:
                self.phase = CLEARING
                self._note("계좌 전체 정리를 시작해 전략 판단과 신규 주문을 멈춥니다")
        elif isinstance(item, StopRequest):
            await self._begin_stop(now, item.account_wide)

    async def tick(self, now: datetime) -> None:
        if self.done.is_set():
            return
        await self._expire_orders(now)
        if self.phase == RUNNING and now >= self.next_poll:
            self.next_poll = now + timedelta(seconds=self.config.poll_interval)
            await self._poll_bars(now)
        if self.feed_state != "live" and now >= self.next_quote:
            self.next_quote = now + timedelta(seconds=self.config.poll_interval)
            await self._poll_quote(now)
        if now >= self.next_reconcile:
            urgent = self.phase == STOPPING or bool(self.unknown)
            interval = self.config.stop_reconcile_interval if urgent else self.config.reconcile_interval
            self.next_reconcile = now + timedelta(seconds=interval)
            await self._reconcile(now)
        if self.phase == STOPPING:
            await self._stop_step(now)

    # ---- 가격과 분봉 ----

    async def _on_trade(self, trade: Trade, now: datetime) -> None:
        if trade.code != self.config.code or not trade.is_trade or trade.price is None:
            return
        await self._on_price(trade.price, now)

    async def _on_price(self, price: float, now: datetime) -> None:
        self.last_price, self.price_at = price, now
        if self.phase != RUNNING:
            return
        last = self.last_called_price
        if last and last[0] == price and (now - last[1]).total_seconds() < self.config.price_throttle:
            return
        self.last_called_price = (price, now)
        await self._call(self.strategy.on_price, now, now, price)

    async def _poll_quote(self, now: datetime) -> None:
        try:
            quote = await asyncio.to_thread(self.broker.fetch_quote)
        except NHError as error:
            self._error_event("현재가 조회에 실패했습니다", error, now)
            return
        if quote.last_trading_day is not None:
            self.last_trading_day = quote.last_trading_day
        if quote.last_price is not None:
            await self._on_price(quote.last_price, now)

    async def _poll_bars(self, now: datetime) -> None:
        try:
            bars = await asyncio.to_thread(self.broker.fetch_bars, now.date())
        except NHError as error:
            self._error_event("분봉 조회에 실패했습니다", error, now)
            return
        self.last_bar_ok = now
        width = timedelta(minutes=self.config.minutes, seconds=self.config.bar_grace)
        ready = sorted(
            (b for b in bars if b.time >= self.started_at and b.time not in self.seen_bars and b.time + width <= now),
            key=lambda bar: bar.time,
        )
        for bar in ready:
            self.seen_bars.add(bar.time)
            self.bars = [b for b in self.bars if b.time.date() == bar.time.date()] + [bar]
            self.last_bar_time = bar.time
            if self.phase == RUNNING:
                close = bar.time + timedelta(minutes=self.config.minutes)
                await self._call(self.strategy.on_bar, close, now, None)

    # ---- 전략 호출 ----

    async def _call(
        self, hook: Callable[[Context], StrategyOutput], decision_now: datetime, now: datetime, price: float | None
    ) -> None:
        ctx = Context(
            now=decision_now,
            bars=list(self.bars),
            params=self.strategy.params,
            last_trading_day=self.last_trading_day,
            price=price,
            lots=self.ledger.lots(),
            open_orders=self._open_orders(),
            state=self.state,
        )
        output = hook(ctx)
        if output.state is not None:
            self.state = dict(output.state)
        score = next((d.score for d in output.decisions if d.score is not None), None)
        for decision in output.decisions:
            self.recorder.record(
                "decision",
                time=decision.time,
                result=decision.result.value,
                reason=decision.reason,
                score=decision.score,
                detail=dict(decision.detail),
                orders=[
                    {"side": o.side.value, "quantity": o.quantity, "entry_id": o.entry_id} for o in output.orders
                ],
            )
        for cancel in output.cancels:
            await self._cancel_by_strategy(cancel, now)
        for intent in output.orders:
            await self._submit(intent, now, score)

    def _open_orders(self) -> list[OpenOrder]:
        orders = [
            OpenOrder(
                order_id=t.order_no,
                side=t.intent.side,
                quantity=t.quantity,
                filled_quantity=t.filled,
                kind=t.intent.kind,
                entry_id=t.intent.entry_id,
                placed_at=t.placed_at,
            )
            for t in self.tracked.values()
            if t.status == "open"
        ]
        orders += [
            OpenOrder(
                order_id=f"unknown-{u.number}",
                side=u.intent.side,
                quantity=u.quantity,
                filled_quantity=0,
                kind=u.intent.kind,
                entry_id=u.intent.entry_id,
                placed_at=u.placed_at,
            )
            for u in self.unknown
        ]
        return orders

    # ---- 주문 ----

    def entry_blocks(self, now: datetime) -> list[str]:
        """신규 진입을 막는 이유. 비어 있으면 낼 수 있다."""
        reasons = []
        if self.phase != RUNNING:
            reasons.append("계좌 전체 정리 중" if self.phase == CLEARING else "종료 중")
        if self.unknown:
            reasons.append("주문 처리 여부를 확인하지 못함")
        if self.mismatch:
            reasons.append(self.mismatch)
        stale = timedelta(seconds=self.config.stale_after)
        if now - self.last_bar_ok > stale:
            reasons.append("분봉 조회가 계속 실패함")
        if self.feed_state != "live" and (self.price_at is None or now - self.price_at > stale):
            reasons.append("시세를 받지 못함")
        return reasons

    async def _submit(self, intent: OrderIntent, now: datetime, score: float | None) -> None:
        if intent.order_type != OrderType.MARKET:
            self._note("시장가가 아닌 주문은 지원하지 않아 무시했습니다", level="warning", entry_id=intent.entry_id)
            return
        if intent.kind == IntentKind.ENTRY:
            reasons = self.entry_blocks(now)
            if reasons:
                self._order_record("blocked", intent, now, reason="신규 진입 차단: " + ", ".join(reasons))
                return
            quantity = await self._entry_quantity(intent, now)
        else:
            quantity = self._exit_quantity(intent, now)
        if quantity <= 0:
            return
        try:
            order_no = await asyncio.to_thread(self.broker.place, intent.side, quantity)
        except BusinessError as error:
            self._order_record("rejected", intent, now, quantity=quantity, code=error.code, message=error.detail)
            return
        except OrderBlocked:
            raise
        except NHConfigError:
            raise
        except NHError as error:
            # 요청이 처리됐는지 알 수 없다. 다시 보내지 않고 주문 내역으로 확인한다.
            self._unknown_count += 1
            self.unknown.append(Unknown(self._unknown_count, intent, quantity, now, score))
            self._order_record("unknown", intent, now, quantity=quantity, error=type(error).__name__)
            self.next_reconcile = now + timedelta(seconds=self.config.stop_reconcile_interval)
            return
        self.scores[intent.entry_id] = score
        self.tracked[order_no] = Tracked(
            order_no, intent, quantity, now, self._expiry(intent, now), score=score
        )
        self._order_record("submitted", intent, now, quantity=quantity, order_no=order_no)
        self.next_reconcile = now + timedelta(seconds=self.config.stop_reconcile_interval)

    async def _entry_quantity(self, intent: OrderIntent, now: datetime) -> int:
        price = self.last_price
        if price is None:
            self._order_record("skipped", intent, now, reason="현재가를 알 수 없어 주문가능수량을 확인하지 못함")
            return 0
        try:
            orderable = await asyncio.to_thread(self.broker.orderable, intent.side, price)
        except NHError as error:
            self._error_event("주문가능수량 조회에 실패했습니다", error, now)
            self._order_record("skipped", intent, now, reason="주문가능수량 조회 실패")
            return 0
        available = orderable.order_quantity or 0
        quantity = min(intent.quantity, available)
        if quantity <= 0:
            self._order_record(
                "skipped", intent, now, reason="주문가능수량이 0", available=available
            )
        elif quantity < intent.quantity:
            self._note(
                "주문가능수량만큼만 주문합니다",
                entry_id=intent.entry_id,
                planned_quantity=intent.quantity,
                quantity=quantity,
            )
        return quantity

    def _exit_quantity(self, intent: OrderIntent, now: datetime) -> int:
        position = self.ledger.positions.get(intent.entry_id)
        if position is None or position.side == intent.side:
            self._note("청산할 진입분이 없어 청산 주문을 무시했습니다", level="warning", entry_id=intent.entry_id)
            return 0
        pending = sum(
            t.remaining
            for t in self.tracked.values()
            if t.status == "open" and t.intent.kind == IntentKind.EXIT and t.intent.entry_id == intent.entry_id
        ) + sum(u.quantity for u in self.unknown if u.intent.kind == IntentKind.EXIT and u.intent.entry_id == intent.entry_id)
        quantity = min(intent.quantity, position.open_quantity - pending)
        if quantity <= 0:
            self._order_record("skipped", intent, now, reason="이미 청산 주문이 나간 수량")
        return quantity

    def _expiry(self, intent: OrderIntent, now: datetime) -> datetime | None:
        if intent.valid_bars is None:
            return None
        width = timedelta(minutes=self.config.minutes)
        anchor = datetime.combine(now.date(), self.config.session_anchor)
        steps = int((now - anchor) / width) + 1 if now >= anchor else 0
        return anchor + width * (steps + intent.valid_bars - 1)

    def _order_record(
        self, status: str, intent: OrderIntent, now: datetime, quantity: int | None = None, **fields: Any
    ) -> None:
        fields = {"reason": intent.reason, **fields}
        self.recorder.record(
            "order",
            time=now,
            status=status,
            side=intent.side.value,
            quantity=quantity if quantity is not None else intent.quantity,
            planned_quantity=intent.quantity,
            order_type=intent.order_type.value,
            intent=intent.kind.value,
            entry_id=intent.entry_id,
            **fields,
        )

    async def _cancel_by_strategy(self, cancel: CancelRequest, now: datetime) -> None:
        tracked = self.tracked.get(cancel.order_id)
        if tracked is None or tracked.status != "open":
            self._note("취소할 주문이 없어 취소 요청을 무시했습니다", level="warning", order_id=cancel.order_id)
            return
        await self._cancel(tracked, cancel.reason, now)

    async def _cancel(self, tracked: Tracked, reason: str, now: datetime) -> None:
        if tracked.cancel_requested or tracked.remaining <= 0:
            return
        tracked.cancel_requested = True
        try:
            await asyncio.to_thread(self.broker.cancel, tracked.intent.side, tracked.remaining, tracked.order_no)
        except NHError as error:
            self._note(
                "취소 요청이 거부되었거나 확인하지 못했습니다",
                level="warning",
                order_no=tracked.order_no,
                error=type(error).__name__,
                detail=str(error),
            )
        else:
            self._order_record("cancel_requested", tracked.intent, now, order_no=tracked.order_no, cancel_reason=reason)
        self.next_reconcile = now + timedelta(seconds=self.config.stop_reconcile_interval)

    async def _expire_orders(self, now: datetime) -> None:
        for tracked in list(self.tracked.values()):
            if tracked.status == "open" and tracked.expires_at and now >= tracked.expires_at:
                await self._cancel(tracked, "주문 유효 시한", now)

    # ---- 체결 반영 ----

    async def _on_order_event(self, event: OrderEvent, now: datetime) -> None:
        tracked = self.tracked.get(event.order_no)
        if tracked is None:
            if event.code == self.config.code and not event.original_order_no:
                self._note("우리가 내지 않은 주문의 알림을 받았습니다", level="warning", order_no=event.order_no)
            return
        if event.status == OrderStatus.REJECTED:
            tracked.status = "rejected"
            self._order_record("rejected", tracked.intent, now, order_no=tracked.order_no, code=event.error_code)
        elif event.status in (OrderStatus.PARTIAL, OrderStatus.FILLED):
            if event.filled_quantity is not None:
                cumulative = event.filled_quantity
            else:
                cumulative = tracked.filled + (event.execution_quantity or 0)
            self._apply_fill(tracked, cumulative, event.filled_price, now, "notification")
        elif event.status == OrderStatus.AUTO_CANCELLED:
            self._close(tracked, "자동 취소", now)

    def _apply_fill(self, tracked: Tracked, cumulative: int, price: float | None, now: datetime, source: str) -> None:
        delta = min(cumulative, tracked.quantity) - tracked.filled
        if delta <= 0 or price is None:
            return
        intent = tracked.intent
        if intent.kind == IntentKind.ENTRY:
            applied = self.ledger.apply_entry(intent.entry_id, intent.side, delta, price, now)
        else:
            applied = self.ledger.apply_exit(intent.entry_id, intent.side, delta, price, now)
        if applied is None:
            self._note("체결을 원장에 반영하지 못했습니다", level="error", order_no=tracked.order_no, entry_id=intent.entry_id)
            return
        tracked.filled += applied.quantity
        self.recorder.record(
            "fill",
            time=now,
            side=intent.side.value,
            quantity=applied.quantity,
            price=price,
            fee=applied.fee,
            fee_estimated=True,
            intent=intent.kind.value,
            entry_id=intent.entry_id,
            reason=intent.reason,
            order_no=tracked.order_no,
            score=tracked.score,
            source=source,
        )
        if applied.trade is not None:
            self._record_trade(applied.trade, now)
        if tracked.filled >= tracked.quantity:
            tracked.status = "filled"

    def _record_trade(self, trade: ClosedTrade, now: datetime) -> None:
        self.recorder.record(
            "trade",
            time=now,
            entry_id=trade.entry_id,
            side=trade.side.value,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            gross_pnl=trade.gross_pnl,
            fee=trade.fee,
            fee_estimated=True,
            net_pnl=trade.net_pnl,
            opened_at=trade.opened_at.isoformat() if trade.opened_at else None,
        )

    def _close(self, tracked: Tracked, why: str, now: datetime) -> None:
        if tracked.status == "open":
            tracked.status = "closed"
            self._order_record(
                "closed", tracked.intent, now, order_no=tracked.order_no, filled_quantity=tracked.filled, closed_because=why
            )

    # ---- 계좌 대조 ----

    async def _reconcile(self, now: datetime) -> None:
        try:
            positions = await asyncio.to_thread(self.broker.positions)
            open_orders = await asyncio.to_thread(self.broker.open_orders)
        except NHError as error:
            self._error_event("계좌 조회에 실패했습니다", error, now)
            return
        code = self.config.code
        account_net = sum(
            (p.quantity or 0) * (1 if p.side == Side.BUY else -1) for p in positions if p.code == code
        )
        account_open = [o for o in open_orders if o.code == code]
        open_numbers = {o.order_no for o in account_open}
        missing = [t for t in self.tracked.values() if t.status == "open" and not any(_same_order(t.order_no, n) for n in open_numbers)]
        if missing or self.unknown or account_net != self.ledger.net_quantity():
            await self._sync_history(now)
            missing = [
                t for t in self.tracked.values()
                if t.status == "open" and not any(_same_order(t.order_no, n) for n in open_numbers)
            ]
        for tracked in missing:
            self._close(tracked, "계좌의 미체결에 없음", now)

        self.account_net, self.account_open = account_net, account_open
        foreign = [
            o for o in account_open
            if not any(_same_order(o.order_no, t.order_no) for t in self.tracked.values())
        ]
        problems = []
        if account_net != self.ledger.net_quantity():
            problems.append(f"계좌 포지션 {account_net}, 원장 {self.ledger.net_quantity()}")
        if foreign and not self.unknown:
            problems.append("계좌에 알 수 없는 미체결 주문이 있음")
        if problems:
            self.mismatch_streak += 1
            if self.mismatch_streak >= 2:
                text = "계좌와 원장이 어긋남: " + "; ".join(problems)
                if text != self.mismatch:
                    self._note(text, level="warning")
                self.mismatch = text
        else:
            if self.mismatch:
                self._note("계좌와 원장이 다시 일치합니다")
            self.mismatch, self.mismatch_streak = None, 0
        self.account_clean = account_net == 0 and not account_open

    async def _sync_history(self, now: datetime) -> None:
        """주문 내역으로 체결 알림을 놓친 체결을 반영하고, 처리 여부를 모르는 주문을 찾는다."""
        try:
            records = await asyncio.to_thread(self.broker.orders)
        except NHError as error:
            self._error_event("주문 내역 조회에 실패했습니다", error, now)
            return
        by_number = {r.order_no: r for r in records}
        for tracked in list(self.tracked.values()):
            record = next((r for n, r in by_number.items() if _same_order(n, tracked.order_no)), None)
            if record is None:
                continue
            self._sync_record(tracked, record, now)
        for unknown in list(self.unknown):
            unknown.checks += 1
            match = next(
                (
                    r for r in records
                    if r.kind == "new"
                    and r.side == unknown.intent.side
                    and r.quantity == unknown.quantity
                    and not any(_same_order(r.order_no, t.order_no) for t in self.tracked.values())
                    and r.received_time >= (unknown.placed_at - timedelta(seconds=5)).strftime("%H%M%S")
                ),
                None,
            )
            if match is not None:
                tracked = Tracked(
                    match.order_no, unknown.intent, unknown.quantity, unknown.placed_at,
                    self._expiry(unknown.intent, unknown.placed_at), score=unknown.score,
                )
                self.tracked[match.order_no] = tracked
                self.unknown.remove(unknown)
                self._note("처리 여부를 몰랐던 주문을 주문 내역에서 찾았습니다", order_no=match.order_no)
                self._sync_record(tracked, match, now)
            elif unknown.checks >= self.config.unknown_checks:
                self.unknown.remove(unknown)
                self._note(
                    "주문 내역에서 찾지 못해 접수되지 않은 것으로 판단합니다", level="warning", entry_id=unknown.intent.entry_id
                )

    def _sync_record(self, tracked: Tracked, record: OrderRecord, now: datetime) -> None:
        if record.filled_quantity:
            self._apply_fill(tracked, record.filled_quantity, record.filled_price, now, "history")
        if record.status == OrderStatus.REJECTED and tracked.status == "open":
            tracked.status = "rejected"
            self._order_record("rejected", tracked.intent, now, order_no=tracked.order_no, message=record.reject_reason)
        elif record.status in (OrderStatus.AUTO_CANCELLED,):
            self._close(tracked, "자동 취소", now)

    # ---- 종료 ----

    async def _begin_stop(self, now: datetime, account_wide: bool = False) -> None:
        if self.phase not in (RUNNING, CLEARING):
            return
        self.phase = STOPPING
        self.verify_account = not account_wide
        self.stop_started = now
        self.account_clean = False
        self.next_reconcile = now
        self._note("운용 종료를 시작합니다: 신규 판단을 멈추고 미체결 주문을 취소한 뒤 보유분을 청산합니다")

    async def _stop_step(self, now: datetime) -> None:
        assert self.stop_started is not None
        if (now - self.stop_started).total_seconds() > self.config.stop_timeout:
            await self._finish("error", "종료 확인 시간이 지나 마치지 못했습니다", now)
            return
        for tracked in list(self.tracked.values()):
            if tracked.status == "open" and not tracked.cancel_requested:
                await self._cancel(tracked, "운용 종료", now)
        if any(t.status == "open" for t in self.tracked.values()) or self.unknown:
            return
        lots = self.ledger.lots()
        if lots:
            retry = timedelta(seconds=self.config.flatten_retry)
            if self.last_flatten_try is None or now - self.last_flatten_try >= retry:
                self.last_flatten_try = now
                for lot in lots:
                    intent = OrderIntent(
                        side=Side.SELL if lot.side == Side.BUY else Side.BUY,
                        quantity=lot.quantity,
                        kind=IntentKind.EXIT,
                        entry_id=lot.entry_id,
                        reason="운용 종료 청산",
                    )
                    await self._submit(intent, now, None)
            return
        if not self.verify_account or (self.account_clean and self.mismatch is None):
            await self._finish("completed", "", now)

    async def _fail(self, error: Exception) -> None:
        logger.error("모의매매가 오류로 멈췄습니다: %s", type(error).__name__)
        await self._finish(
            "error",
            f"{type(error).__name__}: {error}. 보유 포지션과 미체결 주문이 남아 있을 수 있으니 계좌를 확인하세요",
            self.clock(),
        )

    async def _finish(self, status: str, note: str, now: datetime) -> None:
        if self.done.is_set():
            return
        deposit_after = None
        try:
            deposit = await asyncio.to_thread(self.broker.deposit)
            deposit_after = _deposit_dict(deposit)
        except Exception:
            pass
        ledger = self.ledger
        result = {
            "gross_pnl": ledger.gross_pnl,
            "fee": ledger.fee,
            "fee_estimated": True,
            "net_pnl": ledger.net_pnl,
            "trade_count": ledger.trades,
            "win_count": ledger.wins,
            "loss_count": ledger.losses,
            "open_lots": [{"entry_id": l.entry_id, "side": l.side.value, "quantity": l.quantity} for l in ledger.lots()],
            "account": {
                "before": self.deposit_before,
                "after": deposit_after,
                "fee_change": _change(self.deposit_before, deposit_after, "fee"),
                "realized_pnl_change": _change(self.deposit_before, deposit_after, "futures_realized_pnl"),
            },
        }
        if note:
            self._note(note, level="error" if status == "error" else "info")
        self._note("운용 종료" if status == "completed" else "운용이 오류로 끝났습니다", net_pnl=ledger.net_pnl)
        self.recorder.finish(result, status=status)
        self.final_status = status
        self.phase = STOPPED
        self.done.set()

    # ---- 상태와 기록 ----

    def publish(self) -> None:
        now = self.clock()
        price = self.last_price
        unrealized = self.ledger.unrealized(price) if price is not None else 0.0
        if self.ledger.net_pnl != self._notified_pnl:
            self._notified_pnl = self.ledger.net_pnl
            self.recorder.notify_pnl(self._notified_pnl)
        self.snapshot = {
            "phase": self.phase,
            "feed": self.feed_state,
            "last_price": price,
            "last_price_at": self.price_at.isoformat() if self.price_at else None,
            "last_bar_time": self.last_bar_time.isoformat() if self.last_bar_time else None,
            "entry_blocks": self.entry_blocks(now),
            "pnl": {
                "realized_pnl": self.ledger.gross_pnl,
                "unrealized_pnl": unrealized,
                "fee": self.ledger.fee,
                "fee_estimated": True,
                "total_pnl": self.ledger.net_pnl + unrealized,
                "trade_count": self.ledger.trades,
            },
            "lots": [{"entry_id": l.entry_id, "side": l.side.value, "quantity": l.quantity, "entry_price": l.entry_price}
                     for l in self.ledger.lots()],
            "open_orders": [o.order_id for o in self._open_orders()],
        }

    def _note(self, text: str, level: str = "info", **fields: Any) -> None:
        self.recorder.record("event", level=level, text=text, **fields)

    def _error_event(self, text: str, error: Exception, now: datetime) -> None:
        """같은 오류를 30초에 한 번만 기록한다."""
        key = f"{text}:{type(error).__name__}"
        last = self.logged_errors.get(key)
        if last is None or (now - last).total_seconds() >= 30:
            self.logged_errors[key] = now
            self._note(text, level="warning", error=type(error).__name__, detail=str(error))


def _deposit_dict(deposit: Any) -> dict[str, Any]:
    return {
        "cash": deposit.cash,
        "total_assets": deposit.total_assets,
        "fee": deposit.fee,
        "futures_realized_pnl": deposit.futures_realized_pnl,
        "total_pnl": deposit.total_pnl,
    }


def _change(before: dict[str, Any] | None, after: dict[str, Any] | None, key: str) -> float | None:
    if not before or not after or before.get(key) is None or after.get(key) is None:
        return None
    return after[key] - before[key]
