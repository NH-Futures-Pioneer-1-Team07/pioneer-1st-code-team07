from dataclasses import replace
from datetime import datetime, time, timedelta
from fractions import Fraction
from math import ceil, floor
from typing import Any

from strategies.week03_zn_treasury_futures.strategy import Strategy as Week03Strategy
from strategy_base.models import Context, IntentKind, OrderType, Side, StrategyOutput

BAR_DURATION = timedelta(minutes=5)


class Strategy(Week03Strategy):
    """3주차 진입 신호에 당일 체결 평단 조건을 적용한다."""

    def _enter(self, ctx: Context, state: dict, side: str, facts: dict[str, Any]) -> StrategyOutput:
        entry_side = Side(side)
        average = _entry_average(ctx, entry_side)
        facts["today"]["entry_average"] = float(average) if average is not None else None

        # 첫 주문의 체결 여부가 확인되기 전에 또 시장가로 진입하지 않는다.
        if any(order.kind == IntentKind.ENTRY for order in ctx.open_orders):
            return self._skip(ctx, state, "미체결 신규 진입 주문이 있어 체결을 기다림", facts)
        if average is None:
            return super()._enter(ctx, state, side, facts)

        close = Fraction(str(facts["intraday"]["close"]))
        buy = entry_side == Side.BUY
        if (buy and close >= average) or (not buy and close <= average):
            return self._skip(ctx, state, "교차봉 종가가 당일 진입 평단보다 유리하지 않음", facts)
        if ctx.bars[-1].time.date() != ctx.now.date():
            return self._skip(ctx, state, "교차봉과 주문 시점의 날짜가 달라 추가 진입하지 않음", facts)
        if ctx.tick_size is None:
            return self._skip(ctx, state, "호가 단위를 알 수 없어 추가 진입하지 않음", facts)

        tick = Fraction(str(ctx.tick_size))
        average_in_ticks = average / tick
        limit_ticks = ceil(average_in_ticks) - 1 if buy else floor(average_in_ticks) + 1
        limit_price = float(limit_ticks * tick)
        facts["today"]["entry_limit_price"] = limit_price
        output = super()._enter(ctx, state, side, facts)
        if not output.orders:
            return output

        midnight = datetime.combine(ctx.now.date() + timedelta(days=1), time.min, tzinfo=ctx.now.tzinfo)
        order = replace(
            output.orders[0],
            order_type=OrderType.LIMIT,
            limit_price=limit_price,
            valid_bars=1,
            expires_at=min(ctx.now + BAR_DURATION, midnight),
        )
        return replace(output, orders=[order])

    def describe(self, ctx: Context) -> dict[str, Any]:
        description = super().describe(ctx)
        rows = description["sections"][-1]["rows"]
        for side, label in ((Side.BUY, "당일 매수 평단"), (Side.SELL, "당일 매도 평단")):
            average = _entry_average(ctx, side)
            rows.append([label, "—" if average is None else f"{average:.6f}"])
        return description


def _entry_average(ctx: Context, side: Side) -> Fraction | None:
    fills = [fill for fill in ctx.entry_fills if fill.side == side]
    if not fills:
        return None
    value = sum(Fraction(str(fill.price)) * fill.quantity for fill in fills)
    return value / sum(fill.quantity for fill in fills)
