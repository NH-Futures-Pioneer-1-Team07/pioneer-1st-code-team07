"""삼성전자선물 역매매 전략. 연구 코드에 의존하지 않는 실행 전략."""

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
        if params["bar_minutes"] != 3:
            raise ValueError("이 전략의 신호 봉은 3분으로 고정됩니다")
        if params["min_target_ticks"] < 0 or params["tick_size"] <= 0:
            raise ValueError("최소 목표 틱은 0 이상, 틱 간격은 0보다 커야 합니다")
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
            self._release_entry(ctx, work)
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
        bars = [b for b in ctx.bars if b.time.date() == ctx.now.date()
                and b.time.time() >= self._time("signal_start_time")]
        start = 0
        step = timedelta(minutes=self.params["bar_minutes"])
        for index in range(1, len(bars)):
            if bars[index].time - bars[index - 1].time != step:
                start = index
        return bars[start:]

    # ---- 시각·날짜 규칙 ----

    def _exit_on_final_day(self, ctx: Context, work: _Work) -> None:
        self._close_remaining(ctx, work, "최종거래일 보유 포지션 청산", "final_exit_retry_at")
        work.set("final_exit_done", not ctx.lots and not ctx.open_orders)

    def _flatten(self, ctx: Context, work: _Work) -> None:
        if not work.state.get("flatten_started"):
            for order in ctx.open_orders:
                work.cancels.append(CancelRequest(order.order_id, "당일 청산 시각 미체결 주문 취소"))
            self._note(ctx, work, "당일 청산 시각: 미체결 주문 취소 후 전량 청산")
            work.set("flatten_started", True)
        self._close_remaining(ctx, work, "당일 청산", "flatten_retry_at")
        work.set("flatten_done", not ctx.lots and not ctx.open_orders)
        work.set("cutoff_done", True)
        work.set("candidate", None)
        work.set("pending_entry", None)

    def _close_remaining(self, ctx: Context, work: _Work, reason: str, retry_key: str) -> None:
        retry_at = work.state.get(retry_key)
        if retry_at and ctx.now < datetime.fromisoformat(retry_at):
            return
        issued = False
        for lot in ctx.lots:
            reserved = sum(o.quantity-o.filled_quantity for o in ctx.open_orders
                           if o.kind == IntentKind.EXIT and o.entry_id == lot.entry_id)
            remaining = lot.quantity-reserved-work.scheduled_exit.get(lot.entry_id, 0)
            if remaining > 0:
                self._exit(work, lot, remaining, reason)
                issued = True
        if issued:
            work.set(retry_key, (ctx.now+timedelta(seconds=5)).isoformat())

    def _cut_off(self, ctx: Context, work: _Work) -> None:
        if work.state.get("cutoff_done"):
            return
        work.set("cutoff_done", True)
        work.set("pending_entry", None)
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
        if self.params["target_mode"] != TARGET_UPDATE or not bars:
            return
        before = confirmed_swings(bars[:-1], self.params["swing_side_bars"])
        after = confirmed_swings(bars, self.params["swing_side_bars"])
        for lot in ctx.lots:
            position = work.state["positions"].get(lot.entry_id)
            kind = SwingKind.HIGH if lot.side == Side.BUY else SwingKind.LOW
            old, new = latest_swings(before, kind), latest_swings(after, kind)
            if position is None or not new:
                continue
            if (old and new[0].price == old[0].price) or new[0].price == position["target"]:
                continue
            position["target"] = new[0].price
            work.touch()
            passed = bars[-1].close >= position["target"] if lot.side == Side.BUY else bars[-1].close <= position["target"]
            if passed and lot.entry_id not in self._closing_ids(ctx) and not work.scheduled_exit.get(lot.entry_id, 0):
                self._exit_with_decision(ctx, work, lot, position, bars[-1].close, "목표 갱신 후 다음 시가 청산")

    def _check_exits(self, ctx: Context, work: _Work) -> None:
        if ctx.price is None:
            return
        closing = self._closing_ids(ctx)
        for lot in ctx.lots:
            position = work.state["positions"].get(lot.entry_id)
            if position is None or lot.entry_id in closing or work.scheduled_exit.get(lot.entry_id, 0):
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
        if ctx.now.time() < self._time("signal_start_time") or ctx.now.time() >= self._time("entry_cutoff_time"):
            return
        candidate = work.state.get("candidate")
        work.set("candidate", None)
        if candidate:
            if len(bars) >= 2 and candidate["time"] == bars[-2].time.isoformat():
                self._confirm(ctx, work, bars, candidate)
        elif len(bars) >= 2:
            self._find_candidate(ctx, work, bars)

    def _find_candidate(self, ctx: Context, work: _Work, bars: list[Bar]) -> None:
        bar = bars[-1]
        before = confirmed_swings(bars[:-1], self.params["swing_side_bars"])
        highs, lows = latest_swings(before, SwingKind.HIGH), latest_swings(before, SwingKind.LOW)
        if not highs or not lows or highs[0].price <= lows[0].price:
            return
        buy = bar.low <= lows[0].price and bar.close > lows[0].price
        sell = bar.high >= highs[0].price and bar.close < highs[0].price
        detail = {
            "reference_low": lows[0].price,
            "reference_high": highs[0].price,
            "close": bar.close,
        }
        if buy and sell:
            self._skip(ctx, work, "같은 봉에서 매수 후보와 매도 후보가 동시에 발생", detail=detail)
            return
        if not (buy or sell):
            self._hold(ctx, work, "후보 봉 없음", detail)
            return
        side = Side.BUY if buy else Side.SELL
        if ctx.net_quantity and (ctx.net_quantity > 0) != (side == Side.BUY):
            self._skip(ctx, work, "보유 중 반대 방향 후보를 만들지 않음", side, detail)
            return
        reference, opposite = (lows[0], highs[0]) if buy else (highs[0], lows[0])
        work.set(
            "candidate",
            {
                "side": side.value,
                "time": bar.time.isoformat(),
                "reference": reference.price,
                "target": opposite.price,
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
            "expires": expires.isoformat(),
        }
        reason = "저점을 깼다가 회복해 매수" if side == Side.BUY else "고점을 넘었다가 내려와 매도"
        work.set("pending_entry", dict(side=side.value, quantity=self.params["entry_quantity"],
            entry_id=entry_id, reason=reason, valid_bars=valid_bars, at=ctx.now.isoformat()))
        self._hold(ctx, work, "확인 완료: 다음 가격에서 목표거리와 진입 범위 검사",
                   {**detail, "entry_id": entry_id, "stop": stop})

    def _release_entry(self, ctx: Context, work: _Work) -> None:
        pending = work.state.get("pending_entry")
        if not pending or ctx.price is None:
            return
        at = datetime.fromisoformat(pending["at"])
        if ctx.now < at:
            return
        work.set("pending_entry", None)
        side = Side(pending["side"])
        position = work.state["positions"].get(pending["entry_id"])
        reason = self._entry_block(ctx)
        if ctx.now >= at + timedelta(minutes=1):
            reason = "시세 공백으로 다음 진입 구간을 놓침"
        elif position is None:
            reason = "진입 정보가 만료됨"
        elif ctx.open_orders:
            reason = "이전 주문이 처리 중이어서 진입을 건너뜀"
        elif ctx.net_quantity and (ctx.net_quantity > 0) != (side == Side.BUY):
            reason = "보유 중 반대 방향 진입을 건너뜀"
        else:
            inside = position["stop"] < ctx.price < position["target"] if side == Side.BUY else position["target"] < ctx.price < position["stop"]
            distance = (position["target"] - ctx.price) * (1 if side == Side.BUY else -1)
            if not inside:
                reason = "진입 가격이 손절·목표 범위 밖"
            elif distance < self.params["min_target_ticks"] * self.params["tick_size"]:
                reason = "목표까지 거리가 최소 목표 틱 수 미만"
        if reason:
            self._skip(ctx, work, reason, side, {"entry_id": pending["entry_id"], "price": ctx.price})
            return
        work.orders.append(OrderIntent(side, pending["quantity"], IntentKind.ENTRY,
            pending["entry_id"], pending["reason"], valid_bars=pending["valid_bars"]))
        work.decisions.append(Decision(ctx.now, DecisionResult(side.value), pending["reason"],
            detail={"entry_id": pending["entry_id"], "price": ctx.price,
                    "target": position["target"], "stop": position["stop"]}))

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
