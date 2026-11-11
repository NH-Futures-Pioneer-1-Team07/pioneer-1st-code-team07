"""두 종목의 봉을 짝지어 스프레드 봉으로 합성한다.

스프레드 종목은 `sum(비율 × 종목 가격)`을 가격으로 갖고 한 세트를 수량 1로 거래한다.
전략은 합성된 봉을 일반 종목의 봉처럼 받는다.
"""

import math
from collections.abc import Callable, Sequence
from datetime import date

from app.runners.series import DailyFetcher
from strategy_base.manifest import Instrument, SpreadLeg
from strategy_base.models import Bar


def is_valid(bar: Bar) -> bool:
    """종가가 양의 유한한 수이고 거래량이 0보다 큰 봉."""
    return math.isfinite(bar.close) and bar.close > 0 and bar.volume > 0


def combine(first: Bar, second: Bar, ratios: tuple[float, float]) -> Bar:
    """같은 시각의 두 봉을 한 스프레드 봉으로 합친다.

    시가·종가는 비율대로 합치고, 고가·저가는 두 종목이 동시에 그 값을 찍었는지 알 수 없어서
    합친 시가와 종가의 최댓값·최솟값으로 둔다. 거래량은 두 종목 중 작은 값이다.
    """
    one, two = ratios
    close = one * first.close + two * second.close
    open_ = one * first.open + two * second.open if first.open is not None and second.open is not None else None
    reference = close if open_ is None else open_
    return Bar(
        time=first.time,
        high=max(reference, close),
        low=min(reference, close),
        close=close,
        volume=min(first.volume, second.volume),
        open=open_,
    )


def pair_bars(first: Sequence[Bar], second: Sequence[Bar], ratios: tuple[float, float], *, daily: bool = False) -> list[Bar]:
    """같은 시각의 유효한 봉끼리 짝지어 스프레드 봉을 오래된 순서로 돌려준다.

    5분봉은 봉 시작 시각이 같은 쌍, 일봉(`daily=True`)은 기준일이 같은 쌍만 짝짓는다.
    """
    key: Callable[[Bar], object] = (lambda bar: bar.time.date()) if daily else (lambda bar: bar.time)
    others = {key(bar): bar for bar in second if is_valid(bar)}
    paired = []
    for bar in first:
        other = others.get(key(bar))
        if other is not None and is_valid(bar):
            paired.append(combine(bar, other, ratios))
    paired.sort(key=lambda bar: bar.time)
    return paired


def _notional(first: Sequence[Bar], second: Sequence[Bar], ratios: tuple[float, float]) -> list[float]:
    """같은 시각 유효한 쌍의 두 종목 종가 × |가중치|의 합. 수수료 계산 가격으로 쓴다."""
    others = {bar.time: bar for bar in second if is_valid(bar)}
    return [
        abs(ratios[0]) * bar.close + abs(ratios[1]) * others[bar.time].close
        for bar in first
        if is_valid(bar) and bar.time in others
    ]


def _ratios(legs: Sequence[SpreadLeg]) -> tuple[float, float]:
    """스프레드 가격에 곱하는 가중치 두 개(`weight`가 없으면 `ratio`)."""
    return legs[0].price_weight, legs[1].price_weight


def spread_loader(base, legs: Sequence[SpreadLeg]):
    """종목 하나의 분봉 로더를 감싸 두 종목을 각각 받아 스프레드 분봉으로 합치는 로더를 만든다.

    합성 로더는 코드 인자를 쓰지 않고 `legs`의 종목코드로 `base`를 부른다. 진행률은 두 호출을 합쳐 알린다.
    """
    from app.runners.service import LoadedData

    def load(code: str, minutes: int, start: date, end: date, on_progress: Callable[[int, int], None]) -> LoadedData:
        loaded = []
        for index, leg in enumerate(legs):
            loaded.append(
                base(leg.code, minutes, start, end, lambda done, total, index=index: on_progress(index * total + done, 2 * total))
            )
        first, second = loaded
        days: dict[date, list[Bar]] = {}
        notional: list[float] = []
        for day in sorted(set(first.days) & set(second.days)):
            bars = pair_bars(first.days[day], second.days[day], _ratios(legs))
            if bars:
                days[day] = bars
                notional.extend(_notional(first.days[day], second.days[day], _ratios(legs)))
        return LoadedData(days, None, sum(notional) / len(notional) if notional else None)

    return load


def spread_daily_fetcher(base: DailyFetcher) -> DailyFetcher:
    """종목 하나의 일봉 조회를 감싼다. `legs`가 있는 종목이면 두 종목의 일봉을 짝지어 돌려주고, 아니면 그대로 조회한다."""

    def fetch(instrument: Instrument, quantity: int) -> list[Bar]:
        if not instrument.legs:
            return base(instrument, quantity)
        bars = [
            base(instrument.model_copy(update={"code": leg.code, "legs": None}), quantity) for leg in instrument.legs
        ]
        return pair_bars(bars[0], bars[1], _ratios(instrument.legs), daily=True)[-quantity:]

    return fetch


def loader_for(instrument: Instrument, base):
    """`legs`가 있는 종목이면 스프레드 로더로 감싸고, 아니면 그대로 돌려준다."""
    return spread_loader(base, instrument.legs) if instrument.legs else base


class SpreadProbe:
    """두 종목의 날짜별 분봉 수를 합쳐 백테스트 가능 기간을 찾는 데 쓴다. 두 종목 중 적은 쪽을 그날의 봉 수로 본다."""

    def __init__(self, probes: Sequence):
        self._probes = probes

    def bars_on(self, day: date) -> int:
        return min(probe.bars_on(day) for probe in self._probes)

    def last_trading_day(self) -> date | None:
        days = [probe.last_trading_day() for probe in self._probes]
        return min((day for day in days if day), default=None)
