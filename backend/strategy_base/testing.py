"""전략을 서버 없이 고정 봉 데이터로 실행해 보는 테스트 도우미."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from strategy_base.interface import BaseStrategy
from strategy_base.models import Bar, Context, Lot, OpenOrder, StrategyOutput

# (고가, 저가, 종가, 거래량)
BarRow = tuple[float, float, float, int]


def make_bars(rows: Sequence[BarRow], start: datetime, minutes: int = 3) -> list[Bar]:
    """(고가, 저가, 종가, 거래량) 목록으로 연속한 봉을 만든다."""
    return [
        Bar(start + timedelta(minutes=minutes * index), high, low, close, volume)
        for index, (high, low, close, volume) in enumerate(rows)
    ]


@dataclass(frozen=True)
class Step:
    index: int
    output: StrategyOutput


def run_on_bars(
    strategy: BaseStrategy,
    bars: Sequence[Bar],
    *,
    minutes: int = 3,
    lots: Sequence[Lot] = (),
    open_orders: Sequence[OpenOrder] = (),
    last_trading_day: date | None = None,
    state: Mapping[str, Any] | None = None,
) -> list[Step]:
    """봉이 하나씩 마감되는 것처럼 `on_bar`를 차례로 호출하고 각 호출의 출력을 돌려준다.

    체결은 흉내 내지 않는다. 포지션과 미체결 주문은 인자로 받은 값을 계속 쓰고,
    전략이 돌려준 `state`만 다음 호출로 이어 준다.
    """
    steps: list[Step] = []
    current_state: Mapping[str, Any] = state or {}
    for index in range(len(bars)):
        ctx = Context(
            now=bars[index].time + timedelta(minutes=minutes),
            bars=bars[: index + 1],
            params=strategy.params,
            last_trading_day=last_trading_day,
            lots=lots,
            open_orders=open_orders,
            state=current_state,
        )
        output = strategy.on_bar(ctx)
        if output.state is not None:
            current_state = output.state
        steps.append(Step(index, output))
    return steps
