from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.runners.service import LoadedData
from app.runners.spread import combine, pair_bars, spread_daily_fetcher, spread_loader
from strategy_base.manifest import Instrument, SpreadLeg
from strategy_base.models import Bar

KST = timezone(timedelta(hours=9))
LEGS = [SpreadLeg(code="ZFZ26", ratio=3), SpreadLeg(code="ZNZ26", ratio=-2)]
RATIOS = (3, -2)


def bar(minute: int, close: float, *, open_: float | None = None, volume: int = 10, day: int = 10) -> Bar:
    return Bar(datetime(2026, 11, day, 9, minute, tzinfo=KST), close, close, close, volume, open_)


def daily(day: int, close: float, volume: int = 10) -> Bar:
    return Bar(datetime(2026, 11, day, tzinfo=KST), close, close, close, volume, close)


def test_combine_uses_ratios_for_open_and_close():
    first = Bar(datetime(2026, 11, 10, 9, 0, tzinfo=KST), 105, 103, 104, 7, 103.5)
    second = Bar(datetime(2026, 11, 10, 9, 0, tzinfo=KST), 107, 105, 106, 5, 105.5)
    result = combine(first, second, RATIOS)
    assert result.close == 3 * 104 - 2 * 106
    assert result.open == 3 * 103.5 - 2 * 105.5
    assert result.high == max(result.open, result.close)
    assert result.low == min(result.open, result.close)
    assert result.volume == 5


def test_combine_without_open_uses_close_for_range():
    result = combine(bar(0, 104), bar(0, 106), RATIOS)
    assert result.open is None
    assert result.high == result.low == result.close == 100


def test_pair_bars_matches_same_start_time_only():
    first = [bar(0, 104), bar(5, 105), bar(10, 106)]
    second = [bar(5, 107), bar(10, 108), bar(15, 109)]
    paired = pair_bars(first, second, RATIOS)
    assert [b.time.minute for b in paired] == [5, 10]
    assert [b.close for b in paired] == [3 * 105 - 2 * 107, 3 * 106 - 2 * 108]


def test_pair_bars_drops_invalid_pairs():
    first = [bar(0, 104, volume=0), bar(5, 105), bar(10, float("nan")), bar(15, 106), bar(20, 0)]
    second = [bar(0, 107), bar(5, 107, volume=0), bar(10, 107), bar(15, 108), bar(20, 108)]
    paired = pair_bars(first, second, RATIOS)
    assert [b.time.minute for b in paired] == [15]


def test_pair_bars_daily_matches_by_date():
    first = [daily(5, 104), daily(6, 105), daily(9, 106)]
    second = [daily(6, 107), daily(9, 108), daily(10, 109)]
    paired = pair_bars(first, second, RATIOS, daily=True)
    assert [b.time.day for b in paired] == [6, 9]


def test_spread_leg_validation():
    with pytest.raises(ValidationError):
        SpreadLeg(code="ZFZ26", ratio=0)
    base = {"name": "스프레드", "market": "overseas", "exchange": "FCME", "code": "ZFZ26-ZNZ26"}
    assert Instrument(**base, legs=[{"code": "A", "ratio": 3}, {"code": "B", "ratio": -2}]).legs[1].ratio == -2
    with pytest.raises(ValidationError):
        Instrument(**base, legs=[{"code": "A", "ratio": 3}])
    with pytest.raises(ValidationError):
        Instrument(**base, legs=[{"code": "A", "ratio": 3}, {"code": "A", "ratio": -2}])
    assert Instrument(**base).legs is None


def test_spread_loader_loads_each_leg_and_pairs_by_day():
    calls = []

    def base(code, minutes, start, end, on_progress):
        calls.append((code, minutes, start, end))
        on_progress(1, 1)
        close = {"ZFZ26": 104, "ZNZ26": 106}[code]
        days = {date(2026, 11, 10): [bar(0, close), bar(5, close + 1)], date(2026, 11, 11): [bar(0, close, day=11)]}
        if code == "ZNZ26":
            days.pop(date(2026, 11, 11))
        return LoadedData(days, None)

    progress = []
    loaded = spread_loader(base, LEGS)("ZFZ26-ZNZ26", 5, date(2026, 11, 10), date(2026, 11, 11), lambda d, t: progress.append((d, t)))
    assert [call[0] for call in calls] == ["ZFZ26", "ZNZ26"]
    assert list(loaded.days) == [date(2026, 11, 10)]
    assert [b.close for b in loaded.days[date(2026, 11, 10)]] == [3 * 104 - 2 * 106, 3 * 105 - 2 * 107]
    assert progress[-1] == (2, 2)


def test_spread_daily_fetcher_pairs_legs_and_passes_plain_instruments_through():
    seen = []

    def base(instrument, quantity):
        seen.append(instrument.code)
        close = {"ZFZ26": 104, "ZNZ26": 106}.get(instrument.code, 1)
        return [daily(d, close + d) for d in (5, 6, 9)]

    fetch = spread_daily_fetcher(base)
    spread = Instrument(name="스프레드", market="overseas", exchange="FCME", code="ZFZ26-ZNZ26", legs=LEGS)
    bars = fetch(spread, 2)
    assert seen == ["ZFZ26", "ZNZ26"]
    assert [b.time.day for b in bars] == [6, 9]
    assert bars[-1].close == 3 * (104 + 9) - 2 * (106 + 9)

    plain = Instrument(name="ZN", market="overseas", exchange="FCME", code="ZNZ26")
    assert len(fetch(plain, 3)) == 3
    assert seen[-1] == "ZNZ26"
