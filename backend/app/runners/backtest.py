"""백테스트 시뮬레이션. 전략을 하루씩, 봉이 하나씩 마감되는 순서로 호출하고 가상 계좌에서 체결한다.

체결 가정
- `on_bar`가 낸 시장가 주문은 다음 봉의 시가에 전량 체결한다. 그날 마지막 봉이면 그 봉의 종가에 체결한다.
- `on_price`는 봉마다 시가 → 불리한 극단 → 유리한 극단 → 종가 순으로 호가 단위씩 가격을 움직이며
  호출한다. 보유 중이면 불리한 극단이 먼저다(롱은 저가, 숏은 고가). 이 호출이 낸 주문은 그 가격에 체결한다.
- 체결 가격에는 슬리피지를 불리한 방향으로 더하고, 체결대금(체결가 × 거래승수 × 수량)에 수수료율을 곱한
  수수료를 뺀다. 증거금과 주문가능수량은 제한하지 않는다.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from app.records.store import RunRecorder
from app.runners.ledger import Ledger
from strategy_base.interface import BaseStrategy
from strategy_base.models import Bar, Context, IntentKind, Lot, OrderIntent, Side, StrategyOutput

MAX_PATH_STEPS = 200
END_OF_PERIOD_REASON = "백테스트 종료 청산"


@dataclass(frozen=True)
class Assumptions:
    fee_rate: float
    slippage_ticks: int
    multiplier: int
    tick_size: float


@dataclass
class _Totals:
    bars: int = 0
    days: int = 0
    peak: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_rate: float = 0.0
    curve: list[dict[str, Any]] = field(default_factory=list)


def infer_tick(days: dict[date, list[Bar]]) -> float:
    """봉 가격 차이의 최대공약수로 호가 단위를 추정한다. 알 수 없으면 1이다."""
    prices = {
        round(value * 100)
        for bars in days.values()
        for bar in bars
        for value in (bar.open, bar.high, bar.low, bar.close)
        if value is not None
    }
    ordered = sorted(prices)
    divisor = 0
    for earlier, later in zip(ordered, ordered[1:]):
        divisor = math.gcd(divisor, later - earlier)
    return divisor / 100 if divisor else 1.0


def price_path(bar: Bar, net_quantity: int, tick: float) -> list[float]:
    """봉 안에서 가격이 지나간다고 가정하는 값들. 시가에서 시작해 종가로 끝난다."""
    if net_quantity > 0:
        order = [bar.low, bar.high]
    elif net_quantity < 0:
        order = [bar.high, bar.low]
    else:
        order = [bar.high, bar.low] if bar.high - bar.open <= bar.open - bar.low else [bar.low, bar.high]
    points = [bar.open, *order, bar.close]
    path = [bar.open]
    for start, end in zip(points, points[1:]):
        path.extend(_walk(start, end, tick))
    return [price for index, price in enumerate(path) if index == 0 or price != path[index - 1]]


def _walk(start: float, end: float, tick: float) -> list[float]:
    if start == end:
        return []
    steps = min(max(round(abs(end - start) / tick), 1), MAX_PATH_STEPS)
    return [start + (end - start) * step / steps for step in range(1, steps)] + [end]


class BacktestEngine:
    def __init__(
        self,
        strategy: BaseStrategy,
        recorder: RunRecorder,
        assumptions: Assumptions,
        *,
        initial_capital: float,
        minutes: int,
        last_trading_day: date | None,
    ):
        self.strategy = strategy
        self.recorder = recorder
        self.assumptions = assumptions
        self.initial_capital = initial_capital
        self.minutes = minutes
        self.last_trading_day = last_trading_day
        self.ledger = Ledger(
            multiplier=assumptions.multiplier, fee_rate=assumptions.fee_rate, initial_capital=initial_capital
        )
        self.totals = _Totals(peak=initial_capital)
        self.state: dict[str, Any] = {}

    # ---- 실행 ----

    def run(
        self,
        days: dict[date, list[Bar]],
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        last_bar: Bar | None = None
        for index, (day, bars) in enumerate(days.items(), 1):
            self._run_day(day, bars)
            last_bar = bars[-1]
            self.totals.days += 1
            self._day_summary(day, bars[-1])
            if on_progress:
                on_progress(index, len(days))
        if last_bar is not None:
            self._close_all(last_bar.close, last_bar.time + timedelta(minutes=self.minutes))
            self._mark(last_bar.close, last_bar.time + timedelta(minutes=self.minutes))
        return self._result()

    def _run_day(self, day: date, bars: Sequence[Bar]) -> None:
        pending: list[OrderIntent] = []
        step = timedelta(minutes=self.minutes)
        for index, bar in enumerate(bars):
            if bar.open is None:
                raise ValueError(f"{bar.time:%Y-%m-%d %H:%M} 봉에 시가가 없습니다")
            for order in pending:
                self._fill(order, bar.open, bar.time, "next_open")
            pending = []

            completed = list(bars[:index])
            before_close = bar.time + step - timedelta(seconds=1)
            for number, price in enumerate(price_path(bar, self._net(), self.assumptions.tick_size)):
                moment = bar.time if number == 0 else before_close
                output = self._call(self.strategy.on_price, moment, completed, price)
                for order in output.orders:
                    self._fill(order, price, moment, "intrabar")

            close_time = bar.time + step
            output = self._call(self.strategy.on_bar, close_time, completed + [bar], None)
            pending.extend(output.orders)
            self.totals.bars += 1
            self._mark(bar.close, close_time)

        end = bars[-1].time + step
        for order in pending:
            self._fill(order, bars[-1].close, end, "day_end")

    def _call(
        self,
        hook: Callable[[Context], StrategyOutput],
        now: datetime,
        bars: list[Bar],
        price: float | None,
    ) -> StrategyOutput:
        ctx = Context(
            now=now,
            bars=bars,
            params=self.strategy.params,
            last_trading_day=self.last_trading_day,
            price=price,
            lots=self._lots(),
            open_orders=(),
            state=self.state,
        )
        output = hook(ctx)
        if output.state is not None:
            self.state = dict(output.state)
        for decision in output.decisions:
            self.recorder.record(
                "decision",
                time=decision.time,
                result=decision.result.value,
                reason=decision.reason,
                score=decision.score,
                detail=dict(decision.detail),
                orders=[
                    {"side": o.side.value, "quantity": o.quantity, "entry_id": o.entry_id}
                    for o in output.orders
                ],
            )
        for order in output.orders:
            self.recorder.record(
                "order",
                time=now,
                status="submitted",
                side=order.side.value,
                quantity=order.quantity,
                order_type=order.order_type.value,
                intent=order.kind.value,
                entry_id=order.entry_id,
                reason=order.reason,
            )
        return output

    # ---- 체결 ----

    def _fill(self, order: OrderIntent, raw_price: float, moment: datetime, source: str) -> None:
        slip = self.assumptions.slippage_ticks * self.assumptions.tick_size
        price = raw_price + slip if order.side == Side.BUY else raw_price - slip
        if order.kind == IntentKind.ENTRY:
            self._enter(order, price, raw_price, moment, source)
        else:
            self._exit(order, price, raw_price, moment, source)

    def _enter(self, order: OrderIntent, price: float, raw_price: float, moment: datetime, source: str) -> None:
        applied = self.ledger.apply_entry(order.entry_id, order.side, order.quantity, price, moment)
        if applied is None:
            self._warn(moment, f"진입분 {order.entry_id}의 방향과 다른 진입 주문을 무시했습니다")
            return
        self._record_fill(order, applied.quantity, price, raw_price, applied.fee, moment, source)

    def _exit(self, order: OrderIntent, price: float, raw_price: float, moment: datetime, source: str) -> None:
        applied = self.ledger.apply_exit(order.entry_id, order.side, order.quantity, price, moment)
        if applied is None:
            self._warn(moment, f"청산할 진입분 {order.entry_id}이(가) 없어 청산 주문을 무시했습니다")
            return
        self._record_fill(order, applied.quantity, price, raw_price, applied.fee, moment, source)
        if applied.trade is not None:
            trade = applied.trade
            self.recorder.record(
                "trade",
                time=moment,
                entry_id=trade.entry_id,
                side=trade.side.value,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                gross_pnl=trade.gross_pnl,
                fee=trade.fee,
                net_pnl=trade.net_pnl,
                opened_at=trade.opened_at.isoformat() if trade.opened_at else None,
            )

    def _record_fill(
        self,
        order: OrderIntent,
        quantity: int,
        price: float,
        raw_price: float,
        fee: float,
        moment: datetime,
        source: str,
    ) -> None:
        self.recorder.record(
            "fill",
            time=moment,
            side=order.side.value,
            quantity=quantity,
            price=price,
            raw_price=raw_price,
            fee=fee,
            intent=order.kind.value,
            entry_id=order.entry_id,
            reason=order.reason,
            source=source,
        )

    def _close_all(self, raw_price: float, moment: datetime) -> None:
        """기간이 끝났을 때 남은 보유분을 청산한다."""
        for entry_id, position in list(self.ledger.positions.items()):
            side = Side.SELL if position.side == Side.BUY else Side.BUY
            order = OrderIntent(
                side=side,
                quantity=position.open_quantity,
                kind=IntentKind.EXIT,
                entry_id=entry_id,
                reason=END_OF_PERIOD_REASON,
            )
            self._fill(order, raw_price, moment, "backtest_end")

    # ---- 상태와 결과 ----

    def _lots(self) -> list[Lot]:
        return self.ledger.lots()

    def _net(self) -> int:
        return self.ledger.net_quantity()

    def _equity(self, price: float) -> float:
        return self.ledger.equity(price)

    @property
    def positions(self) -> dict:
        return self.ledger.positions

    def _mark(self, price: float, moment: datetime) -> None:
        equity = self._equity(price)
        totals = self.totals
        totals.peak = max(totals.peak, equity)
        drawdown = totals.peak - equity
        totals.max_drawdown = max(totals.max_drawdown, drawdown)
        if totals.peak > 0:
            totals.max_drawdown_rate = max(totals.max_drawdown_rate, drawdown / totals.peak)

    def _day_summary(self, day: date, last: Bar) -> None:
        equity = self._equity(last.close)
        self.totals.curve.append({"time": (last.time + timedelta(minutes=self.minutes)).isoformat(), "equity": equity})
        self.recorder.record(
            "event",
            time=last.time + timedelta(minutes=self.minutes),
            text="일별 요약",
            day=day.isoformat(),
            equity=equity,
            net_pnl=self.ledger.net_pnl,
            trades=self.ledger.trades,
        )

    def _warn(self, moment: datetime, text: str) -> None:
        self.recorder.record("event", time=moment, level="warning", text=text)

    def _result(self) -> dict[str, Any]:
        totals, ledger = self.totals, self.ledger
        net = ledger.net_pnl
        if totals.curve:
            totals.curve[-1] = {**totals.curve[-1], "equity": self.initial_capital + net}
        return {
            "initial_capital": self.initial_capital,
            "final_equity": self.initial_capital + net,
            "gross_pnl": ledger.gross_pnl,
            "fee": ledger.fee,
            "net_pnl": net,
            "return_rate": net / self.initial_capital if self.initial_capital else None,
            "trade_count": ledger.trades,
            "win_count": ledger.wins,
            "loss_count": ledger.losses,
            "max_drawdown": totals.max_drawdown,
            "max_drawdown_rate": totals.max_drawdown_rate,
            "days": totals.days,
            "bars": totals.bars,
            "equity_curve": totals.curve,
        }
