from datetime import timedelta
from typing import Any

from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Context,
    Decision,
    DecisionResult,
    IntentKind,
    OrderIntent,
    Side,
    StrategyOutput,
)

BAR_MINUTES = 5
SELL_SPREAD, BUY_SPREAD = "sell", "buy"


class Strategy(BaseStrategy):
    """Z3N·ZN 스프레드 전략. 판단 규칙은 `docs/strategies/week04_z3n_zn_spread.md`를 따른다.

    - 종목은 `2 × Z3N − 1 × ZN` 스프레드 한 개이고 한 세트가 수량 1이다(승수 1,000 기준 가중치). 매도는 Z3N 1계약 매도·ZN 1계약 매수다.
    - 일봉 스프레드 `window_days`개의 분포로 진입·청산 경계를 만든다. 일봉 계열은 직전 거래일까지만 들어온다.
    - 진입: 직전 5분봉이 진입 경계 안에 있고 현재 5분봉이 경계 밖일 때 평균회귀 방향으로 낸다.
    - 청산: 현재 5분봉이 보유 방향의 청산 경계에 닿으면 전량 청산한다. 손절은 없다.
    - 재진입: 청산 판단을 한 봉이 마감된 뒤에 시작한 두 봉이 진입 조건을 충족해야 한다.
    - 하루는 한국 시간 날짜로 센다(해외영업일 근사).
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

    # ---- 밴드와 판단 수치 ----

    def _band(self, ctx: Context) -> dict[str, float] | None:
        """일봉 스프레드 분포로 만든 경계. 일봉 쌍이 모자라면 `None`."""
        window = int(self.params["window_days"])
        closes = [bar.close for bar in ctx.series.get("daily", [])][-window:]
        if len(closes) < window:
            return None
        values = sorted(closes)
        pct = float(self.params["entry_pct"])
        median = _quantile(values, 0.5)
        buffer = abs(median) * float(self.params["exit_buffer_ratio"])
        return {
            "entry_lower": _quantile(values, pct),
            "entry_upper": _quantile(values, 1 - pct),
            "median": median,
            "exit_lower": median - buffer,
            "exit_upper": median + buffer,
        }

    def _facts(self, ctx: Context) -> dict[str, Any]:
        """판단에 쓴 수치. 판단 기록의 `detail`과 화면 설명이 같은 값을 쓴다."""
        band = self._band(ctx)
        current = ctx.bars[-1] if ctx.bars else None
        previous = ctx.bars[-2] if len(ctx.bars) >= 2 else None
        consecutive = bool(
            current
            and previous
            and current.time.date() == previous.time.date()
            and current.time - previous.time == timedelta(minutes=BAR_MINUTES)
        )
        return {
            "band": band,
            "spread": current.close if current else None,
            "previous_spread": previous.close if consecutive and previous else None,
            "previous_time": previous.time.isoformat() if consecutive and previous else None,
            "daily_pairs": len(ctx.series.get("daily", [])),
            "net": ctx.net_quantity,
        }

    # ---- 진입 ----

    def _look_for_entry(self, ctx: Context, state: dict, facts: dict[str, Any]) -> StrategyOutput:
        band, spread, before = facts["band"], facts["spread"], facts["previous_spread"]
        if band is None:
            return self._record(
                ctx, state, DecisionResult.SKIP, f"일봉 스프레드 {self.params['window_days']}개가 모자라 판단 보류", facts
            )
        if before is None:
            return self._record(ctx, state, DecisionResult.HOLD, "같은 날 연속한 직전 봉이 없어 진입 판단 보류", facts)
        if state.get("rearm_at") and facts["previous_time"] < state["rearm_at"]:
            return self._record(ctx, state, DecisionResult.HOLD, "청산 완료 전에 마감한 봉이 있어 재진입 보류", facts)
        if not band["entry_lower"] <= before <= band["entry_upper"]:
            return self._record(ctx, state, DecisionResult.HOLD, "직전 봉이 진입 경계 밖이라 돌파 아님", facts)

        if spread > band["entry_upper"] and band["exit_upper"] < band["entry_upper"]:
            return self._enter(ctx, state, SELL_SPREAD, facts)
        if spread < band["entry_lower"] and band["exit_lower"] > band["entry_lower"]:
            return self._enter(ctx, state, BUY_SPREAD, facts)
        return self._record(ctx, state, DecisionResult.HOLD, "스프레드가 진입 경계 안", facts)

    def _enter(self, ctx: Context, state: dict, side: str, facts: dict[str, Any]) -> StrategyOutput:
        band, spread = facts["band"], facts["spread"]
        sequence = state["sequence"] + 1
        if side == SELL_SPREAD:
            reason = f"스프레드 {spread:.4f}가 진입 상단 {band['entry_upper']:.4f}을 넘음 (스프레드 매도)"
        else:
            reason = f"스프레드 {spread:.4f}가 진입 하단 {band['entry_lower']:.4f} 밑으로 내려감 (스프레드 매수)"
        order = OrderIntent(
            side=Side.SELL if side == SELL_SPREAD else Side.BUY,
            quantity=1,
            kind=IntentKind.ENTRY,
            entry_id=f"{ctx.now.date().isoformat()}-{sequence}",
            reason=reason,
        )
        state.update(sequence=sequence, rearm_at=None)
        result = DecisionResult.SELL if side == SELL_SPREAD else DecisionResult.BUY
        decision = Decision(ctx.now, result, reason, detail=facts)
        return StrategyOutput(orders=[order], decisions=[decision], state=state)

    # ---- 보유와 청산 ----

    def _manage(self, ctx: Context, state: dict, facts: dict[str, Any]) -> StrategyOutput:
        band, spread = facts["band"], facts["spread"]
        if band is None:
            return self._record(
                ctx, state, DecisionResult.SKIP, f"일봉 스프레드 {self.params['window_days']}개가 모자라 청산 판단 보류", facts
            )
        short_spread = ctx.net_quantity < 0
        if short_spread and spread <= band["exit_upper"]:
            reason = f"스프레드 {spread:.4f}가 청산 상단 {band['exit_upper']:.4f} 이하로 돌아옴"
        elif not short_spread and spread >= band["exit_lower"]:
            reason = f"스프레드 {spread:.4f}가 청산 하단 {band['exit_lower']:.4f} 이상으로 돌아옴"
        else:
            return self._record(ctx, state, DecisionResult.HOLD, "청산 경계에 닿지 않아 보유", facts)

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
        result = DecisionResult.BUY if short_spread else DecisionResult.SELL
        return StrategyOutput(orders=orders, decisions=[Decision(ctx.now, result, reason, detail=facts)], state=state)

    # ---- 화면 설명 ----

    def describe(self, ctx: Context) -> dict[str, Any]:
        facts = self._facts(ctx)
        band, spread = facts["band"], facts["spread"]
        if band is None:
            band_section = {
                "title": "밴드 (일봉 스프레드)",
                "headline": f"일봉 {facts['daily_pairs']}/{self.params['window_days']}개",
                "tone": "neutral",
                "rows": [["상태", "일봉 쌍이 모자라 계산 불가"]],
            }
            position = "계산 불가"
            tone = "neutral"
        else:
            band_section = {
                "title": "밴드 (일봉 스프레드)",
                "headline": f"일봉 {self.params['window_days']}개 기준",
                "tone": "neutral",
                "rows": [
                    ["진입 상단", _price(band["entry_upper"])],
                    ["청산 상단", _price(band["exit_upper"])],
                    ["중앙값", _price(band["median"])],
                    ["청산 하단", _price(band["exit_lower"])],
                    ["진입 하단", _price(band["entry_lower"])],
                ],
            }
            position, tone = _position(spread, band)
        net = facts["net"]
        return {
            "levels": self._levels(band),
            "sections": [
                band_section,
                {
                    "title": "현재 스프레드 (5분봉)",
                    "headline": position,
                    "tone": tone,
                    "rows": [
                        ["스프레드", _price(spread)],
                        ["직전 봉 스프레드", _price(facts["previous_spread"])],
                    ],
                },
                {
                    "title": "보유",
                    "headline": "없음" if not net else ("스프레드 매수 보유" if net > 0 else "스프레드 매도 보유"),
                    "tone": "neutral" if not net else ("buy" if net > 0 else "sell"),
                    "rows": [["수량(세트)", str(abs(net))]],
                },
            ]
        }

    @staticmethod
    def _levels(band: dict[str, float] | None) -> list[dict[str, Any]]:
        """차트에 수평선으로 그릴 경계. 화면은 `label`·`value`·`description`을 그대로 그린다."""
        if band is None:
            return []
        return [
            {"label": "진입 상단", "value": band["entry_upper"], "description": "5분봉 스프레드가 안에서 밖으로 넘어가면 스프레드 매도 진입"},
            {"label": "청산 상단", "value": band["exit_upper"], "description": "스프레드 매도를 보유 중 이 값 이하로 내려오면 청산"},
            {"label": "중앙값", "value": band["median"], "description": "일봉 스프레드의 중앙값. 청산 경계의 기준"},
            {"label": "청산 하단", "value": band["exit_lower"], "description": "스프레드 매수를 보유 중 이 값 이상으로 올라오면 청산"},
            {"label": "진입 하단", "value": band["entry_lower"], "description": "5분봉 스프레드가 안에서 밖으로 넘어가면 스프레드 매수 진입"},
        ]

    # ---- 기록 ----

    def _record(self, ctx: Context, state: dict, result: DecisionResult, reason: str, facts: dict[str, Any]) -> StrategyOutput:
        return StrategyOutput(decisions=[Decision(ctx.now, result, reason, detail=facts)], state=state)


def _quantile(sorted_values: list[float], fraction: float) -> float:
    """정렬한 값 사이를 선형 보간한 분위수."""
    position = fraction * (len(sorted_values) - 1)
    low = int(position)
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def _position(spread: float | None, band: dict[str, float]) -> tuple[str, str]:
    if spread is None:
        return "계산 불가", "neutral"
    if spread > band["entry_upper"]:
        return "진입 상단 위", "sell"
    if spread < band["entry_lower"]:
        return "진입 하단 아래", "buy"
    return "진입 경계 안", "neutral"


def _price(value: float | None) -> str:
    return "—" if value is None else f"{value:.4f}"
