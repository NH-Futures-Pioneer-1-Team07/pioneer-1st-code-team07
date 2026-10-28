from datetime import date, timedelta

from app.runners.availability import RangeCache, find_range

TODAY = date(2026, 10, 28)


class Source:
    """날짜별 분봉 수를 정해 둔 가짜 조회. `days`는 분봉이 있는 날짜의 집합이다."""

    def __init__(self, days, last_trading_day=date(2026, 11, 12), few=None):
        self.days = set(days)
        self.few = few or {}
        self.ltd = last_trading_day
        self.calls = 0

    def bars_on(self, day):
        self.calls += 1
        return self.few.get(day, 100) if day in self.days else 0

    def last_trading_day(self):
        return self.ltd


def weekdays(start, end, skip=()):
    days, day = [], start
    while day <= end:
        if day.weekday() < 5 and day not in skip:
            days.append(day)
        day += timedelta(days=1)
    return days


# 실제 모의환경 관찰: 상장일 8/14에 1봉, 8/17은 비고, 추석 연휴(9/24~9/26)에는 없음
REAL = weekdays(date(2026, 8, 14), date(2026, 10, 27), skip={date(2026, 8, 17), date(2026, 9, 24), date(2026, 9, 25)})


def test_분봉이_있는_첫_날과_마지막_날을_찾는다():
    found = find_range(Source(REAL), TODAY)

    assert (found.start, found.end, found.last_trading_day) == (date(2026, 8, 14), date(2026, 10, 27), date(2026, 11, 12))


def test_종료는_오늘_이전의_분봉이_있는_가장_최근_날이다():
    days = weekdays(date(2026, 9, 1), date(2026, 10, 23))

    found = find_range(Source(days), date(2026, 10, 26))  # 월요일: 주말을 건너뛴다

    assert found.end == date(2026, 10, 23)


def test_오늘의_분봉은_가능_기간에_넣지_않는다():
    days = weekdays(date(2026, 9, 1), date(2026, 10, 28))

    assert find_range(Source(days), TODAY).end == date(2026, 10, 27)


def test_최종거래일이_지난_월물은_최종거래일이_종료다():
    days = weekdays(date(2026, 7, 1), date(2026, 9, 10))

    found = find_range(Source(days, last_trading_day=date(2026, 9, 10)), TODAY)

    assert (found.start, found.end) == (date(2026, 7, 1), date(2026, 9, 10))


def test_분봉이_전혀_없으면_없다():
    assert find_range(Source([]), TODAY) is None


def test_가운데가_두_주_비어도_시작을_잘못_정하지_않는다():
    days = weekdays(date(2026, 6, 1), date(2026, 6, 30)) + weekdays(date(2026, 7, 14), date(2026, 10, 27))

    assert find_range(Source(days), TODAY).start == date(2026, 6, 1)


def test_세_주_넘게_빈_뒤의_데이터는_다른_월물로_보고_포함하지_않는다():
    days = weekdays(date(2026, 3, 2), date(2026, 3, 31)) + weekdays(date(2026, 8, 3), date(2026, 10, 27))

    assert find_range(Source(days), TODAY).start == date(2026, 8, 3)


def test_상장일_근처에서_가장_이른_날을_하루_단위로_찾는다():
    days = [date(2026, 8, 14), date(2026, 8, 18), date(2026, 8, 19), *weekdays(date(2026, 8, 20), date(2026, 10, 27))]

    assert find_range(Source(days), TODAY).start == date(2026, 8, 14)


def test_데이터가_하루뿐이어도_찾는다():
    found = find_range(Source([date(2026, 10, 27)]), TODAY)

    assert (found.start, found.end) == (date(2026, 10, 27), date(2026, 10, 27))


def test_조회_호출_수가_작다():
    source = Source(REAL)

    find_range(source, TODAY)

    assert source.calls < 45


def test_같은_날에는_보관한_값을_쓰고_날이_바뀌면_다시_조회한다():
    source = Source(REAL)
    clock = {"today": TODAY}
    cache = RangeCache(lambda: clock["today"])

    first = cache.get("A116B000", source)
    after_first = source.calls
    second = cache.get("A116B000", source)
    assert second == first and source.calls == after_first

    cache.get("OTHER", source)  # 다른 종목은 따로 조회한다
    after_other = source.calls
    assert after_other > after_first

    clock["today"] = TODAY + timedelta(days=1)
    third = cache.get("A116B000", source)
    assert source.calls > after_other
    assert third.end == date(2026, 10, 27)


def test_기준보다_봉이_적은_날을_봉_수와_함께_담고_휴장일은_담지_않는다():
    few = {date(2026, 8, 14): 1, date(2026, 8, 20): 19, date(2026, 9, 10): 70, date(2026, 9, 9): 69}

    found = find_range(Source(REAL, few=few), TODAY, sparse_below=70)

    assert found.sparse_days == {date(2026, 8, 14): 1, date(2026, 8, 20): 19, date(2026, 9, 9): 69}
    assert date(2026, 8, 17) not in found.sparse_days and date(2026, 9, 24) not in found.sparse_days


def test_기준을_주지_않으면_봉이_적은_날을_찾지_않고_조회_수도_늘지_않는다():
    plain, counted = Source(REAL, few={date(2026, 8, 20): 5}), Source(REAL, few={date(2026, 8, 20): 5})

    assert find_range(plain, TODAY).sparse_days == {}
    find_range(counted, TODAY, sparse_below=70)
    assert counted.calls <= plain.calls + len(REAL)


def test_봉이_적은_날을_찾을_때_같은_날을_두_번_조회하지_않는다():
    source = Source(REAL)
    seen = []
    original = source.bars_on
    source.bars_on = lambda day: (seen.append(day), original(day))[1]

    find_range(source, TODAY, sparse_below=70)

    assert len(seen) == len(set(seen))
