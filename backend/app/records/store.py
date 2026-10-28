"""실행 기록의 저장과 조회.

    <root>/<전략 id>/<backtest|paper>/<실행 일시>/
        meta.json            실행 정보
        result.json          실행이 끝나면 쓰는 최종 요약
        journal/<날짜>.jsonl 날짜별 기록. 한 줄이 한 사건
"""

import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.records.sanitize import sanitize
from strategy_base.manifest import STRATEGY_ID_PATTERN

KST = timezone(timedelta(hours=9))

MODES = ("backtest", "paper")
KINDS = ("decision", "order", "fill", "trade", "event")
STATUSES = ("running", "completed", "interrupted", "error")

RUN_ID_PATTERN = re.compile(r"^\d{8}_\d{6}(-\d+)?$")
BASE_FIELDS = ("run_id", "strategy_id", "mode", "seq", "time", "kind")

BACKTEST_ASSUMPTIONS = {"fee": None, "slippage": None, "fill": None}


class RecordError(Exception):
    pass


class RunNotFound(RecordError):
    pass


def to_kst(value: datetime) -> datetime:
    """시간대가 없는 시각은 한국 시간으로 본다."""
    return value.replace(tzinfo=KST) if value.tzinfo is None else value.astimezone(KST)


def now_kst() -> datetime:
    return datetime.now(KST)


