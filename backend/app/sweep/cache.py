"""분봉을 파일로 저장해 두고 다시 쓰는 로더.

NH가 오래된 분봉을 지워도 한 번 받은 기간은 남고, 같은 기간을 다시 받지 않는다. 요청한 기간 중
저장되지 않은 구간만 원래 로더로 받는다. 오늘 이후 날짜는 완성되지 않았으므로 저장하지 않는다.
"""

import json
import os
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

from app.runners.service import DataLoader, LoadedData
from strategy_base.models import Bar


def _bar_to_row(bar: Bar) -> list:
    return [bar.time.isoformat(), bar.high, bar.low, bar.close, bar.volume, bar.open]


def _row_to_bar(row: list) -> Bar:
    return Bar(datetime.fromisoformat(row[0]), row[1], row[2], row[3], row[4], row[5])


def _missing(start: date, end: date, covered: list[tuple[date, date]]) -> list[tuple[date, date]]:
    """[start, end] 중 저장된 구간에 없는 구간들."""
    pieces: list[tuple[date, date]] = []
    cursor = start
    for first, last in sorted(covered):
        if last < cursor:
            continue
        if first > end:
            break
        if first > cursor:
            pieces.append((cursor, first - timedelta(days=1)))
        cursor = max(cursor, last + timedelta(days=1))
        if cursor > end:
            break
    if cursor <= end:
        pieces.append((cursor, end))
    return pieces


def _merge(covered: list[tuple[date, date]]) -> list[tuple[date, date]]:
    merged: list[tuple[date, date]] = []
    for first, last in sorted(covered):
        if merged and first <= merged[-1][1] + timedelta(days=1):
            merged[-1] = (merged[-1][0], max(merged[-1][1], last))
        else:
            merged.append((first, last))
    return merged


class CachedLoader:
    def __init__(self, inner: DataLoader, folder: Path, market: str, today: Callable[[], date]):
        self._inner = inner
        self._folder = folder
        self._market = market
        self._today = today
        self.fetches = 0  # 원래 로더를 부른 횟수

    def __call__(
        self, code: str, minutes: int, start: date, end: date, on_progress: Callable[[int, int], None]
    ) -> LoadedData:
        path = self._folder / f"{self._market}_{code}_{minutes}m.json"
        stored = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        days: dict[date, list[Bar]] = {
            date.fromisoformat(key): [_row_to_bar(row) for row in rows] for key, rows in stored.get("days", {}).items()
        }
        covered = [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in stored.get("covered", [])]
        last_trading_day = stored.get("last_trading_day")
        last_trading = date.fromisoformat(last_trading_day) if last_trading_day else None

        changed = False
        for first, last in _missing(start, end, covered):
            loaded = self._inner(code, minutes, first, last, on_progress)
            self.fetches += 1
            if loaded.last_trading_day is not None:
                last_trading = loaded.last_trading_day
            complete = min(last, self._today() - timedelta(days=1))
            for day, bars in loaded.days.items():
                if day <= complete:
                    days[day] = bars
                    changed = True
            if first <= complete:
                covered = _merge([*covered, (first, complete)])
                changed = True
            for day, bars in loaded.days.items():
                days.setdefault(day, bars)

        if changed:
            self._folder.mkdir(parents=True, exist_ok=True)
            stored_days = {day.isoformat(): [_bar_to_row(bar) for bar in bars] for day, bars in sorted(days.items())}
            payload = {
                "last_trading_day": last_trading.isoformat() if last_trading else None,
                "covered": [[a.isoformat(), b.isoformat()] for a, b in covered],
                "days": {key: rows for key, rows in stored_days.items() if date.fromisoformat(key) < self._today()},
            }
            temp = path.with_name(path.name + ".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            os.replace(temp, path)

        selected = {day: days[day] for day in sorted(days) if start <= day <= end}
        return LoadedData(selected, last_trading)
