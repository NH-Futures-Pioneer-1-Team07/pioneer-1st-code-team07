"""승수가 다른 두 종목의 스프레드: 계약 수는 `ratio`, 가격 합성은 `weight`를 쓴다."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.runners.spread import combine, pair_bars, _ratios
from app.runners.spread_broker import SpreadPriceMux
from strategy_base.manifest import Instrument, SpreadLeg
from strategy_base.models import Bar

KST = timezone(timedelta(hours=9))
# 3년물 1계약(1포인트 2,000달러)과 10년물 1계약(1포인트 1,000달러): 스프레드 승수 1,000 기준 가중치 2·-1
LEGS = [SpreadLeg(code="Z3NZ26", ratio=1, weight=2), SpreadLeg(code="ZNZ26", ratio=-1)]


def test_가중치가_없으면_계약_비율이_가격_가중치다():
    assert SpreadLeg(code="ZFZ26", ratio=3).price_weight == 3
    assert SpreadLeg(code="ZNZ26", ratio=-2).price_weight == -2
    assert _ratios(LEGS) == (2, -1)


def test_가중치는_0이_아니고_계약_비율과_부호가_같아야_한다():
    with pytest.raises(ValidationError):
        SpreadLeg(code="A", ratio=1, weight=-2)
    with pytest.raises(ValidationError):
        SpreadLeg(code="A", ratio=1, weight=0)
    assert Instrument(name="x", market="overseas", legs=LEGS).legs[0].price_weight == 2


def test_봉은_가중치로_합치고_수수료_기준가도_가중치를_쓴다():
    one = Bar(datetime(2026, 11, 10, 9, 0, tzinfo=KST), 103.0, 103.0, 103.0, 5, 103.0)
    two = Bar(datetime(2026, 11, 10, 9, 0, tzinfo=KST), 106.0, 106.0, 106.0, 5, 106.0)
    assert combine(one, two, _ratios(LEGS)).close == 2 * 103.0 - 106.0
    assert [bar.close for bar in pair_bars([one], [two], _ratios(LEGS))] == [100.0]


def test_실시간_합성도_가중치를_쓴다():
    from app.nh.realtime_data import Trade

    posted = []
    mux = SpreadPriceMux("Z3NZ26-ZNZ26", LEGS, posted.append)
    for code, price in (("Z3NZ26", 103.0), ("ZNZ26", 106.0)):
        mux(Trade(code, "100000", price, 1, None, None, None, None, None, None, "1"))
    assert posted[0].price == 100.0


def test_시세_구성_문자열은_소수_가중치도_읽는다():
    from fastapi import HTTPException

    from app.api.market import _legs
    from app.api.stream import _parse_legs

    assert _legs("Z3NZ26:2,ZNZ26:-1", "overseas", "FCME") == [("Z3NZ26", 2.0), ("ZNZ26", -1.0)]
    assert _legs("Z3NZ26:1.5,ZNZ26:-1", "overseas", "FCME")[0] == ("Z3NZ26", 1.5)
    with pytest.raises(HTTPException):
        _legs("Z3NZ26:x,ZNZ26:-1", "overseas", "FCME")
    parsed = _parse_legs("Z3NZ26:2,ZNZ26:-1.5")
    assert [leg.price_weight for leg in parsed] == [2, -1.5]
    assert _parse_legs("Z3NZ26:0,ZNZ26:-1") is None
