from datetime import time

from strategy_base.interface import BaseStrategy
from strategy_base.models import (
    Context,
    Decision,
    DecisionResult,
    IntentKind,
    OrderIntent,
    Side,
    StrategyOutput,
)


class Strategy(BaseStrategy):
    """템플릿 전략. 새 전략은 이 파일을 복사해 판단 규칙만 바꾼다.

    - 전략은 입력(`ctx`)만 보고 주문 의도를 돌려준다.
    - 주문 전송, 취소 실행, 계좌 조회, 파일 저장은 하지 않는다.
    - 기억해야 할 값은 `state`에 담아 돌려준다.
    """

    def on_bar(self, ctx: Context) -> StrategyOutput:
        bar = ctx.bars[-1]
        flatten_time = time.fromisoformat(self.params["flatten_time"])

        if ctx.now.time() >= flatten_time:
            return self._flatten(ctx)

        if len(ctx.bars) < 2 or ctx.lots or ctx.open_orders:
            return StrategyOutput()

        previous = ctx.bars[-2]
        if bar.close <= previous.high:
            return StrategyOutput(
                decisions=[Decision(ctx.now, DecisionResult.HOLD, "종가가 직전 봉 고가 이하")]
            )

        entry_number = ctx.state.get("entry_count", 0) + 1
        order = OrderIntent(
            side=Side.BUY,
            quantity=self.params["quantity"],
            kind=IntentKind.ENTRY,
            entry_id=f"entry-{entry_number}",
            reason="종가가 직전 봉 고가 초과",
            valid_bars=self.params["order_valid_bars"],
        )
        decision = Decision(
            ctx.now,
            DecisionResult.BUY,
            order.reason,
            detail={"close": bar.close, "previous_high": previous.high},
        )
        return StrategyOutput(orders=[order], decisions=[decision], state={"entry_count": entry_number})

    def _flatten(self, ctx: Context) -> StrategyOutput:
        orders = [
            OrderIntent(
                side=Side.SELL if lot.side == Side.BUY else Side.BUY,
                quantity=lot.quantity,
                kind=IntentKind.EXIT,
                entry_id=lot.entry_id,
                reason="당일 청산 시각",
            )
            for lot in ctx.lots
        ]
        return StrategyOutput(orders=orders)
