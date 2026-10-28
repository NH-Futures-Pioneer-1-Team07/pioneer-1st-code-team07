from datetime import datetime

from strategy_base.indicators import SwingKind, average_volume, confirmed_swings, latest_swings
from strategy_base.testing import make_bars

START = datetime(2026, 10, 27, 9, 0)


def bars_of(*rows):
    return make_bars(rows, START)


def flat(high, low, close=None, volume=100):
    return (high, low, close if close is not None else low, volume)


def test_고점은_뒤쪽_봉이_완성돼야_확정된다():
    # 인덱스 2가 고점 후보 (앞 2개 이하, 뒤 2개 미만)
    rows = [flat(10, 1), flat(11, 1), flat(15, 1), flat(12, 1), flat(11, 1)]

    assert confirmed_swings(bars_of(*rows[:4])) == []
    swings = confirmed_swings(bars_of(*rows))
    assert [(s.kind, s.index, s.confirmed_index, s.price) for s in swings] == [
        (SwingKind.HIGH, 2, 4, 15)
    ]


def test_고점은_앞쪽_봉과_같아도_뒤쪽_봉과_같으면_아니다():
    앞과_같음 = [flat(15, 1), flat(15, 1), flat(15, 1), flat(12, 1), flat(11, 1)]
    뒤와_같음 = [flat(10, 1), flat(11, 1), flat(15, 1), flat(15, 1), flat(11, 1)]

    assert [s.kind for s in confirmed_swings(bars_of(*앞과_같음))] == [SwingKind.HIGH]
    assert confirmed_swings(bars_of(*뒤와_같음)) == []


def test_저점은_앞쪽_봉과_같아도_뒤쪽_봉과_같으면_아니다():
    앞과_같음 = [flat(50, 5), flat(50, 5), flat(50, 5), flat(50, 8), flat(50, 9)]
    뒤와_같음 = [flat(50, 9), flat(50, 8), flat(50, 5), flat(50, 5), flat(50, 9)]

    assert [s.kind for s in confirmed_swings(bars_of(*앞과_같음))] == [SwingKind.LOW]
    assert confirmed_swings(bars_of(*뒤와_같음)) == []


def test_저점을_확정한다():
    rows = [flat(50, 9), flat(50, 8), flat(50, 5), flat(50, 7), flat(50, 8)]

    swings = confirmed_swings(bars_of(*rows))

    assert [(s.kind, s.index, s.price) for s in swings] == [(SwingKind.LOW, 2, 5)]


def test_마지막_봉을_빼면_그_봉으로_확정되는_고점은_빠진다():
    rows = [flat(10, 1), flat(11, 1), flat(15, 1), flat(12, 1), flat(11, 1)]
    bars = bars_of(*rows)

    assert len(confirmed_swings(bars)) == 1
    assert confirmed_swings(bars[:-1]) == []


def test_가장_최근_확정값을_종류별로_고른다():
    rows = [
        flat(10, 1), flat(11, 1), flat(15, 1), flat(12, 1), flat(11, 1),
        flat(12, 1), flat(20, 1), flat(13, 1), flat(12, 1),
    ]
    swings = confirmed_swings(bars_of(*rows))

    highs = latest_swings(swings, SwingKind.HIGH, 2)
    assert [s.price for s in highs] == [15, 20]
    assert latest_swings(swings, SwingKind.HIGH, 5) == highs


def test_평균_거래량은_마지막_n개의_평균이다():
    bars = bars_of(*[flat(2, 1, volume=v) for v in (100, 200, 300, 400)])

    assert average_volume(bars, 2) == 350
    assert average_volume(bars[:-1], 3) == 200


def test_평균_거래량은_봉이_모자라면_없다():
    bars = bars_of(*[flat(2, 1, volume=100)] * 3)

    assert average_volume(bars, 4) is None
    assert average_volume(bars, 0) is None
