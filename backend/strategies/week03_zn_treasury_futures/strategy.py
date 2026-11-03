from bisect import bisect_right
from typing import Any

from strategy_base.indicators import simple_moving_average
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

BUY, SELL, NEUTRAL = "buy", "sell", "neutral"
MID_LABELS = {BUY: "매수 허용", SELL: "매도 허용", NEUTRAL: "중립", None: "계산 불가"}
TONES = {BUY: "buy", SELL: "sell", NEUTRAL: "neutral", None: "neutral"}


class Strategy(BaseStrategy):
    """ZN 이동평균 전략. 판단 규칙은 `docs/strategies/week03_zn_treasury_futures.md`를 따른다.

    - 중기 신호: 직전 거래일 종가와 일봉 이동평균 두 개로 그날 허용하는 방향을 정한다.
    - 진입: 장중 5분봉의 단기선이 장기선을 교차한 봉이 마감되면 시장가 1계약을 낸다.
    - 청산: 중기 신호가 보유와 반대 방향을 허용하거나 증거금 대비 손익이 기준에 이르면 전량 청산한다.
    - 하루(한국 시간 날짜) 안에 낸 신규 진입 수량은 `state`에 기록하고 청산해도 되돌리지 않는다.
    - 매 판단 기록의 `detail`에 중기·장중 판단 수치를 담고, 판단 문구와 주문 사유에 같은 요약을 붙인다.
    """

    def on_bar(self, ctx: Context) -> StrategyOutput:
        day = ctx.now.date().isoformat()
        state = dict(ctx.state)
        if state.get("day") != day:
            state.update(day=day, entered_today=0, sequence=state.get("sequence", 0))

        facts = self._facts(ctx, state)
        signal, cross = facts["mid"]["signal"], facts["intraday"]["cross"]
        summary = self._summary(facts)

        exit_reason = self._exit_reason(ctx, facts)
        if exit_reason:
            return self._exit_all(ctx, state, f"{exit_reason} ({summary})", facts)

        if signal == NEUTRAL or signal is None:
            return self._hold(ctx, state, "중기 신호가 중립이거나 계산할 수 없어 신규 진입하지 않음", facts)
        if cross is None:
            return self._hold(ctx, state, "장중 이동평균 교차 없음", facts)
        if cross != signal:
            return self._hold(ctx, state, "장중 교차 방향이 허용 방향과 달라 진입하지 않음", facts)
        return self._enter(ctx, state, signal, facts)

    # ---- 판단 수치 ----

    def _facts(self, ctx: Context, state: dict) -> dict[str, Any]:
        """판단에 쓴 수치. 판단 기록의 `detail`과 화면 설명이 같은 값을 쓴다."""
        daily = ctx.series.get("daily", [])
        mid_short = simple_moving_average(daily, self.params["mid_short_days"])
        mid_long = simple_moving_average(daily, self.params["mid_long_days"])
        close = daily[-1].close if daily else None
        signal = None
        if mid_short is not None and mid_long is not None and close is not None:
            signal = BUY if close > mid_short > mid_long else SELL if close < mid_short and close < mid_long else NEUTRAL

        short_bars, long_bars = self.params["short_bars"], self.params["long_bars"]
        short = simple_moving_average(ctx.bars, short_bars)
        long = simple_moving_average(ctx.bars, long_bars)
        before_short = simple_moving_average(ctx.bars[:-1], short_bars)
        before_long = simple_moving_average(ctx.bars[:-1], long_bars)
        bar_close = ctx.bars[-1].close if ctx.bars else None
        cross = None
        if None not in (short, long, before_short, before_long, bar_close):
            if before_short <= before_long and short > long and bar_close > short and bar_close > long:
                cross = BUY
            elif before_short >= before_long and short < long and bar_close < short and bar_close < long:
                cross = SELL
        position = None
        if short is not None and long is not None:
            position = "above" if short > long else "below" if short < long else "equal"

        day = ctx.now.date().isoformat()
        entered = state.get("entered_today", 0) if state.get("day") == day else 0
        holding = sum(lot.quantity for lot in ctx.lots)
        pnl_ratio = None
        if ctx.margin and ctx.unrealized_pnl is not None and holding:
            pnl_ratio = ctx.unrealized_pnl / (ctx.margin * holding)
        return {
            "mid": {"signal": signal, "close": close, "short_ma": mid_short, "long_ma": mid_long},
            "intraday": {"cross": cross, "position": position, "short_ma": short, "long_ma": long, "close": bar_close},
            "today": {
                "vix": ctx.vix,
                "entered": entered,
                "limit": self._daily_limit(ctx.vix, signal) if signal in (BUY, SELL) else None,
                "holding": holding,
                "net": ctx.net_quantity,
                "pnl_ratio": pnl_ratio,
                "profit_loss_rate": self.params["profit_loss_rate"],
            },
        }

    def _summary(self, facts: dict[str, Any]) -> str:
        mid, intraday = facts["mid"], facts["intraday"]
        return f"중기 {MID_LABELS[mid['signal']]} · 장중 {self._intraday_label(intraday)}"

    @staticmethod
    def _intraday_label(intraday: dict[str, Any]) -> str:
        if intraday["cross"] == BUY:
            return "단기선 상향 교차"
        if intraday["cross"] == SELL:
            return "단기선 하향 교차"
        return {"above": "단기선이 장기선 위", "below": "단기선이 장기선 아래", "equal": "단기선과 장기선이 같음"}.get(
            intraday["position"], "계산 불가"
        )

    # ---- 화면 설명 ----

    def describe(self, ctx: Context) -> dict[str, Any]:
        facts = self._facts(ctx, dict(ctx.state))
        mid, intraday, today = facts["mid"], facts["intraday"], facts["today"]
        rate = today["profit_loss_rate"]
        position = (
            f"{'매수' if today['net'] > 0 else '매도'} {today['holding']}계약" if today["holding"] else "없음"
        )
        return {
            "sections": [
                {
                    "title": "중기 판단 (일봉)",
                    "headline": MID_LABELS[mid["signal"]],
                    "tone": TONES[mid["signal"]],
                    "rows": [
                        ["직전 거래일 종가", _price(mid["close"])],
                        [f"{self.params['mid_short_days']}일선", _price(mid["short_ma"])],
                        [f"{self.params['mid_long_days']}일선", _price(mid["long_ma"])],
                    ],
                },
                {
                    "title": "장중 판단 (5분봉)",
                    "headline": self._intraday_label(intraday),
                    "tone": {BUY: "buy", SELL: "sell"}.get(intraday["cross"]) or {"above": "buy", "below": "sell"}.get(intraday["position"], "neutral"),
                    "rows": [
                        [f"단기선({self.params['short_bars']}봉)", _price(intraday["short_ma"])],
                        [f"장기선({self.params['long_bars']}봉)", _price(intraday["long_ma"])],
                        ["마지막 봉 종가", _price(intraday["close"])],
                        ["진입 신호", {BUY: "매수 교차", SELL: "매도 교차"}.get(intraday["cross"], "없음")],
                    ],
                },
                {
                    "title": "오늘 진입·보유",
                    "headline": f"신규 진입 {today['entered']}/{today['limit'] if today['limit'] is not None else '—'}계약",
                    "tone": "neutral",
                    "rows": [
                        ["VIX(직전 거래일 종가)", _price(today["vix"], 2)],
                        ["보유", position],
                        [
                            "증거금 대비 손익",
                            "—" if today["pnl_ratio"] is None else f"{today['pnl_ratio']:+.1%} (기준 ±{rate:.0%})",
                        ],
                    ],
                },
            ]
        }

    # ---- 청산 ----

    def _exit_reason(self, ctx: Context, facts: dict[str, Any]) -> str | None:
        net, signal = ctx.net_quantity, facts["mid"]["signal"]
        if net == 0:
            return None
        if (net > 0 and signal == SELL) or (net < 0 and signal == BUY):
            return "중기 신호가 보유와 반대 방향을 허용"
        ratio, rate = facts["today"]["pnl_ratio"], self.params["profit_loss_rate"]
        if ratio is not None:
            if ratio >= rate:
                return f"증거금 대비 평가손익 {ratio:.1%}가 익절 기준 {rate:.0%}에 도달"
            if ratio <= -rate:
                return f"증거금 대비 평가손익 {ratio:.1%}가 손절 기준 -{rate:.0%}에 도달"
        return None

    def _exit_all(self, ctx: Context, state: dict, reason: str, facts: dict[str, Any]) -> StrategyOutput:
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
        result = DecisionResult.SELL if ctx.net_quantity > 0 else DecisionResult.BUY
        return StrategyOutput(orders=orders, decisions=[Decision(ctx.now, result, reason, detail=facts)], state=state)

    # ---- 진입 ----

    def _enter(self, ctx: Context, state: dict, side: str, facts: dict[str, Any]) -> StrategyOutput:
        limit = facts["today"]["limit"]
        if limit is None:
            return self._skip(ctx, state, "VIX를 알 수 없어 신규 진입하지 않음", facts)

        quantity = self.params["entry_quantity"]
        holding = facts["today"]["holding"] + sum(
            order.quantity - order.filled_quantity for order in ctx.open_orders if order.kind == IntentKind.ENTRY
        )
        if state["entered_today"] + quantity > limit:
            return self._skip(ctx, state, f"하루 신규 진입 한도 {limit}계약을 모두 사용", facts)
        if holding + quantity > self.params["max_position"]:
            return self._skip(ctx, state, f"전체 보유 한도 {self.params['max_position']}계약에 도달", facts)

        sequence = state["sequence"] + 1
        reason = f"장중 이동평균 교차 ({self._summary(facts)})"
        order = OrderIntent(
            side=Side.BUY if side == BUY else Side.SELL,
            quantity=quantity,
            kind=IntentKind.ENTRY,
            entry_id=f"{state['day']}-{sequence}",
            reason=reason,
        )
        state.update(sequence=sequence, entered_today=state["entered_today"] + quantity)
        facts["today"] = {**facts["today"], "entered": state["entered_today"], "holding": holding}
        decision = Decision(ctx.now, DecisionResult.BUY if side == BUY else DecisionResult.SELL, reason, detail=facts)
        return StrategyOutput(orders=[order], decisions=[decision], state=state)

    def _daily_limit(self, vix: float | None, side: str) -> int | None:
        if vix is None:
            return None
        index = bisect_right(self.params["vix_thresholds"], vix)
        table = self.params["daily_limit_buy"] if side == BUY else self.params["daily_limit_sell"]
        return table[min(index, len(table) - 1)]

    # ---- 기록 ----

    def _hold(self, ctx: Context, state: dict, reason: str, facts: dict[str, Any]) -> StrategyOutput:
        return StrategyOutput(
            decisions=[Decision(ctx.now, DecisionResult.HOLD, f"{reason} ({self._summary(facts)})", detail=facts)],
            state=state,
        )

    def _skip(self, ctx: Context, state: dict, reason: str, facts: dict[str, Any]) -> StrategyOutput:
        return StrategyOutput(
            decisions=[Decision(ctx.now, DecisionResult.SKIP, f"{reason} ({self._summary(facts)})", detail=facts)],
            state=state,
        )


def _price(value: float | None, digits: int = 4) -> str:
    return "—" if value is None else f"{value:.{digits}f}"
