"""전략 입력 중 봉 외의 값(추가 봉 계열, VIX, 증거금)을 `Context`에 채울 값으로 만든다. 백테스트와 모의매매가 같은 코드를 쓴다."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app.data.vix import VixHistory
from strategy_base.models import Bar

# 날짜 -> 계열 이름별 일봉(오래된 것부터). 모의매매는 날짜가 바뀔 때 다시 부른다.
SeriesLoader = Callable[[date], Mapping[str, Sequence[Bar]]]


@dataclass
class ExtraInputs:
    """봉 외의 전략 입력.

    - `series`: 계열 이름별 일봉. `now` 이전 날짜의 봉만 넘긴다(오늘 일봉은 아직 완성되지 않았다).
    - `vix`: 직전 거래일 종가를 넘긴다.
    - `margin`: 계약당 기준 증거금.
    """

    series: Mapping[str, Sequence[Bar]] = field(default_factory=dict)
    vix: VixHistory | None = None
    margin: float | None = None
    loader: SeriesLoader | None = None
    _loaded_for: date | None = field(default=None, init=False, repr=False)

    def prepare(self, day: date) -> None:
        """날짜가 바뀌었으면 계열을 다시 불러온다. 블로킹 호출이므로 비동기 코드에서는 스레드에서 부른다."""
        if self.loader is not None and self._loaded_for != day:
            self.series = self.loader(day)
            self._loaded_for = day

    def fields(self, now: datetime) -> dict[str, Any]:
        today = now.date()
        return {
            "series": {name: [bar for bar in bars if bar.time.date() < today] for name, bars in self.series.items()},
            "vix": self.vix.previous_close(today) if self.vix else None,
            "margin": self.margin,
        }
