"""VIX 일 종가. FRED `VIXCLS`를 CSV로 받아 `backend/data/vixcls.csv`에 저장해 두고 백테스트·모의매매가 같은 파일을 읽는다.

전략에는 직전 거래일 종가를 넘긴다. 장중 VIX는 다루지 않는다.
파일은 `uv run python -m app.data.vix`로 갱신한다.
"""

import csv
import sys
from bisect import bisect_left
from datetime import date, datetime
from pathlib import Path

import httpx

from app.config import BACKEND_DIR

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
VIX_FILE = BACKEND_DIR / "data" / "vixcls.csv"
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

    def previous_close(self, day: date) -> float | None:
        """`day` 이전 마지막 거래일의 종가. 그런 날이 없으면 `None`이다."""
        index = bisect_left(self._days, day)
        return self._closes[self._days[index - 1]] if index else None


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


if __name__ == "__main__":
    history = update()
    print(f"VIX {len(history)}일, 마지막 날짜 {history.last_day}", file=sys.stdout)
