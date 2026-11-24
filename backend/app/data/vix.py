"""VIX 일 종가. 백테스트·조합 탐색·모의매매가 실행할 때 FRED `VIXCLS`에서 최신 값을 받는다(`latest`).

받은 값은 Git에 올리지 않는 `backend/data/vix_cache.csv`에 둔다. 받지 못하면 그 파일과 저장소의
`backend/data/vixcls.csv` 중 더 최근 값을 쓴다. 전략에는 직전 거래일 종가를 넘긴다. 장중 VIX는 다루지 않는다.
저장소의 파일은 `uv run python -m app.data.vix`로 갱신한다.
"""

import csv
import os
import sys
import tempfile
from bisect import bisect_left
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import httpx

from app.config import BACKEND_DIR

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
VIX_FILE = BACKEND_DIR / "data" / "vixcls.csv"
CACHE_FILE = BACKEND_DIR / "data" / "vix_cache.csv"
# 실행을 오래 붙잡지 않도록 자동으로 받을 때는 짧게 기다린다.
LATEST_TIMEOUT = 5.0
HEADER = ("observation_date", "VIXCLS")


class VixError(Exception):
    pass


class VixHistory:
    """날짜순으로 정렬한 VIX 종가. 휴장일 빈 값은 건너뛴다."""

    def __init__(self, closes: dict[date, float]):
        self._days = sorted(closes)
        self._closes = closes

    def __len__(self) -> int:
        return len(self._days)

    @property
    def last_day(self) -> date | None:
        return self._days[-1] if self._days else None

    def previous_day(self, day: date) -> date | None:
        """`day` 이전 마지막 거래일. 그런 날이 없으면 `None`이다."""
        index = bisect_left(self._days, day)
        return self._days[index - 1] if index else None

    def previous_close(self, day: date) -> float | None:
        """`day` 이전 마지막 거래일의 종가. 그런 날이 없으면 `None`이다."""
        previous = self.previous_day(day)
        return self._closes[previous] if previous else None


@dataclass(frozen=True)
class LatestVix:
    """실행에 쓸 VIX. `error`가 있으면 새로 받지 못해 저장해 둔 값을 쓴 것이다."""

    history: VixHistory | None
    error: str | None = None

    def event(self, day: date | None = None) -> dict[str, object]:
        """실행 기록에 남길 내용. `day`를 주면 그날 쓰는 종가와 날짜도 담는다."""
        fields: dict[str, object] = {
            "text": "VIX를 새로 받지 못해 저장된 값을 씁니다" if self.error else "VIX 최신 값을 받았습니다",
            "level": "warning" if self.error else "info",
            "vix_last_day": self.history.last_day.isoformat() if self.history and self.history.last_day else None,
        }
        if self.error:
            fields["error"] = self.error
        if day is not None:
            used = self.history.previous_day(day) if self.history else None
            fields["vix_day"] = used.isoformat() if used else None
            fields["vix"] = self.history.previous_close(day) if self.history else None
        return fields


def parse(text: str) -> VixHistory:
    closes: dict[date, float] = {}
    for row in csv.DictReader(text.splitlines()):
        try:
            when = datetime.strptime((row.get(HEADER[0]) or "").strip(), "%Y-%m-%d").date()
            closes[when] = float((row.get(HEADER[1]) or "").strip())
        except ValueError:
            continue  # 휴장일 빈 값(`.`·공백) 등
    if not closes:
        raise VixError("VIX 종가를 읽지 못했습니다")
    return VixHistory(closes)


def load(path: Path = VIX_FILE) -> VixHistory | None:
    """저장된 파일을 읽는다. 파일이 없으면 `None`이다."""
    if not path.is_file():
        return None
    return parse(path.read_text(encoding="utf-8"))


def download(client: httpx.Client | None = None) -> str:
    http = client or httpx.Client(timeout=30.0, follow_redirects=True)
    try:
        response = http.get(FRED_URL)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise VixError(f"FRED에서 VIX를 받지 못했습니다: {type(error).__name__}") from None
    parse(response.text)  # 형식 확인
    return response.text


def update(path: Path = VIX_FILE, client: httpx.Client | None = None) -> VixHistory:
    """FRED에서 받아 파일을 바꾼다. 받기에 실패하면 기존 파일을 그대로 둔다."""
    text = download(client)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return parse(text)


def latest() -> LatestVix:
    """FRED에서 최신 값을 받는다. 받지 못해도 예외를 내지 않고 저장해 둔 값 중 더 최근 것을 돌려준다."""
    error: str | None = None
    found: list[VixHistory] = []
    try:
        with httpx.Client(timeout=LATEST_TIMEOUT, follow_redirects=True) as client:
            text = download(client)
        found.append(parse(text))
        _write_cache(text)
    except VixError as problem:
        error = str(problem)
    for path in (CACHE_FILE, VIX_FILE):
        try:
            stored = load(path)
        except (VixError, OSError):
            continue  # 깨진 파일은 건너뛴다
        if stored is not None:
            found.append(stored)
    return LatestVix(max(found, key=lambda history: history.last_day or date.min, default=None), error)


def _write_cache(text: str) -> None:
    """다른 실행이 읽는 중에도 깨지지 않게 임시 파일에 쓴 뒤 바꾼다. 쓰지 못해도 받은 값은 그대로 쓴다."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        handle, name = tempfile.mkstemp(dir=CACHE_FILE.parent, prefix=CACHE_FILE.name, suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as file:
                file.write(text if text.endswith("\n") else text + "\n")
            os.replace(name, CACHE_FILE)
        except OSError:
            Path(name).unlink(missing_ok=True)
    except OSError:
        pass


if __name__ == "__main__":
    history = update()
    print(f"VIX {len(history)}일, 마지막 날짜 {history.last_day}", file=sys.stdout)
