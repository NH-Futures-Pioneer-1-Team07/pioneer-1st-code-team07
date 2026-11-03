import json
from pathlib import Path

import pytest

from strategy_base.registry import StrategyRegistry

VALID_MANIFEST = {
    "name": "테스트 전략",
    "description": "테스트용",
    "instruments": [{"name": "삼성전자선물", "market": "domestic", "code": "A116B000"}],
    "bar": {"unit": "minute", "size": 3},
    "parameters": {"quantity": {"default": 5, "description": "수량"}},
}

VALID_STRATEGY = """
from strategy_base.interface import BaseStrategy
from strategy_base.models import StrategyOutput

class Strategy(BaseStrategy):
    def on_bar(self, ctx):
        return StrategyOutput()
"""


def make_folder(root: Path, name: str, manifest=VALID_MANIFEST, strategy: str | None = VALID_STRATEGY):
    folder = root / name
    folder.mkdir()
    if manifest is not None:
        text = manifest if isinstance(manifest, str) else json.dumps(manifest, ensure_ascii=False)
        (folder / "manifest.json").write_text(text, encoding="utf-8")
    if strategy is not None:
        (folder / "strategy.py").write_text(strategy, encoding="utf-8")


def test_폴더를_추가하면_전략으로_등록된다(tmp_path):
    make_folder(tmp_path, "week02_sample")

    registry = StrategyRegistry(tmp_path)

    assert [item.id for item in registry.all()] == ["week02_sample"]
    assert registry.errors == {}
    assert registry.get("week02_sample").manifest.default_params() == {"quantity": 5}


def test_종목에_market이_없거나_잘못되면_등록하지_않는다(tmp_path):
    def with_market(**market):
        return {**VALID_MANIFEST, "instruments": [{"name": "삼성전자선물", "code": "A116B000", **market}]}

    make_folder(tmp_path, "no_market", manifest=with_market())
    make_folder(tmp_path, "bad_market", manifest=with_market(market="japan"))
    make_folder(tmp_path, "overseas", manifest=with_market(market="overseas"))

    registry = StrategyRegistry(tmp_path)

    assert [item.id for item in registry.all()] == ["overseas"]
    assert set(registry.errors) == {"no_market", "bad_market"}
    assert "market" in registry.errors["no_market"]


def test_밑줄이나_점으로_시작하는_폴더는_건너뛴다(tmp_path):
    make_folder(tmp_path, "_template")
    make_folder(tmp_path, ".hidden")

    registry = StrategyRegistry(tmp_path)

    assert registry.all() == []
    assert registry.errors == {}


def test_잘못된_폴더는_제외하고_나머지는_등록한다(tmp_path):
    make_folder(tmp_path, "good")
    make_folder(tmp_path, "no_manifest", manifest=None)
    make_folder(tmp_path, "bad_json", manifest="{not json")
    make_folder(tmp_path, "bad_manifest", manifest={"name": "이름만 있음"})
    make_folder(tmp_path, "no_strategy_file", strategy=None)
    make_folder(tmp_path, "no_class", strategy="x = 1")
    make_folder(tmp_path, "broken_code", strategy="raise RuntimeError('boom')")
    make_folder(tmp_path, "BadName")

    registry = StrategyRegistry(tmp_path)

    assert [item.id for item in registry.all()] == ["good"]
    assert set(registry.errors) == {
        "no_manifest",
        "bad_json",
        "bad_manifest",
        "no_strategy_file",
        "no_class",
        "broken_code",
        "BadName",
    }
    assert "manifest.json이 없습니다" in registry.errors["no_manifest"]
    assert "description" in registry.errors["bad_manifest"]


def test_전략_폴더가_없으면_빈_목록이다(tmp_path):
    registry = StrategyRegistry(tmp_path / "missing")

    assert registry.all() == []


def test_저장소의_전략_폴더는_오류_없이_스캔되고_템플릿은_등록하지_않는다():
    from app.config import BACKEND_DIR

    registry = StrategyRegistry(BACKEND_DIR / "strategies")

    assert registry.errors == {}
    assert "_template" not in [item.id for item in registry.all()]


def test_추가_봉_계열은_일봉만_선언할_수_있다():
    from pydantic import ValidationError

    from strategy_base.manifest import Manifest

    base = {
        "name": "n",
        "description": "d",
        "instruments": [{"name": "i", "market": "overseas", "exchange": "FCME", "code": "ZNZ26", "margin": 2500}],
        "bar": {"unit": "minute", "size": 5},
        "history_bars": 20,
    }

    manifest = Manifest.model_validate({**base, "series": {"daily": {"unit": "day", "size": 1}}})
    assert manifest.series["daily"].unit == "day" and manifest.history_bars == 20

    for bad in ({"hourly": {"unit": "minute", "size": 60}}, {"Daily": {"unit": "day", "size": 1}}):
        with pytest.raises(ValidationError):
            Manifest.model_validate({**base, "series": bad})


def test_파라미터_범위와_단위를_선언하고_요청값을_검증한다():
    from strategy_base.manifest import Manifest

    manifest = Manifest.model_validate(
        {
            "name": "n",
            "description": "d",
            "instruments": [{"name": "i", "market": "domestic"}],
            "bar": {"unit": "minute", "size": 3},
            "parameters": {
                "rate": {"default": 0.2, "description": "비율", "editable": True, "unit": "percent", "min": 0.01, "max": 1},
                "plain": {"default": 1, "description": "범위 없음"},
            },
        }
    )

    assert manifest.override_problem({"rate": 0.5, "plain": "아무 값"}) is None
    assert manifest.override_problem(None) is None
    assert "1% 이상" in manifest.override_problem({"rate": 0})
    assert "100% 이하" in manifest.override_problem({"rate": 1.01})
    assert "숫자" in manifest.override_problem({"rate": "많이"})
    assert "숫자" in manifest.override_problem({"rate": True})
    assert "없는 파라미터" in manifest.override_problem({"unknown": 1})
