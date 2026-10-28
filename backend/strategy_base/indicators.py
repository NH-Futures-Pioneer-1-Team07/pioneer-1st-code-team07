"""전략이 함께 쓰는 지표 함수. 모두 입력만 보고 결과를 돌려주는 순수 함수다."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from strategy_base.models import Bar


class SwingKind(StrEnum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True)
class Swing:
    """확정된 고점 또는 저점.

    - `index`: 후보 봉(가운데 봉)의 위치.
    - `confirmed_index`: 뒤쪽 봉이 모두 완성돼 확정된 시점의 봉 위치(`index + side_bars`).
    """

    kind: SwingKind
    index: int
    confirmed_index: int
    price: float


def confirmed_swings(bars: Sequence[Bar], side_bars: int = 2) -> list[Swing]:
    """주어진 봉만 보고 확정된 고점·저점을 시간순으로 돌려준다.

    가운데 봉 앞뒤로 `side_bars`개씩, 연속한 `2 × side_bars + 1`개 봉을 본다.
    - 고점: 고가가 앞쪽 봉의 각 고가 이상이고 뒤쪽 봉의 각 고가보다 높다.
    - 저점: 저가가 앞쪽 봉의 각 저가 이하이고 뒤쪽 봉의 각 저가보다 낮다.
    뒤쪽 봉이 모두 있어야 확정되므로, 마지막 `side_bars`개 봉은 후보가 되지 못한다.
    "신호 봉이 시작되기 전에 확정된" 값이 필요하면 신호 봉을 뺀 `bars[:-1]`을 넘긴다.
    """
    swings: list[Swing] = []
    for index in range(side_bars, len(bars) - side_bars):
        before = bars[index - side_bars : index]
        after = bars[index + 1 : index + 1 + side_bars]
        center = bars[index]
        confirmed = index + side_bars
        if all(center.high >= bar.high for bar in before) and all(center.high > bar.high for bar in after):
            swings.append(Swing(SwingKind.HIGH, index, confirmed, center.high))
        if all(center.low <= bar.low for bar in before) and all(center.low < bar.low for bar in after):
            swings.append(Swing(SwingKind.LOW, index, confirmed, center.low))
    return swings


def latest_swings(swings: Sequence[Swing], kind: SwingKind, count: int = 1) -> list[Swing]:
    """주어진 종류의 가장 최근 확정 `count`개를 오래된 것부터 돌려준다. 모자라면 있는 만큼만 돌려준다."""
    return [swing for swing in swings if swing.kind == kind][-count:]


def average_volume(bars: Sequence[Bar], count: int) -> float | None:
    """마지막 `count`개 봉 거래량의 평균. 봉이 `count`개보다 적으면 `None`.

    판단 대상 봉을 평균에서 빼야 하면 판단 대상 봉을 뺀 `bars[:-1]`을 넘긴다.
    """
    if count <= 0 or len(bars) < count:
        return None
    return sum(bar.volume for bar in bars[-count:]) / count
