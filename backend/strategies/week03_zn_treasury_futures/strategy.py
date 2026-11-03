from bisect import bisect_right

from strategy_base.indicators import simple_moving_average
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

BUY, SELL, NEUTRAL = "buy", "sell", "neutral"


class Strategy(BaseStrategy):
    """ZN 이동평균 전략. 판단 규칙은 `docs/strategies/week03_zn_treasury_futures.md`를 따른다.

    - 중기 신호: 직전 거래일 종가와 일봉 이동평균 두 개로 그날 허용하는 방향을 정한다.
    - 진입: 장중 5분봉의 단기선이 장기선을 교차한 봉이 마감되면 시장가 1계약을 낸다.
    - 청산: 중기 신호가 보유와 반대 방향을 허용하거나 증거금 대비 손익이 기준에 이르면 전량 청산한다.
    - 하루(한국 시간 날짜) 안에 낸 신규 진입 수량은 `state`에 기록하고 청산해도 되돌리지 않는다.
    """

    def on_bar(self, ctx: Context) -> StrategyOutput:
        day = ctx.now.date().isoformat()
        state = dict(ctx.state)
        if state.get("day") != day:
            state.update(day=day, entered_today=0, sequence=state.get("sequence", 0))

        signal = self._mid_signal(ctx)
        net = ctx.net_quantity

        exit_reason = self._exit_reason(ctx, signal, net)
        if exit_reason:
            return self._exit_all(ctx, state, exit_reason, signal)

        if signal == NEUTRAL or signal is None:
            return self._hold(ctx, state, "중기 신호가 중립이거나 계산할 수 없어 신규 진입하지 않음", signal)

        cross = self._cross(ctx)
        if cross is None:
            return self._hold(ctx, state, "장중 이동평균 교차 없음", signal)
        if cross != signal:
            return self._hold(ctx, state, "장중 교차 방향이 허용 방향과 달라 진입하지 않음", signal, cross=cross)
        return self._enter(ctx, state, signal)

    # ---- 중기 신호 ----

    def _mid_signal(self, ctx: Context) -> str | None:
        daily = ctx.series.get("daily", [])
        short_days, long_days = self.params["mid_short_days"], self.params["mid_long_days"]
        short = simple_moving_average(daily, short_days)
        long = simple_moving_average(daily, long_days)
        if short is None or long is None:
            return None
        close = daily[-1].close
        if close > short > long:
            return BUY
        if close < short and close < long:
            return SELL
        return NEUTRAL

    # ---- 장중 교차 ----

    def _cross(self, ctx: Context) -> str | None:
        """방금 마감된 봉에서 단기선이 장기선을 교차했고 그 봉의 종가가 두 선 모두 바깥에 있으면 방향을 돌려준다."""
        short_bars, long_bars = self.params["short_bars"], self.params["long_bars"]
        now_short = simple_moving_average(ctx.bars, short_bars)
        now_long = simple_moving_average(ctx.bars, long_bars)
        before_short = simple_moving_average(ctx.bars[:-1], short_bars)
        before_long = simple_moving_average(ctx.bars[:-1], long_bars)
        if None in (now_short, now_long, before_short, before_long):
            return None
        close = ctx.bars[-1].close
        if before_short <= before_long and now_short > now_long and close > now_short and close > now_long:
            return BUY
        if before_short >= before_long and now_short < now_long and close < now_short and close < now_long:
            return SELL
        return None

    # ---- 청산 ----

    def _exit_reason(self, ctx: Context, signal: str | None, net: int) -> str | None:
        if net == 0:
            return None
        if (net > 0 and signal == SELL) or (net < 0 and signal == BUY):
            return "중기 신호가 보유와 반대 방향을 허용"
        rate = self.params["profit_loss_rate"]
        quantity = sum(lot.quantity for lot in ctx.lots)
        if ctx.margin and ctx.unrealized_pnl is not None and quantity:
            ratio = ctx.unrealized_pnl / (ctx.margin * quantity)
            if ratio >= rate:
                return f"증거금 대비 평가손익 {ratio:.1%}가 익절 기준 {rate:.0%}에 도달"
            if ratio <= -rate:
                return f"증거금 대비 평가손익 {ratio:.1%}가 손절 기준 -{rate:.0%}에 도달"
        return None

    def _exit_all(self, ctx: Context, state: dict, reason: str, signal: str | None) -> StrategyOutput:
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
        decision = Decision(ctx.now, result, reason, detail={"mid_signal": signal, "net": ctx.net_quantity})
        return StrategyOutput(orders=orders, decisions=[decision], state=state)

    # ---- 진입 ----

    def _enter(self, ctx: Context, state: dict, side: str) -> StrategyOutput:
        limit = self._daily_limit(ctx.vix, side)
        if limit is None:
            return self._skip(ctx, state, "VIX를 알 수 없어 신규 진입하지 않음", side)

        quantity = self.params["entry_quantity"]
        holding = sum(lot.quantity for lot in ctx.lots) + sum(
            order.quantity - order.filled_quantity for order in ctx.open_orders if order.kind == IntentKind.ENTRY
        )
        if state["entered_today"] + quantity > limit:
            return self._skip(ctx, state, f"하루 신규 진입 한도 {limit}계약을 모두 사용", side, limit=limit)
        if holding + quantity > self.params["max_position"]:
            return self._skip(ctx, state, f"전체 보유 한도 {self.params['max_position']}계약에 도달", side, holding=holding)

        sequence = state["sequence"] + 1
        order = OrderIntent(
            side=Side.BUY if side == BUY else Side.SELL,
            quantity=quantity,
            kind=IntentKind.ENTRY,
            entry_id=f"{state['day']}-{sequence}",
            reason="장중 이동평균 교차",
        )
        state.update(sequence=sequence, entered_today=state["entered_today"] + quantity)
        decision = Decision(
            ctx.now,
            DecisionResult.BUY if side == BUY else DecisionResult.SELL,
            order.reason,
            detail={"vix": ctx.vix, "daily_limit": limit, "entered_today": state["entered_today"], "holding": holding},
        )
        return StrategyOutput(orders=[order], decisions=[decision], state=state)

    def _daily_limit(self, vix: float | None, side: str) -> int | None:
        if vix is None:
            return None
        index = bisect_right(self.params["vix_thresholds"], vix)
        table = self.params["daily_limit_buy"] if side == BUY else self.params["daily_limit_sell"]
        return table[min(index, len(table) - 1)]

    # ---- 기록 ----

    def _hold(self, ctx: Context, state: dict, reason: str, signal: str | None, **detail) -> StrategyOutput:
        decision = Decision(ctx.now, DecisionResult.HOLD, reason, detail={"mid_signal": signal, **detail})
        return StrategyOutput(decisions=[decision], state=state)

    def _skip(self, ctx: Context, state: dict, reason: str, side: str, **detail) -> StrategyOutput:
        decision = Decision(ctx.now, DecisionResult.SKIP, reason, detail={"side": side, **detail})
        return StrategyOutput(decisions=[decision], state=state)
