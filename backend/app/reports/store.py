"""보고서 저장소. 읽기만 한다. 보고서는 `sweep-report` 스킬이 파일로 쓴다.

    <root>/<전략 id>/<보고서 이름>/report.md   JSON 머리말(`---` 두 줄 사이) + 마크다운 본문
    <root>/<전략 id>/<보고서 이름>/table.csv   `python -m app.sweep table`이 만든 비교표
"""

import csv
import json
import re
from pathlib import Path
from typing import Any

from strategy_base.manifest import STRATEGY_ID_PATTERN

REPORT_FILE = "report.md"
TABLE_FILE = "table.csv"
FRONT_FIELDS = ("strategy_id", "name", "title", "question", "updated", "author", "result_count", "periods", "recommended")
# 경로로 쓰이므로 구분자·상위 폴더 표시·숨김 이름을 막는다.
_NAME_FORBIDDEN = re.compile(r"[/\\\x00]")


class ReportError(Exception):
    pass


class ReportNotFound(ReportError):
    pass


class InvalidReport(ReportError):
    pass


def valid_name(name: str) -> bool:
    return bool(name) and not _NAME_FORBIDDEN.search(name) and not name.startswith(".") and len(name) <= 80


def split_front(text: str) -> tuple[dict[str, Any], str]:
    """(머리말, 본문). 머리말이 없거나 JSON이 아니면 `InvalidReport`다."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise InvalidReport("머리말(---)로 시작하지 않습니다")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as error:
        raise InvalidReport("머리말을 닫는 ---가 없습니다") from error
    try:
        front = json.loads("\n".join(lines[1:end]))
    except json.JSONDecodeError as error:
        raise InvalidReport(f"머리말이 JSON이 아닙니다: {error.msg} (줄 {error.lineno})") from error
    if not isinstance(front, dict):
        raise InvalidReport("머리말은 JSON 객체여야 합니다")
    missing = [name for name in FRONT_FIELDS if name not in front]
    if missing:
        raise InvalidReport(f"머리말에 없는 필드: {', '.join(missing)}")
    return front, "\n".join(lines[end + 1 :]).lstrip("\n")


def _cell(text: str) -> Any:
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return text


def read_table(path: Path) -> dict[str, Any] | None:
    """CSV를 `{columns, rows}`로 읽는다. 빈 칸은 `None`, 숫자는 실수다. 파일이 없으면 `None`."""
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        columns = next(reader, [])
        rows = [[_cell(value) for value in row] for row in reader if row]
    return {"columns": columns, "rows": rows}


class ReportStore:
    def __init__(self, root: Path):
        self.root = root

    def _path(self, strategy_id: str, name: str) -> Path:
        if not STRATEGY_ID_PATTERN.match(strategy_id) or not valid_name(name):
            raise ReportNotFound("보고서를 찾을 수 없습니다")
        return self.root / strategy_id / name

    def list_reports(self) -> list[dict[str, Any]]:
        """보고서 목록. 갱신일이 최근인 것부터. 머리말이 깨진 보고서는 `error`와 함께 담는다."""
        items: list[dict[str, Any]] = []
        if not self.root.exists():
            return items
        for strategy in sorted(path for path in self.root.iterdir() if path.is_dir()):
            for folder in sorted(path for path in strategy.iterdir() if path.is_dir()):
                report = folder / REPORT_FILE
                if not report.exists():
                    continue
                base = {"strategy_id": strategy.name, "name": folder.name}
                try:
                    front, _ = split_front(report.read_text(encoding="utf-8"))
                except (InvalidReport, UnicodeDecodeError) as error:
                    items.append({**base, "error": str(error)})
                    continue
                items.append(
                    {
                        **base,
                        "title": front["title"],
                        "question": front["question"],
                        "updated": front["updated"],
                        "author": front["author"],
                        "result_count": front["result_count"],
                        "recommended": [item.get("label") for item in front["recommended"]],
                        "error": None,
                    }
                )
        items.sort(key=lambda item: (item.get("updated") or "", item["name"]), reverse=True)
        return items

    def get(self, strategy_id: str, name: str) -> dict[str, Any]:
        folder = self._path(strategy_id, name)
        report = folder / REPORT_FILE
        if not report.exists():
            raise ReportNotFound("보고서를 찾을 수 없습니다")
        try:
            front, body = split_front(report.read_text(encoding="utf-8"))
        except UnicodeDecodeError as error:
            raise InvalidReport("보고서가 UTF-8이 아닙니다") from error
        return {"strategy_id": strategy_id, "name": name, "meta": front, "body": body, "table": read_table(folder / TABLE_FILE)}
