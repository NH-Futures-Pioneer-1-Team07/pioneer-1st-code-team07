"""삼성전자선물 고저점 역매매 전략. 판단 규칙은 docs/strategies/week02_samsung_futures_reversal.md를 따른다."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from fractions import Fraction
from typing import Any

from strategy_base.indicators import SwingKind, average_volume, confirmed_swings, latest_swings
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

TARGET_UPDATE = "갱신"
TARGET_FIXED = "고정"


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

    def touch(self) -> None:
        self.changed = True


class Strategy(BaseStrategy):
    def __init__(self, params: Mapping[str, Any]):
        super().__init__(params)
        if params["target_mode"] not in (TARGET_UPDATE, TARGET_FIXED):
            raise ValueError(f"target_mode는 '{TARGET_UPDATE}' 또는 '{TARGET_FIXED}'이어야 합니다")

    def on_bar(self, ctx: Context) -> StrategyOutput:
        return self._run(ctx, on_bar=True)

    def on_price(self, ctx: Context) -> StrategyOutput:
        return self._run(ctx, on_bar=False)

    # ---- 호출 흐름 ----

    def _run(self, ctx: Context, on_bar: bool) -> StrategyOutput:
        work = self._start(ctx)
        now_time = ctx.now.time()
        final_day = ctx.last_trading_day is not None and ctx.last_trading_day == ctx.now.date()

        if final_day:
            self._exit_on_final_day(ctx, work)
        if now_time >= self._time("flatten_time"):
            already_flattened = bool(work.state.get("flatten_done"))
            self._flatten(ctx, work)
            if already_flattened and on_bar:
                self._skip(ctx, work, "당일 청산 시각 이후에는 신호를 판단하지 않음")
            return self._finish(work)
        if now_time >= self._time("entry_cutoff_time"):
            self._cut_off(ctx, work)

        self._prune_positions(ctx, work)
        if on_bar:
            bars = self._today_bars(ctx)
            self._update_targets(ctx, work, bars)
            self._evaluate_signal(ctx, work, bars)
        else:
            self._check_exits(ctx, work)
        return self._finish(work)

    def _start(self, ctx: Context) -> _Work:
        day = ctx.now.date().isoformat()
        if ctx.state.get("day") == day:
            return _Work(dict(ctx.state))
        return _Work({"day": day, "entry_count": 0, "candidate": None, "positions": {}}, changed=True)

    def _finish(self, work: _Work) -> StrategyOutput:
        return StrategyOutput(
            orders=work.orders,
            cancels=work.cancels,
            decisions=work.decisions,
            state=work.state if work.changed else None,
        )

    def _today_bars(self, ctx: Context) -> list[Bar]:
        return [bar for bar in ctx.bars if bar.time.date() == ctx.now.date()]

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
        work.set("candidate", None)
        self._note(ctx, work, "당일 청산 시각: 미체결 주문 취소 후 전량 청산")

    def _cut_off(self, ctx: Context, work: _Work) -> None:
        if work.state.get("cutoff_done"):
            return
        work.set("cutoff_done", True)
        if work.state.get("candidate"):
            self._skip(ctx, work, "신규 진입 제한 시각이 되어 후보 봉을 확인하지 않음")
        work.set("candidate", None)
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
        """신규·추가 진입을 막는 이유. 막을 이유가 없으면 `None`."""
        if ctx.last_trading_day is None:
            return "최종거래일을 확인하지 못해 신규 진입을 하지 않음"
        if ctx.last_trading_day == ctx.now.date():
            return "최종거래일에는 신규 진입을 하지 않음"
        if ctx.now.time() >= self._time("entry_cutoff_time"):
            return "신규 진입 제한 시각 이후에는 신규 진입을 하지 않음"
        return None

    # ---- 진입분 관리 ----

    def _prune_positions(self, ctx: Context, work: _Work) -> None:
        """보유도 미체결도 없고 주문 유효 시한도 지난 진입분 정보를 지운다."""
        positions: dict[str, Any] = work.state["positions"]
        alive = {lot.entry_id for lot in ctx.lots} | {
            order.entry_id for order in ctx.open_orders if order.entry_id
        }
        for entry_id in list(positions):
            expires = datetime.fromisoformat(positions[entry_id]["expires"])
            if entry_id not in alive and ctx.now >= expires:
                del positions[entry_id]
                work.touch()

    def _update_targets(self, ctx: Context, work: _Work, bars: list[Bar]) -> None:
        """목표 갱신 방식: 보유 중 새로 확정된 반대쪽 고점·저점으로 목표를 바꾸고, 이미 지났으면 청산한다."""
        if self.params["target_mode"] != TARGET_UPDATE or not bars:
            return
        swings = confirmed_swings(bars, self.params["swing_side_bars"])
        price = ctx.price if ctx.price is not None else bars[-1].close
        closing = self._closing_ids(ctx)
        for lot in ctx.lots:
            position = work.state["positions"].get(lot.entry_id)
            if position is None:
                continue
            kind = SwingKind.HIGH if lot.side == Side.BUY else SwingKind.LOW
            fresh = [s for s in swings if s.kind == kind and s.confirmed_index > position["since_index"]]
            if not fresh or fresh[-1].index <= position["target_index"]:
                continue
            position["target"] = fresh[-1].price
            position["target_index"] = fresh[-1].index
            work.touch()
            reason = _exit_reason(lot.side, price, position)
            if reason and lot.entry_id not in closing:
                self._exit_with_decision(ctx, work, lot, position, price, f"{reason} (목표 갱신 시점)")

    def _check_exits(self, ctx: Context, work: _Work) -> None:
        if ctx.price is None:
            return
        closing = self._closing_ids(ctx)
        for lot in ctx.lots:
            position = work.state["positions"].get(lot.entry_id)
            if position is None or lot.entry_id in closing:
                continue
            reason = _exit_reason(lot.side, ctx.price, position)
            if reason:
                self._exit_with_decision(ctx, work, lot, position, ctx.price, reason)

    def _closing_ids(self, ctx: Context) -> set[str]:
        """이미 청산 주문이 나간 진입분 id."""
        return {order.entry_id for order in ctx.open_orders if order.kind == IntentKind.EXIT and order.entry_id}

    def _exit_with_decision(
        self, ctx: Context, work: _Work, lot: Lot, position: dict[str, Any], price: float, reason: str
    ) -> None:
        self._exit(work, lot, lot.quantity, reason)
        side = Side.SELL if lot.side == Side.BUY else Side.BUY
        detail = {
            "entry_id": lot.entry_id,
            "price": price,
            "stop": position["stop"],
            "target": position["target"],
        }
        work.decisions.append(Decision(ctx.now, DecisionResult(side.value), reason, detail=detail))

    # ---- 신호 ----

    def _evaluate_signal(self, ctx: Context, work: _Work, bars: list[Bar]) -> None:
        if len(bars) < 2:
            self._hold(ctx, work, "당일 완성 봉이 2개보다 적음")
            return
        candidate = work.state.get("candidate")
        work.set("candidate", None)
        if candidate and candidate["time"] == bars[-2].time.isoformat():
            self._confirm(ctx, work, bars, candidate)
        self._find_candidate(ctx, work, bars)

    def _find_candidate(self, ctx: Context, work: _Work, bars: list[Bar]) -> None:
        bar = bars[-1]
        before = confirmed_swings(bars[:-1], self.params["swing_side_bars"])
        low = latest_swings(before, SwingKind.LOW)
        high = latest_swings(before, SwingKind.HIGH)
        buy = bool(low) and bar.low <= low[0].price and bar.close > low[0].price
        sell = bool(high) and bar.high >= high[0].price and bar.close < high[0].price
        detail = {
            "reference_low": low[0].price if low else None,
            "reference_high": high[0].price if high else None,
            "close": bar.close,
        }
        if buy and sell:
            self._skip(ctx, work, "같은 봉에서 매수 후보와 매도 후보가 동시에 발생", detail=detail)
            return
        if not (buy or sell):
            self._hold(ctx, work, "후보 봉 없음", detail)
            return
        side = Side.BUY if buy else Side.SELL
        reference, opposite = (low[0], high) if buy else (high[0], low)
        if not opposite:
            name = "고점" if buy else "저점"
            self._skip(ctx, work, f"반대쪽 확정 {name}이 없음", side, detail)
            return
        work.set(
            "candidate",
            {
                "side": side.value,
                "time": bar.time.isoformat(),
                "reference": reference.price,
                "target": opposite[0].price,
                "target_index": opposite[0].index,
            },
        )
        self._hold(ctx, work, f"{side.value} 후보 봉 발생, 다음 봉에서 확인", detail)

    def _confirm(self, ctx: Context, work: _Work, bars: list[Bar], candidate: dict[str, Any]) -> None:
        side = Side(candidate["side"])
        bar = bars[-1]
        reference = candidate["reference"]
        confirmed = bar.close > reference if side == Side.BUY else bar.close < reference
        detail = {"reference": reference, "close": bar.close, "target": candidate["target"]}
        if not confirmed:
            self._hold(ctx, work, "확인 봉 종가가 기준을 넘지 못해 신호가 아님", detail)
            return

        count = self.params["volume_avg_bars"]
        previous = bars[:-1]
        if average_volume(previous, count) is None:
            self._skip(ctx, work, f"직전 완성 봉이 {count}개보다 적음", side, detail)
            return
        total = sum(b.volume for b in previous[-count:])
        if total == 0:
            self._skip(ctx, work, "평균 거래량이 0", side, detail)
            return
        ratio = Fraction(self.params["volume_min_ratio"]).limit_denominator(1000)
        if bar.volume * count < ratio * total:
            self._skip(ctx, work, "확인 봉 거래량이 평균 거래량의 최소 배수 미만", side, detail)
            return
        if ctx.net_quantity != 0 and (ctx.net_quantity > 0) != (side == Side.BUY):
            self._skip(ctx, work, "보유 중 반대 방향 신호를 건너뜀", side, detail)
            return
        if ctx.open_orders:
            self._skip(ctx, work, "이전 주문이 미체결이거나 청산 주문이 처리 중이어서 신호를 건너뜀", side, detail)
            return
        block = self._entry_block(ctx)
        if block:
            self._skip(ctx, work, block, side, detail)
            return
        self._enter(ctx, work, bars, side, candidate, detail)

    def _enter(
        self,
        ctx: Context,
        work: _Work,
        bars: list[Bar],
        side: Side,
        candidate: dict[str, Any],
        detail: dict[str, Any],
    ) -> None:
        number = work.state["entry_count"] + 1
        work.set("entry_count", number)
        entry_id = f"{work.state['day']}-{number}"
        valid_bars = self.params["order_valid_bars"]
        offset = self.params["stop_offset"]
        reference = candidate["reference"]
        stop = reference - offset if side == Side.BUY else reference + offset
        expires = ctx.now + timedelta(minutes=self.params["bar_minutes"] * (valid_bars + 1))
        work.state["positions"][entry_id] = {
            "side": side.value,
            "stop": stop,
            "target": candidate["target"],
            "target_index": candidate["target_index"],
            "since_index": len(bars) - 1,
            "expires": expires.isoformat(),
        }
        reason = "저점을 깼다가 회복해 매수" if side == Side.BUY else "고점을 넘었다가 내려와 매도"
        work.orders.append(
            OrderIntent(
                side=side,
                quantity=self.params["entry_quantity"],
                kind=IntentKind.ENTRY,
                entry_id=entry_id,
                reason=reason,
                valid_bars=valid_bars,
            )
        )
        work.decisions.append(
            Decision(
                ctx.now,
                DecisionResult(side.value),
                reason,
                detail={**detail, "entry_id": entry_id, "stop": stop, "quantity": self.params["entry_quantity"]},
            )
        )

    # ---- 주문·판단 기록 ----

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

    def _hold(self, ctx: Context, work: _Work, reason: str, detail: dict[str, Any] | None = None) -> None:
        work.decisions.append(Decision(ctx.now, DecisionResult.HOLD, reason, detail=detail or {}))

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


def _exit_reason(side: Side, price: float, position: Mapping[str, Any]) -> str | None:
    """가격이 손절 또는 목표에 도달했는지 본다. 둘 다 도달하면 손절이다."""
    if side == Side.BUY:
        stop_hit, target_hit = price <= position["stop"], price >= position["target"]
    else:
        stop_hit, target_hit = price >= position["stop"], price <= position["target"]
    if stop_hit:
        return "손절"
    if target_hit:
        return "이익 청산 목표 도달"
    return None
