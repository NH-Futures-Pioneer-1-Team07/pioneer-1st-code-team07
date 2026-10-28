"""완성된 신호 봉과 실제 관측 1분봉 가격 경로를 함께 사용하는 백테스트."""

from datetime import date, timedelta

from app.runners.backtest import BacktestEngine, price_path
from strategy_base.models import Bar, IntentKind


class MinuteBacktestEngine(BacktestEngine):
    def __init__(self, *args, minute_days: dict[date, list[Bar]], **kwargs):
        super().__init__(*args, **kwargs)
        self.minute_days = minute_days

    def run(self, days, on_progress=None):
        # A partial observed interval may exist (no-trade omission/market halt).
        # Preserve its availability; never fabricate absent minute bars.
        for day, bars in days.items():
            source = sorted(self.minute_days.get(day, []), key=lambda b: b.time)
            if len({m.time for m in source}) != len(source):
                raise ValueError(f"{day}: 중복된 1분봉")
            if any(m.time.date() != day or m.open is None or m.volume < 0
                   or not m.low <= min(m.open, m.close) <= max(m.open, m.close) <= m.high for m in source):
                raise ValueError(f"{day}: 잘못된 1분봉 OHLCV")
            for b in bars:
                group = [m for m in source if b.time <= m.time < b.time + timedelta(minutes=self.minutes)]
                actual = ((group[0].open, max(m.high for m in group), min(m.low for m in group),
                           group[-1].close, sum(m.volume for m in group)) if group else None)
                if actual != (b.open, b.high, b.low, b.close, b.volume):
                    raise ValueError(f"{b.time}: 1분봉 합산과 신호 봉 OHLCV가 일치하지 않습니다")
        return super().run(days, on_progress)

    def _run_day(self, day, bars):
        pending = []
        step = timedelta(minutes=self.minutes)
        source = sorted(self.minute_days[day], key=lambda b: b.time)
        for index, bar in enumerate(bars):
            completed = list(bars[:index])
            if index and bar.time - bars[index-1].time != step:
                pending = [order for order in pending if order.kind == IntentKind.EXIT]
            group = [m for m in source if bar.time <= m.time < bar.time + step]
            for minute in group:
                if minute.open is None:
                    raise ValueError(f"{minute.time}: 시가 없는 1분봉")
                # Delayed exits execute only when a real observed price becomes available.
                for order in pending:
                    self._fill(order, minute.open, minute.time, "next_open")
                pending = []
                output = self._call(self.strategy.on_price, minute.time, completed, minute.open)
                for order in output.orders:
                    self._fill(order, minute.open, minute.time, "minute_path")
                # The first price can establish a new position. Choose the adverse
                # extreme using that filled position, rather than the earlier flat state.
                for price in price_path(minute, self._net(), self.assumptions.tick_size)[1:]:
                    moment = minute.time + timedelta(seconds=59)
                    output = self._call(self.strategy.on_price, moment, completed, price)
                    for order in output.orders:
                        self._fill(order, price, moment, "minute_path")
                self._mark(minute.close, minute.time + timedelta(minutes=1))
            output = self._call(self.strategy.on_bar, bar.time + step, completed + [bar], None)
            pending.extend(output.orders)
            self.totals.bars += 1
        if pending or self.positions:
            raise ValueError(f"{day}: 관측 시세 내에서 당일 청산을 완료하지 못했습니다")
