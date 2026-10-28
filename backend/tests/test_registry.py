import json
from pathlib import Path

from strategy_base.registry import StrategyRegistry

VALID_MANIFEST = {
    "name": "테스트 전략",
    "description": "테스트용",
    "instruments": [{"name": "삼성전자선물", "code": "A116B000"}],
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
