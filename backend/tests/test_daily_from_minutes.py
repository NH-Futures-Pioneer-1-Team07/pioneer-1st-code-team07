"""분봉으로 일봉을 합성한다(NH가 일봉을 주지 않는 해외 종목용)."""

from datetime import datetime, timedelta, timezone

from app.runners.series import daily_from_minutes
from app.runners.spread import spread_daily_fetcher
from strategy_base.manifest import Instrument, SpreadLeg
from strategy_base.models import Bar

KST = timezone(timedelta(hours=9))


def minute(day: int, hour: int, mi: int, close: float, *, high=None, low=None, open_=None, volume=10) -> Bar:
    return Bar(datetime(2026, 11, day, hour, mi, tzinfo=KST), high or close, low or close, close, volume, open_ if open_ is not None else close)


def test_영업일은_한국시간에서_7시간을_뺀_날짜로_나눈다():
    bars = [
        minute(9, 23, 55, 100.0),  # 11-09 영업일의 늦은 봉
        minute(10, 0, 0, 101.0),  # 자정을 넘어도 11-09 영업일
        minute(10, 6, 55, 102.0),  # 휴장 직전 마지막 봉: 11-09 영업일
        minute(10, 8, 0, 103.0),  # 새 세션 첫 봉: 11-10 영업일
        minute(10, 23, 55, 104.0),
    ]
    days = daily_from_minutes(bars)
    assert [bar.time.date().day for bar in days] == [9, 10]
    assert [bar.close for bar in days] == [102.0, 104.0]


def test_일봉은_첫_시가_마지막_종가_고저와_거래량_합이다():
    bars = [
        minute(10, 9, 0, 100.0, high=101.0, low=99.5, open_=100.0, volume=3),
        minute(10, 9, 5, 100.5, high=102.0, low=100.0, open_=100.0, volume=4),
        minute(10, 9, 10, 100.2, high=100.6, low=98.0, open_=100.5, volume=5),
    ]
    (day,) = daily_from_minutes(bars)
    assert (day.open, day.high, day.low, day.close, day.volume) == (100.0, 102.0, 98.0, 100.2, 12)
    assert day.time == datetime(2026, 11, 10, tzinfo=KST)


def test_순서가_뒤섞인_봉도_시각순으로_합성한다():
    bars = [minute(10, 9, 10, 3.0), minute(10, 9, 0, 1.0), minute(10, 9, 5, 2.0)]
    assert daily_from_minutes(bars)[0].close == 3.0 and daily_from_minutes(bars)[0].open == 1.0


LEGS = [SpreadLeg(code="AAA", ratio=1), SpreadLeg(code="BBB", ratio=-1)]
INSTRUMENT = Instrument(name="x", market="overseas", exchange="FCME", code="AAA-BBB", multiplier=1000, legs=LEGS)


def daily(day: int, close: float) -> Bar:
    return Bar(datetime(2026, 11, day, tzinfo=KST), close, close, close, 10, close)


def make_base(daily_by_code, minute_by_code=None):
    calls = []

    def base(instrument, quantity):
        calls.append(("daily", instrument.code))
        return daily_by_code.get(instrument.code, [])

    if minute_by_code is not None:

        def from_minutes(instrument, quantity):
            calls.append(("minutes", instrument.code))
            return minute_by_code[instrument.code]

        base.from_minutes = from_minutes
    return base, calls


def test_한쪽_일봉이_비면_두_종목_모두_분봉_합성_일봉을_쓴다():
    base, calls = make_base(
        {"BBB": [daily(9, 50.0), daily(10, 51.0)]},
        {"AAA": [daily(9, 10.0), daily(10, 11.0)], "BBB": [daily(9, 20.0), daily(10, 22.0)]},
    )
    bars = spread_daily_fetcher(base)(INSTRUMENT, 10)
    assert [bar.close for bar in bars] == [10.0 - 20.0, 11.0 - 22.0]  # NH 일봉(50·51)이 아니라 합성 일봉으로 계산
    assert ("minutes", "AAA") in calls and ("minutes", "BBB") in calls


def test_일봉이_모두_있으면_합성하지_않는다():
    base, calls = make_base(
        {"AAA": [daily(9, 10.0)], "BBB": [daily(9, 4.0)]},
        {"AAA": [daily(9, 99.0)], "BBB": [daily(9, 99.0)]},
    )
    assert [bar.close for bar in spread_daily_fetcher(base)(INSTRUMENT, 10)] == [6.0]
    assert all(kind == "daily" for kind, _ in calls)


def test_합성_수단이_없으면_빈_일봉을_그대로_돌려준다():
    base, _ = make_base({"BBB": [daily(9, 4.0)]})
    assert spread_daily_fetcher(base)(INSTRUMENT, 10) == []
