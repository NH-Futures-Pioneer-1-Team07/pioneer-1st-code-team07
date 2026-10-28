from datetime import datetime

import pytest

from app.nh.market_hours import market_session

NAME = "삼성전자 F 202611 ( 10)"
WEEKDAY = (2026, 10, 28)
SATURDAY = (2026, 10, 31)


@pytest.mark.parametrize(
    ("date", "hour", "minute", "expected"),
    [
        (WEEKDAY, 8, 29, "before_open"),
        (WEEKDAY, 8, 30, "auction"),
        (WEEKDAY, 8, 44, "auction"),
        (WEEKDAY, 8, 45, "regular"),
        (WEEKDAY, 15, 34, "regular"),
        (WEEKDAY, 15, 35, "auction"),
        (WEEKDAY, 15, 44, "auction"),
        (WEEKDAY, 15, 45, "closed"),
        (SATURDAY, 10, 0, "holiday"),
    ],
)
def test_삼성전자선물은_시각에_따라_장_종류를_판정한다(date, hour, minute, expected):
    assert market_session(NAME, datetime(*date, hour, minute)) == expected


def test_시간표가_없는_종목은_알_수_없음이다():
    assert market_session("미니 코스피200 F 202611", datetime(*WEEKDAY, 10, 0)) == "unknown"