def _write_json(path: Path, data: Any) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(temp, path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class RunRecorder:
    """실행 하나의 기록을 남긴다."""

    def __init__(self, folder: Path, meta: dict[str, Any]):
        self.folder = folder
        self.meta = meta
        self._seq = 0
        self._lock = threading.Lock()
        (folder / "journal").mkdir(exist_ok=True)

    @property
    def run_id(self) -> str:
        return self.meta["run_id"]

    def record(self, kind: str, time: datetime | None = None, **fields: Any) -> dict[str, Any]:
        """사건 한 줄을 덧붙인다. 비밀정보 필드는 지우고 쓴다."""
        if kind not in KINDS:
            raise RecordError(f"알 수 없는 기록 종류: {kind}")
        clash = [name for name in fields if name in BASE_FIELDS]
        if clash:
            raise RecordError(f"공통 필드와 겹치는 이름은 쓸 수 없습니다: {', '.join(clash)}")
        moment = to_kst(time) if time else now_kst()
        with self._lock:
            self._seq += 1
            line = {
                "run_id": self.run_id,
                "strategy_id": self.meta["strategy_id"],
                "mode": self.meta["mode"],
                "seq": self._seq,
                "time": moment.isoformat(),
                "kind": kind,
                **sanitize(fields),
            }
            path = self.folder / "journal" / f"{moment.date().isoformat()}.jsonl"
            with path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
        return line

    def finish(self, result: dict[str, Any] | None = None, status: str = "completed") -> None:
        """실행을 마치고 결과와 상태를 확정한다."""
        if status not in STATUSES or status == "running":
            raise RecordError(f"끝낼 때 쓸 수 없는 상태: {status}")
        with self._lock:
            if result is not None:
                _write_json(self.folder / "result.json", sanitize(result))
            self.meta["status"] = status
            self.meta["ended_at"] = now_kst().isoformat()
            _write_json(self.folder / "meta.json", self.meta)


@dataclass(frozen=True)
class JournalPage:
    items: list[dict[str, Any]]
    total: int
    offset: int
    limit: int


class RunStore:
    def __init__(self, root: Path):
        self.root = root

    # ---- 시작 ----

    def start_run(
        self,
        *,
        strategy_id: str,
        strategy_name: str,
        mode: str,
        instrument: dict[str, Any],
        params: dict[str, Any],
        started_at: datetime | None = None,
        period: dict[str, str] | None = None,
        initial_capital: float | None = None,
        assumptions: dict[str, Any] | None = None,
    ) -> RunRecorder:
        """실행 폴더를 만들고 기록기를 돌려준다.

        백테스트는 `period`, `initial_capital`, `assumptions`(비용·체결 가정)를 함께 남긴다.
        """
        self._check_ids(strategy_id, mode)
        started = to_kst(started_at) if started_at else now_kst()
        folder, run_id = self._new_folder(strategy_id, mode, started)
        meta: dict[str, Any] = {
            "run_id": run_id,
            "strategy_id": strategy_id,
            "strategy_name": strategy_name,
            "mode": mode,
            "instrument": instrument,
            "params": params,
            "started_at": started.isoformat(),
            "ended_at": None,
            "status": "running",
        }
        if mode == "backtest":
            meta["period"] = period
            meta["initial_capital"] = initial_capital
            meta["assumptions"] = {**BACKTEST_ASSUMPTIONS, **(assumptions or {})}
        meta = sanitize(meta)
        recorder = RunRecorder(folder, meta)
        _write_json(folder / "meta.json", meta)
        return recorder

    def _new_folder(self, strategy_id: str, mode: str, started: datetime) -> tuple[Path, str]:
        parent = self.root / strategy_id / mode
        parent.mkdir(parents=True, exist_ok=True)
        base = started.strftime("%Y%m%d_%H%M%S")
        run_id, number = base, 0
        while True:
            try:
                (parent / run_id).mkdir()
                return parent / run_id, run_id
            except FileExistsError:
                number += 1
                run_id = f"{base}-{number}"

    # ---- 재시작 ----

    def mark_interrupted(self) -> list[str]:
        """실행 중으로 남은 기록을 중단 상태로 바꾼다. 바꾼 폴더 경로를 돌려준다."""
        changed = []
        for meta_path in self.root.glob("*/*/*/meta.json") if self.root.is_dir() else []:
            meta = _read_json(meta_path)
            if meta.get("status") == "running":
                meta["status"] = "interrupted"
                _write_json(meta_path, meta)
                changed.append(str(meta_path.parent))
        return changed

    # ---- 조회 ----

    def list_runs(self, mode: str | None = None, strategy_id: str | None = None) -> list[dict[str, Any]]:
        """실행 목록. 최근에 시작한 순서다. 결과가 있으면 순손익도 담는다."""
        runs = []
        if not self.root.is_dir():
            return runs
        for meta_path in self.root.glob("*/*/*/meta.json"):
            try:
                meta = _read_json(meta_path)
            except (OSError, json.JSONDecodeError):
                continue
            if mode and meta.get("mode") != mode:
                continue
            if strategy_id and meta.get("strategy_id") != strategy_id:
                continue
            result = self._read_result(meta_path.parent)
            runs.append({**_summary(meta), "net_pnl": (result or {}).get("net_pnl")})
        return sorted(runs, key=lambda item: item["started_at"], reverse=True)

    def get_run(self, strategy_id: str, mode: str, run_id: str) -> dict[str, Any]:
        folder = self._folder(strategy_id, mode, run_id)
        return {"meta": _read_json(folder / "meta.json"), "result": self._read_result(folder)}

    def read_journal(
        self,
        strategy_id: str,
        mode: str,
        run_id: str,
        *,
        kind: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> JournalPage:
        """기록을 시간순으로 거르고 나눠서 돌려준다. `end`는 포함하지 않는다."""
        folder = self._folder(strategy_id, mode, run_id)
        low = to_kst(start) if start else None
        high = to_kst(end) if end else None
        matched: list[dict[str, Any]] = []
        for path in sorted((folder / "journal").glob("*.jsonl")):
            if not _day_overlaps(path.stem, low, high):
                continue
            for text in path.read_text(encoding="utf-8").splitlines():
                if not text.strip():
                    continue
                line = json.loads(text)
                moment = datetime.fromisoformat(line["time"])
                if kind and line["kind"] != kind:
                    continue
                if (low and moment < low) or (high and moment >= high):
                    continue
                matched.append(line)
        return JournalPage(matched[offset : offset + limit], len(matched), offset, limit)

    # ---- 내부 ----

    def _folder(self, strategy_id: str, mode: str, run_id: str) -> Path:
        self._check_ids(strategy_id, mode)
        if not RUN_ID_PATTERN.match(run_id):
            raise RunNotFound(run_id)
        folder = self.root / strategy_id / mode / run_id
        if not (folder / "meta.json").is_file():
            raise RunNotFound(f"{strategy_id}/{mode}/{run_id}")
        return folder

    def _check_ids(self, strategy_id: str, mode: str) -> None:
        if not STRATEGY_ID_PATTERN.match(strategy_id):
            raise RunNotFound(f"잘못된 전략 id: {strategy_id}")
        if mode not in MODES:
            raise RunNotFound(f"잘못된 모드: {mode}")

    def _read_result(self, folder: Path) -> dict[str, Any] | None:
        path = folder / "result.json"
        return _read_json(path) if path.is_file() else None


def _summary(meta: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "run_id",
        "strategy_id",
        "strategy_name",
        "mode",
        "instrument",
        "started_at",
        "ended_at",
        "status",
        "period",
        "initial_capital",
    )
    return {key: meta.get(key) for key in keys}


def _day_overlaps(stem: str, low: datetime | None, high: datetime | None) -> bool:
    """날짜별 파일이 조회 구간과 겹칠 수 있는지 본다."""
    try:
        day = date.fromisoformat(stem)
    except ValueError:
        return False
    if low and day < low.date():
        return False
    if high and day > high.date():
        return False
    return True
