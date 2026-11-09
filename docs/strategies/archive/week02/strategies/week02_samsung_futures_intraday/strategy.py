"""삼성전자선물 장중 전략. 판단 규칙은 docs/strategies/week02_samsung_futures_intraday.md를 따른다."""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from fractions import Fraction
from typing import Any

from strategy_base.indicators import Swing, SwingKind, average_volume, confirmed_swings, latest_swings
from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Bar,
    CancelRequest,
    Context,
    Decision,
    DecisionResult,
    IntentKind,
    Lot,
    OrderIntent,
    Side,
    StrategyOutput,
)

UP = "up"
DOWN = "down"


@dataclass
class _Work:
    """한 번의 호출 동안 모으는 출력과 갱신할 상태."""

    state: dict[str, Any]
    orders: list[OrderIntent] = field(default_factory=list)
    cancels: list[CancelRequest] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    scheduled_exit: dict[str, int] = field(default_factory=dict)
    changed: bool = False

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value
        self.changed = True


@dataclass(frozen=True)
class _Detection:
    side: Side | None
    reason: str
    detail: dict[str, Any]


class Strategy(BaseStrategy):
    def on_bar(self, ctx: Context) -> StrategyOutput:
        return self._run(ctx, evaluate_signal=True)

    def on_price(self, ctx: Context) -> StrategyOutput:
        return self._run(ctx, evaluate_signal=False)

    # ---- 호출 흐름 ----

    def _run(self, ctx: Context, evaluate_signal: bool) -> StrategyOutput:
        work = self._start(ctx)
        now_time = ctx.now.time()
        final_day = ctx.last_trading_day is not None and ctx.last_trading_day == ctx.now.date()

        if final_day:
            self._exit_on_final_day(ctx, work)
        if now_time >= self._time("flatten_time"):
            already_flattened = bool(work.state.get("flatten_done"))
            self._flatten(ctx, work)
            if already_flattened and evaluate_signal:
                self._skip(ctx, work, "당일 청산 시각 이후에는 신호를 판단하지 않음")
            return self._finish(work)
        if now_time >= self._time("entry_cutoff_time"):
            self._cut_off(ctx, work)
        self._resolve_pending_flip(ctx, work)
        if evaluate_signal:
            self._evaluate_signal(ctx, work)
        return self._finish(work)

    def _start(self, ctx: Context) -> _Work:
        day = ctx.now.date().isoformat()
        if ctx.state.get("day") == day:
            return _Work(dict(ctx.state))
        return _Work({"day": day, "entry_count": 0}, changed=True)

    def _finish(self, work: _Work) -> StrategyOutput:
        return StrategyOutput(
            orders=work.orders,
            cancels=work.cancels,
            decisions=work.decisions,
            state=work.state if work.changed else None,
        )

    # ---- 시각·날짜 규칙 ----

    def _exit_on_final_day(self, ctx: Context, work: _Work) -> None:
        if work.state.get("final_exit_done") or not ctx.lots:
            return
        closing = {order.entry_id for order in ctx.open_orders if order.kind == IntentKind.EXIT}
        for lot in ctx.lots:
            if lot.entry_id not in closing:
                self._exit(work, lot, lot.quantity, "최종거래일 보유 포지션 청산")
        work.set("final_exit_done", True)
        self._note(ctx, work, "최종거래일 보유 포지션 청산을 시도")

    def _flatten(self, ctx: Context, work: _Work) -> None:
        if work.state.get("flatten_done"):
            return
        for order in ctx.open_orders:
            work.cancels.append(CancelRequest(order.order_id, "당일 청산 시각 미체결 주문 취소"))
        for lot in ctx.lots:
            remaining = lot.quantity - work.scheduled_exit.get(lot.entry_id, 0)
            if remaining > 0:
                self._exit(work, lot, remaining, "당일 청산")
        work.set("flatten_done", True)
        work.set("cutoff_done", True)
        work.set("pending_flip", None)
        self._note(ctx, work, "당일 청산 시각: 미체결 주문 취소 후 전량 청산")

    def _cut_off(self, ctx: Context, work: _Work) -> None:
        if work.state.get("cutoff_done"):
            return
        work.set("cutoff_done", True)
        work.set("pending_flip", None)
        for order in ctx.open_orders:
            work.cancels.append(CancelRequest(order.order_id, "신규 진입 제한 시각 장중 미체결 주문 취소"))
            remaining = order.quantity - order.filled_quantity
            if order.kind == IntentKind.EXIT and remaining > 0:
                work.orders.append(
                    OrderIntent(
                        side=order.side,
                        quantity=remaining,
                        kind=IntentKind.EXIT,
                        entry_id=order.entry_id or order.order_id,
                        reason="취소한 청산 주문의 남은 수량 청산",
                    )
                )
        self._note(ctx, work, "신규 진입 제한 시각: 장중 미체결 주문 취소")

    def _entry_block(self, ctx: Context) -> str | None:
        """신규 진입·보유 수량 증가를 막는 이유. 막을 이유가 없으면 `None`."""
        if ctx.last_trading_day is None:
            return "최종거래일을 확인하지 못해 신규 진입을 하지 않음"
        if ctx.last_trading_day == ctx.now.date():
            return "최종거래일에는 신규 진입을 하지 않음"
        if ctx.now.time() >= self._time("entry_cutoff_time"):
            return "신규 진입 제한 시각 이후에는 신규 진입을 하지 않음"
        return None

    # ---- 반대 신호 초과분 신규 진입 ----

    def _resolve_pending_flip(self, ctx: Context, work: _Work) -> None:
        pending = work.state.get("pending_flip")
        if not pending:
            return
        side = Side(pending["side"])
        if ctx.now >= datetime.fromisoformat(pending["deadline"]):
            work.set("pending_flip", None)
            self._skip(ctx, work, "반대 방향 신규 진입 기한이 지나 초과분 진입을 하지 않음")
            return
        block = self._entry_block(ctx)
        if block:
            work.set("pending_flip", None)
            self._skip(ctx, work, f"반대 방향 초과분 진입을 하지 않음: {block}")
            return
        if ctx.lots or ctx.open_orders:
            return
        work.set("pending_flip", None)
        order = self._entry(ctx, work, side, pending["quantity"], "반대 신호 초과분 신규 진입")
        work.decisions.append(
            Decision(ctx.now, DecisionResult(side.value), order.reason, detail={"quantity": order.quantity})
        )

    # ---- 신호 ----

    def _evaluate_signal(self, ctx: Context, work: _Work) -> None:
        bars = [bar for bar in ctx.bars if bar.time.date() == ctx.now.date()]
        if len(bars) < 2:
            self._hold(ctx, work, "당일 완성 봉이 2개보다 적음", {})
            return
        detection = self._detect(bars)
        if detection.side is None:
            self._hold(ctx, work, detection.reason, detection.detail)
            return

        side = detection.side
        count = self.params["volume_avg_bars"]
        previous = bars[:-1]
        if average_volume(previous, count) is None:
            self._skip(ctx, work, f"직전 완성 봉이 {count}개보다 적음", side, detection.detail)
            return
        total = sum(bar.volume for bar in previous[-count:])
        if total == 0:
            self._skip(ctx, work, "평균 거래량이 0", side, detection.detail)
            return
        if ctx.open_orders:
            self._skip(ctx, work, "이전 주문이 미체결이어서 신호를 건너뜀", side, detection.detail)
            return
        if work.state.get("pending_flip"):
            self._skip(ctx, work, "반대 방향 전환이 진행 중이어서 신호를 건너뜀", side, detection.detail)
            return

        factor = Fraction(self.params["quantity_factor"]).limit_denominator(1000)
        quantity = math.floor(factor * bars[-1].volume * count / total)
        detail = {**detection.detail, "average_volume": total / count, "quantity": quantity}
        if quantity <= 0:
            self._skip(ctx, work, "계산된 수량이 0", side, detail)
            return
        self._trade(ctx, work, side, quantity, detection.reason, detail)

    def _detect(self, bars: list[Bar]) -> _Detection:
        side_bars = self.params["swing_side_bars"]
        signal, previous = bars[-1], bars[-2]
        trend = self._trend(confirmed_swings(bars, side_bars))
        before = confirmed_swings(bars[:-1], side_bars)
        high = latest_swings(before, SwingKind.HIGH)
        low = latest_swings(before, SwingKind.LOW)
        detail: dict[str, Any] = {
            "trend": trend,
            "close": signal.close,
            "reference_high": high[0].price if high else None,
            "reference_low": low[0].price if low else None,
        }
        if trend is None:
            return _Detection(None, "추세 판단 보류", detail)
        if trend == UP:
            if not high:
                return _Detection(None, "기준 고점이 없음", detail)
            if previous.close <= high[0].price < signal.close:
                return _Detection(Side.BUY, "상승 추세에서 기준 고점 돌파", detail)
        else:
            if not low:
                return _Detection(None, "기준 저점이 없음", detail)
            if previous.close >= low[0].price > signal.close:
                return _Detection(Side.SELL, "하락 추세에서 기준 저점 돌파", detail)
        return _Detection(None, "돌파 없음", detail)

    def _trend(self, swings: list[Swing]) -> str | None:
        count = self.params["trend_compare_count"]
        highs = [swing.price for swing in latest_swings(swings, SwingKind.HIGH, count)]
        lows = [swing.price for swing in latest_swings(swings, SwingKind.LOW, count)]
        if len(highs) < count or len(lows) < count:
            return None
        if _increasing(highs) and _increasing(lows):
            return UP
        if _increasing(highs[::-1]) and _increasing(lows[::-1]):
            return DOWN
        return None

    # ---- 주문 만들기 ----

    def _trade(
        self, ctx: Context, work: _Work, side: Side, quantity: int, reason: str, detail: dict[str, Any]
    ) -> None:
        net = ctx.net_quantity
        block = self._entry_block(ctx)
        if net == 0 or (net > 0) == (side == Side.BUY):
            if block:
                self._skip(ctx, work, block, side, detail)
                return
            self._entry(ctx, work, side, quantity, reason)
            work.decisions.append(Decision(ctx.now, DecisionResult(side.value), reason, detail=detail))
            return

        held = abs(net)
        self._reduce(work, ctx.lots, min(quantity, held), reason)
        excess = quantity - held
        detail = {**detail, "reduce_quantity": min(quantity, held), "excess_quantity": max(excess, 0)}
        if excess > 0:
            if block:
                detail["excess_dropped"] = block
            else:
                minutes = self.params["bar_minutes"] * self.params["order_valid_bars"]
                deadline = ctx.now + timedelta(minutes=minutes)
                work.set(
                    "pending_flip",
                    {"side": side.value, "quantity": excess, "deadline": deadline.isoformat()},
                )
        work.decisions.append(Decision(ctx.now, DecisionResult(side.value), reason, detail=detail))

    def _entry(self, ctx: Context, work: _Work, side: Side, quantity: int, reason: str) -> OrderIntent:
        number = work.state["entry_count"] + 1
        work.set("entry_count", number)
        order = OrderIntent(
            side=side,
            quantity=quantity,
            kind=IntentKind.ENTRY,
            entry_id=f"{work.state['day']}-{number}",
            reason=reason,
            valid_bars=self.params["order_valid_bars"],
        )
        work.orders.append(order)
        return order

    def _reduce(self, work: _Work, lots: Sequence[Lot], quantity: int, reason: str) -> None:
        """보유분을 오래된 것부터 `quantity`만큼 청산한다."""
        remaining = quantity
        for lot in lots:
            if remaining <= 0:
                break
            amount = min(lot.quantity, remaining)
            self._exit(work, lot, amount, reason)
            remaining -= amount

    def _exit(self, work: _Work, lot: Lot, quantity: int, reason: str) -> None:
        work.orders.append(
            OrderIntent(
                side=Side.SELL if lot.side == Side.BUY else Side.BUY,
                quantity=quantity,
                kind=IntentKind.EXIT,
                entry_id=lot.entry_id,
                reason=reason,
            )
        )
        work.scheduled_exit[lot.entry_id] = work.scheduled_exit.get(lot.entry_id, 0) + quantity

    # ---- 판단 기록 ----

    def _hold(self, ctx: Context, work: _Work, reason: str, detail: dict[str, Any]) -> None:
        work.decisions.append(Decision(ctx.now, DecisionResult.HOLD, reason, detail=detail))

    def _skip(
        self,
        ctx: Context,
        work: _Work,
        reason: str,
        side: Side | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = {**(detail or {}), **({"signal": side.value} if side else {})}
        work.decisions.append(Decision(ctx.now, DecisionResult.SKIP, reason, detail=detail))

    def _note(self, ctx: Context, work: _Work, reason: str) -> None:
        work.decisions.append(Decision(ctx.now, DecisionResult.HOLD, reason))

    def _time(self, name: str) -> time:
        return time.fromisoformat(self.params[name])


def _increasing(values: list[float]) -> bool:
    return all(later > earlier for earlier, later in zip(values, values[1:]))
