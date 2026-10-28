import importlib.util
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from strategy_base.interface import BaseStrategy
from strategy_base.manifest import STRATEGY_ID_PATTERN, Manifest

logger = logging.getLogger(__name__)

MANIFEST_FILE = "manifest.json"
STRATEGY_FILE = "strategy.py"
STRATEGY_CLASS = "Strategy"


@dataclass(frozen=True)
class RegisteredStrategy:
    id: str
    path: Path
    manifest: Manifest
    strategy_class: type[BaseStrategy]


class LoadError(Exception):
    pass


class StrategyRegistry:
    """`strategies/` 아래 폴더를 스캔해 전략을 등록한다.

    - 폴더명이 전략 `id`다.
    - `_`나 `.`으로 시작하는 폴더는 건너뛴다(템플릿 등).
    - 잘못된 폴더는 `errors`에 폴더명과 원인을 남기고 목록에서 제외한다.
    """

    def __init__(self, root: Path):
        self.root = root
        self.strategies: dict[str, RegisteredStrategy] = {}
        self.errors: dict[str, str] = {}
        self.scan()

    def scan(self) -> None:
        self.strategies = {}
        self.errors = {}
        if not self.root.is_dir():
            logger.warning("전략 폴더가 없습니다: %s", self.root)
            return
        for folder in sorted(self.root.iterdir()):
            if not folder.is_dir() or folder.name.startswith(("_", ".")):
                continue
            try:
                if not STRATEGY_ID_PATTERN.match(folder.name):
                    raise LoadError("폴더명은 소문자 영문으로 시작하고 소문자·숫자·밑줄만 쓸 수 있습니다")
                self.strategies[folder.name] = load_strategy(folder)
            except LoadError as error:
                self.errors[folder.name] = str(error)
                logger.error("전략 %s을(를) 등록하지 못했습니다: %s", folder.name, error)

    def get(self, strategy_id: str) -> RegisteredStrategy | None:
        return self.strategies.get(strategy_id)

    def all(self) -> list[RegisteredStrategy]:
        return list(self.strategies.values())


def load_strategy(folder: Path) -> RegisteredStrategy:
    """전략 폴더 하나를 읽어 검증한다. 문제가 있으면 `LoadError`를 낸다."""
    strategy_id = folder.name
    manifest = _read_manifest(folder / MANIFEST_FILE)
    strategy_class = _read_strategy_class(strategy_id, folder / STRATEGY_FILE)
    return RegisteredStrategy(strategy_id, folder, manifest, strategy_class)


def _read_manifest(path: Path) -> Manifest:
    if not path.is_file():
        raise LoadError(f"{MANIFEST_FILE}이 없습니다")
    try:
        return Manifest.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        raise LoadError(f"{MANIFEST_FILE}이 올바른 JSON이 아닙니다: {error}") from error
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}" for item in error.errors()
        )
        raise LoadError(f"{MANIFEST_FILE}이 올바르지 않습니다: {details}") from error


def _read_strategy_class(strategy_id: str, path: Path) -> type[BaseStrategy]:
    if not path.is_file():
        raise LoadError(f"{STRATEGY_FILE}이 없습니다")
    spec = importlib.util.spec_from_file_location(f"strategies.{strategy_id}", path)
    if spec is None or spec.loader is None:
        raise LoadError(f"{STRATEGY_FILE}을 불러올 수 없습니다")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        raise LoadError(f"{STRATEGY_FILE}을 불러오다 오류가 났습니다: {error!r}") from error
    strategy_class = getattr(module, STRATEGY_CLASS, None)
    if not (isinstance(strategy_class, type) and issubclass(strategy_class, BaseStrategy)):
        raise LoadError(f"{STRATEGY_FILE}에 BaseStrategy를 상속한 {STRATEGY_CLASS} 클래스가 없습니다")
    return strategy_class
