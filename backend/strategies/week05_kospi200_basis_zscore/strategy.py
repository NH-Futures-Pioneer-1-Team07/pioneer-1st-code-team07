import math
import statistics
from datetime import time, timedelta
from typing import Any

from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Bar,
    Context,
    Decision,
    DecisionResult,
    IntentKind,
    OrderIntent,
    Side,
    StrategyOutput,
)

BAR_MINUTES = 5
SIGNAL_START, SIGNAL_END = time(9, 0), time(15, 20)


class Strategy(BaseStrategy):
    """코스피200 베이시스 z-score 전략. 판단 규칙은 `docs/strategies/week05_kospi200_basis_zscore.md`를 따른다.

    - 베이시스는 `선물 종가 - 지수 종가(Bar.reference)`이다. 지수 종가가 없는 봉과 신호 시간(09:00~15:20) 밖의 봉은 쓰지 않는다.
    - z-score는 현재 봉을 뺀 직전 `window_bars`개 유효 봉으로 계산한다(모표준편차).
    - 진입: 직전 봉의 `|z| < entry_z`이고 현재 봉의 `|z| >= entry_z`일 때 1계약. z가 양수면 매도, 음수면 매수.
    - 청산: 증거금 대비 평가손익률이 `±exit_return_pct`에 닿으면 전량 청산한다(이익·손절 모두).
    - 재진입: 청산 판단을 한 봉이 마감된 뒤에 시작한 두 봉이 진입 조건을 충족해야 한다.
    """

    def on_bar(self, ctx: Context) -> StrategyOutput:
        facts = self._facts(ctx)
        state = dict(ctx.state)
        state.setdefault("sequence", 0)

        if ctx.lots:
            return self._manage(ctx, state, facts)
        if ctx.open_orders:
            return self._record(ctx, state, DecisionResult.HOLD, "진행 중인 주문이 있어 판단 보류", facts)
        return self._look_for_entry(ctx, state, facts)

    # ---- 판단 수치 ----

    def _usable(self, ctx: Context) -> list[Bar]:
        """지수 종가가 있고 신호 시간 안에 있는 봉(오래된 것부터)."""
        return [
            bar
            for bar in ctx.bars
            if bar.reference is not None and SIGNAL_START <= bar.time.time() < SIGNAL_END
        ]

    def _z(self, usable: list[Bar], index: int) -> float | None:
        """`usable[index]`의 z-score. 직전 `window_bars`개가 모자라거나 표준편차가 0이면 `None`."""
        window = int(self.params["window_bars"])
        if index < window:
            return None
        history = [bar.close - bar.reference for bar in usable[index - window : index]]
        deviation = statistics.pstdev(history)
        if deviation == 0 or not math.isfinite(deviation):
            return None
        return (usable[index].close - usable[index].reference - statistics.fmean(history)) / deviation

    def _facts(self, ctx: Context) -> dict[str, Any]:
        """판단에 쓴 수치. 판단 기록의 `detail`과 화면 설명이 같은 값을 쓴다."""
        usable = self._usable(ctx)
        current = ctx.bars[-1] if ctx.bars else None
        is_current = bool(current and usable and usable[-1].time == current.time)
        last = len(usable) - 1
        previous_ok = (
            is_current and last >= 1 and usable[-1].time - usable[-2].time == timedelta(minutes=BAR_MINUTES)
        )
        return {
            "basis": usable[-1].close - usable[-1].reference if is_current else None,
            "z": self._z(usable, last) if is_current else None,
            "previous_z": self._z(usable, last - 1) if previous_ok else None,
            "previous_time": usable[-2].time.isoformat() if previous_ok else None,
            "usable_bars": len(usable),
            "window_bars": int(self.params["window_bars"]),
            "net": ctx.net_quantity,
            "return_pct": self._return_pct(ctx),
        }

    @staticmethod
    def _return_pct(ctx: Context) -> float | None:
        if not ctx.lots or not ctx.margin or ctx.unrealized_pnl is None:
            return None
        return ctx.unrealized_pnl / ctx.margin * 100

    # ---- 진입 ----

    def _look_for_entry(self, ctx: Context, state: dict, facts: dict[str, Any]) -> StrategyOutput:
        z, before = facts["z"], facts["previous_z"]
        entry_z = float(self.params["entry_z"])
        if ctx.last_trading_day is not None and ctx.now.date() >= ctx.last_trading_day:
            return self._record(ctx, state, DecisionResult.SKIP, "최종거래일이라 신규 진입 안 함", facts)
        if z is None:
            return self._record(ctx, state, DecisionResult.SKIP, self._why_no_z(ctx, facts), facts)
        if before is None:
            return self._record(ctx, state, DecisionResult.HOLD, "같은 날 연속한 직전 봉의 z-score가 없어 진입 판단 보류", facts)
        if state.get("rearm_at") and facts["previous_time"] < state["rearm_at"]:
            return self._record(ctx, state, DecisionResult.HOLD, "청산 완료 전에 마감한 봉이 있어 재진입 보류", facts)
        if abs(before) >= entry_z:
            return self._record(ctx, state, DecisionResult.HOLD, "직전 봉이 이미 진입 기준 밖이라 돌파 아님", facts)
        if z >= entry_z:
            return self._enter(ctx, state, Side.SELL, facts)
        if z <= -entry_z:
            return self._enter(ctx, state, Side.BUY, facts)
        return self._record(ctx, state, DecisionResult.HOLD, "z-score가 진입 기준 안", facts)

    def _why_no_z(self, ctx: Context, facts: dict[str, Any]) -> str:
        if facts["basis"] is None:
            return "지수 봉이 없거나 신호 시간 밖의 봉이라 판단 보류"
        if facts["usable_bars"] <= facts["window_bars"]:
            return f"유효한 봉 {facts['usable_bars']}/{facts['window_bars'] + 1}개로 z-score 계산 불가"
        return "표준편차가 0이거나 직전 봉이 모자라 z-score 계산 불가"

    def _enter(self, ctx: Context, state: dict, side: Side, facts: dict[str, Any]) -> StrategyOutput:
        sequence = state["sequence"] + 1
        z, basis = facts["z"], facts["basis"]
        if side == Side.SELL:
            reason = f"베이시스 {basis:.2f}의 z-score {z:.2f}가 +{self.params['entry_z']} 이상 (선물 매도)"
        else:
            reason = f"베이시스 {basis:.2f}의 z-score {z:.2f}가 -{self.params['entry_z']} 이하 (선물 매수)"
        order = OrderIntent(
            side=side,
            quantity=1,
            kind=IntentKind.ENTRY,
            entry_id=f"{ctx.now.date().isoformat()}-{sequence}",
            reason=reason,
        )
        state.update(sequence=sequence, rearm_at=None)
        result = DecisionResult.SELL if side == Side.SELL else DecisionResult.BUY
        return StrategyOutput(orders=[order], decisions=[Decision(ctx.now, result, reason, score=z, detail=facts)], state=state)

    # ---- 보유와 청산 ----

    def _manage(self, ctx: Context, state: dict, facts: dict[str, Any]) -> StrategyOutput:
        rate = facts["return_pct"]
        if rate is None:
            return self._record(ctx, state, DecisionResult.SKIP, "증거금 또는 평가손익을 알 수 없어 청산 판단 보류", facts)
        limit = float(self.params["exit_return_pct"])
        if rate >= limit:
            reason = f"증거금 대비 수익률 {rate:.2f}%가 +{limit:g}% 이상 (이익 청산)"
        elif rate <= -limit:
            reason = f"증거금 대비 수익률 {rate:.2f}%가 -{limit:g}% 이하 (손절 청산)"
        else:
            return self._record(ctx, state, DecisionResult.HOLD, f"수익률 {rate:.2f}%가 청산 기준 안이라 보유", facts)

        orders = [
            OrderIntent(
                side=Side.SELL if lot.side == Side.BUY else Side.BUY,
                quantity=lot.quantity,
                kind=IntentKind.EXIT,
                entry_id=lot.entry_id,
                reason=reason,
            )
            for lot in ctx.lots
        ]
        state["rearm_at"] = ctx.now.isoformat()
        result = DecisionResult.SELL if ctx.net_quantity > 0 else DecisionResult.BUY
        return StrategyOutput(orders=orders, decisions=[Decision(ctx.now, result, reason, detail=facts)], state=state)

    # ---- 화면 설명 ----

    def describe(self, ctx: Context) -> dict[str, Any]:
        facts = self._facts(ctx)
        z = facts["z"]
        entry_z = float(self.params["entry_z"])
        if z is None:
            headline, tone = f"유효한 봉 {facts['usable_bars']}/{facts['window_bars'] + 1}개", "neutral"
        elif z >= entry_z:
            headline, tone = "진입 기준 위 (선물 매도 구간)", "sell"
        elif z <= -entry_z:
            headline, tone = "진입 기준 아래 (선물 매수 구간)", "buy"
        else:
            headline, tone = "진입 기준 안", "neutral"
        net = facts["net"]
        return {
            "sections": [
                {
                    "title": "베이시스 z-score (5분봉)",
                    "headline": headline,
                    "tone": tone,
                    "rows": [
                        ["베이시스(선물-지수)", _number(facts["basis"])],
                        ["z-score", _number(z)],
                        ["직전 봉 z-score", _number(facts["previous_z"])],
                        ["진입 기준", f"±{entry_z:g}"],
                    ],
                },
                {
                    "title": "보유",
                    "headline": "없음" if not net else ("선물 매수 보유" if net > 0 else "선물 매도 보유"),
                    "tone": "neutral" if not net else ("buy" if net > 0 else "sell"),
                    "rows": [
                        ["수량(계약)", str(abs(net))],
                        ["증거금 대비 수익률(%)", _number(facts["return_pct"])],
                        ["청산 기준(%)", f"±{float(self.params['exit_return_pct']):g}"],
                    ],
                },
            ]
        }

    # ---- 기록 ----

    def _record(self, ctx: Context, state: dict, result: DecisionResult, reason: str, facts: dict[str, Any]) -> StrategyOutput:
        return StrategyOutput(decisions=[Decision(ctx.now, result, reason, detail=facts)], state=state)


def _number(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"
