from datetime import date, datetime, timedelta

import pytest

from app.runners.backtest import Assumptions
from app.runners.minute_backtest import MinuteBacktestEngine
from tests.test_backtest_engine import engine_for, journal
from strategy_base.interface import BaseStrategy
from strategy_base.models import Bar, IntentKind, OrderIntent, Side, StrategyOutput


DAY = date(2026, 10, 27)
START = datetime(2026, 10, 27, 9)


class ShortAtOpen(BaseStrategy):
    def on_bar(self, ctx):
        return StrategyOutput(state={"ready": True}) if len(ctx.bars) == 1 else StrategyOutput()

    def on_price(self, ctx):
        if ctx.state.get("ready") and not ctx.state.get("entered"):
            return StrategyOutput(orders=[OrderIntent(Side.SELL, 5, IntentKind.ENTRY, "short", "entry")],
                                  state={"entered": True})
        if ctx.lots:
            reason = "stop" if ctx.price >= 210500 else "target" if ctx.price <= 209500 else None
            if reason:
                return StrategyOutput(orders=[OrderIntent(Side.BUY, 5, IntentKind.EXIT, "short", reason)])
        return StrategyOutput()


def fixture(tmp_path):
    first = Bar(START, 210000, 210000, 210000, 3, 210000)
    second = Bar(START+timedelta(minutes=3), 211000, 209500, 210000, 3, 210000)
    minute = []
    for bar in (first, second):
        minute.extend([Bar(bar.time, bar.high, bar.low, bar.close, 1, bar.open),
                       Bar(bar.time+timedelta(minutes=1), bar.close, bar.close, bar.close, 1, bar.close),
                       Bar(bar.time+timedelta(minutes=2), bar.close, bar.close, bar.close, 1, bar.close)])
    _, recorder = engine_for(tmp_path, ShortAtOpen({}))
    engine = MinuteBacktestEngine(ShortAtOpen({}), recorder, Assumptions(0, 0, 10, 500),
        initial_capital=50000000, minutes=3, last_trading_day=date(2026, 11, 12), minute_days={DAY: minute})
    return engine, recorder, {DAY:[first, second]}, minute


def test_open_entry_sets_adverse_path_before_both_stop_and_target_touched(tmp_path):
    engine, recorder, days, _ = fixture(tmp_path)
    result = engine.run(days)
    trade = journal(recorder, "trade")[0]
    exit_fill = next(r for r in journal(recorder, "fill") if r["intent"] == "exit")
    assert trade["exit_price"] == 210500 and exit_fill["reason"] == "stop"
    assert result["net_pnl"] == -25000 and not engine.positions


def test_missing_minute_with_aggregate_mismatch_never_falls_back_to_signal_bar(tmp_path):
    engine, _, days, minutes = fixture(tmp_path)
    engine.minute_days = {DAY: minutes[:-1]}
    with pytest.raises(ValueError, match="OHLCV"):
        engine.run(days)
