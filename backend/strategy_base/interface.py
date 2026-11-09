from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from strategy_base.models import Context, StrategyOutput


class BaseStrategy(ABC):
    """모든 전략의 부모 클래스.

    전략 폴더의 `strategy.py`는 이 클래스를 상속한 `Strategy` 클래스를 정의한다.
    """

    def __init__(self, params: Mapping[str, Any]):
        self.params = params

    @abstractmethod
    def on_bar(self, ctx: Context) -> StrategyOutput:
        """봉이 마감될 때마다 호출된다. `ctx.bars[-1]`이 방금 마감된 봉이다."""

    def describe(self, ctx: Context) -> Mapping[str, Any]:
        """지금의 판단을 화면에 보여 줄 구조로 설명한다. 주문은 내지 않는다. 설명할 것이 없으면 빈 값을 돌려준다.

        돌려주는 형식은 `{"sections": [{"title", "headline", "tone", "rows": [[이름, 값], ...]}, ...]}`다.
        `tone`은 `buy`·`sell`·`neutral` 중 하나로 화면의 색을 정한다.
        """
        return {}

    def on_price(self, ctx: Context) -> StrategyOutput:
        """장중 가격이 갱신될 때 호출된다. 손절·목표 확인이 필요한 전략만 재정의한다."""
        return StrategyOutput()
