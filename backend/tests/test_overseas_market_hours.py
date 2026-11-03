from datetime import datetime, time

import pytest

from app.nh.overseas.market_hours import exchange_name, parse_window, product_code, session

OVERNIGHT = (time(8, 0), time(7, 0))  # 08:00 ~ 07:00


def at(day, hour, minute=0):
    return datetime(2026, 11, day, hour, minute)  # 2일 월, 3일 화, 4일 수, 6일 금, 7일 토, 8일 일


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (at(2, 7, 59), "closed"),  # 월요일 시작 전(주말 휴장)
        (at(2, 8, 0), "regular"),  # 월요일 시작
        (at(3, 0, 0), "regular"),  # 화요일 새벽은 월요일 구간의 이어짐
        (at(3, 6, 59), "regular"),
        (at(3, 7, 0), "closed"),  # 일일 휴장
        (at(3, 7, 59), "closed"),
        (at(3, 8, 0), "regular"),
        (at(6, 23, 0), "regular"),  # 금요일 저녁
        (at(7, 6, 59), "regular"),  # 토요일 새벽은 금요일 구간의 끝
        (at(7, 7, 0), "closed"),  # 주말 휴장 시작
        (at(7, 12, 0), "closed"),
        (at(8, 12, 0), "closed"),  # 일요일
    ],
)
def test_날짜를_넘는_거래시간과_주말_휴장을_판정한다(moment, expected):
    assert session(OVERNIGHT, moment) == expected


def test_같은_날_안에_끝나는_거래시간은_평일만_연다():
    window = (time(9, 0), time(17, 0))

    assert session(window, at(3, 12)) == "regular"
    assert session(window, at(3, 18)) == "closed"
    assert session(window, at(7, 12)) == "closed"


def test_거래시간_문자열을_읽는다():
    assert parse_window("08:00 ~ 07:00") == (time(8, 0), time(7, 0))
    assert parse_window("00:00 ~ 24:00") == (time(0, 0), time(0, 0))
    assert parse_window("") is None
    assert parse_window("모름") is None


def test_종목코드와_거래소_코드를_변환한다():
    assert product_code("ZNZ26") == "ZN"
    assert product_code("6AU26") == "6A"
    assert product_code("ZN") == "ZN"
    assert exchange_name("FCME") == "CME"
    assert exchange_name("CME") == "CME"
