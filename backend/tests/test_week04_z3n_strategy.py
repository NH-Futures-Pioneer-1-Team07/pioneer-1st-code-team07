"""Z3N·ZN 스프레드 전략: 기존 ZF·ZN 전략과 판단 규칙은 같고 종목·가중치·비용 값만 다르다."""

from pathlib import Path

from strategy_base.registry import StrategyRegistry

STRATEGIES = Path(__file__).resolve().parents[1] / "strategies"


def registered():
    registry = StrategyRegistry(STRATEGIES)
    registry.scan()
    return registry


def test_두_스프레드_전략이_함께_등록된다():
    registry = registered()
    assert registry.get("week04_zf_zn_spread") is not None
    assert registry.get("week04_z3n_zn_spread") is not None


def test_z3n_zn_종목은_1대1_계약과_승수_반영_가중치를_가진다():
    instrument = registered().get("week04_z3n_zn_spread").manifest.instruments[0]
    assert instrument.code == "Z3NZ26-ZNZ26"
    assert instrument.multiplier == 1000
    assert [(leg.code, leg.ratio, leg.price_weight) for leg in instrument.legs] == [("Z3NZ26", 1, 2.0), ("ZNZ26", -1, -1.0)]
    # 슬리피지 1틱: 두 종목이 1호가씩 불리하게 체결되는 폭(승수 1,000 기준)
    assert instrument.tick_size == 2 * 0.00390625 + 0.015625
    assert instrument.margin == 2000 + 2063


def test_파라미터는_기존_전략과_같다():
    registry = registered()
    old = registry.get("week04_zf_zn_spread").manifest
    new = registry.get("week04_z3n_zn_spread").manifest
    assert new.default_params() == old.default_params()
    assert new.bar == old.bar
    assert "entry_confirm_seconds" not in new.default_params()


def test_기존_전략_매니페스트는_가중치가_없다():
    instrument = registered().get("week04_zf_zn_spread").manifest.instruments[0]
    assert [leg.weight for leg in instrument.legs] == [None, None]
    assert [leg.price_weight for leg in instrument.legs] == [3, -2]
