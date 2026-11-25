from dataclasses import replace
from datetime import datetime, time, timedelta
from fractions import Fraction
from math import ceil, floor
from typing import Any

from strategies.week03_zn_treasury_futures.strategy import BUY, NEUTRAL, SELL
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
        signal = self._facts(ctx, dict(ctx.state))["mid"]["signal"]
        description["sections"].insert(2, _average_section(ctx, signal))
        return description


def _average_section(ctx: Context, signal: str | None) -> dict[str, Any]:
    """당일 평단과 현재 가격의 비교. 실제 진입은 교차봉 종가로 판정하므로 참고용이다."""
    title = "평단 판단 (당일)"
    averages = {side: _entry_average(ctx, side) for side in (Side.BUY, Side.SELL)}
    price = _price(ctx.price)
    if signal not in (BUY, SELL):
        return {
            "title": title,
            "headline": "진입 안 함" if signal == NEUTRAL else "계산 불가",
            "tone": "neutral",
            "rows": [
                ["당일 매수 평단", _price(averages[Side.BUY])],
                ["당일 매도 평단", _price(averages[Side.SELL])],
                ["현재 가격", price],
            ],
        }

    label = "매수" if signal == BUY else "매도"
    average = averages[Side(signal)]
    gap, headline, condition, tone = "—", "첫 진입 전", "없음 (시장가)", "neutral"
    if average is not None:
        headline, condition = "현재 가격 대기", "—"
        if ctx.price is not None:
            difference = Fraction(str(ctx.price)) - average
            met = difference < 0 if signal == BUY else difference > 0
            gap = f"{float(difference):+.4f}"
            headline = "평단과 같음" if difference == 0 else "평단보다 낮음" if difference < 0 else "평단보다 높음"
            condition, tone = ("충족", signal) if met else ("미충족", "neutral")
    return {
        "title": title,
        "headline": headline,
        "tone": tone,
        "rows": [
            [f"당일 {label} 평단", _price(average)],
            ["현재 가격", price],
            ["평단과의 차이", gap],
            [f"추가 {label} 조건", condition],
            ["실제 판정", "교차봉 종가 기준"],
        ],
    }


def _price(value: Fraction | float | None) -> str:
    return "—" if value is None else f"{float(value):.4f}"


def _entry_average(ctx: Context, side: Side) -> Fraction | None:
    fills = [fill for fill in ctx.entry_fills if fill.side == side]
    if not fills:
        return None
    value = sum(Fraction(str(fill.price)) * fill.quantity for fill in fills)
    return value / sum(fill.quantity for fill in fills)
