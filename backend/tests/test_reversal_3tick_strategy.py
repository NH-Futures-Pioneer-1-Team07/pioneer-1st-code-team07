from datetime import date, datetime, timedelta

import pytest

from app.config import BACKEND_DIR
from strategy_base.models import IntentKind, Lot, OpenOrder, Side
from strategy_base.registry import StrategyRegistry, load_strategy
from tests.test_reversal_strategy import BUY_ROWS, Run


FOLDER = BACKEND_DIR / "strategies/week02_samsung_futures_reversal_3tick"


def pending():
    registered = load_strategy(FOLDER)
    strategy = registered.strategy_class({**registered.manifest.default_params(), "stop_offset": 2, "tick_size": 1})
    probe = Run(strategy, BUY_ROWS)
    output = probe.through(12)[-1]
    assert not output.orders
    assert probe.state["pending_entry"]["entry_id"] == "2026-10-27-1"
    return probe


def test_new_strategy_registers_with_existing_two():
    registry = StrategyRegistry(BACKEND_DIR / "strategies")
    assert not registry.errors
    assert {"week02_samsung_futures_intraday", "week02_samsung_futures_reversal", FOLDER.name} <= set(registry.strategies)
    manifest = registry.get(FOLDER.name).manifest
    assert manifest.bar.size == 3 and manifest.backtest.price_minutes == 1
    assert manifest.default_params()["min_target_ticks"] == 3


@pytest.mark.parametrize("price,accepted", [(21, True), (22, False), (10, False), (24, False)])
def test_entry_uses_first_price_and_inclusive_minimum_target(price, accepted):
    probe = pending()
    output = probe.price(12, price)
    assert bool(output.orders) == accepted
    if accepted:
        order = output.orders[0]
        assert (order.kind, order.side, order.quantity) == (IntentKind.ENTRY, Side.BUY, 5)
    assert not probe.price(12, 16).orders  # consumed signal, including rejected first quote


@pytest.mark.parametrize("now", [datetime(2026, 10, 27, 9, 37), datetime(2026, 10, 27, 15, 24)])
def test_stale_or_cutoff_signal_never_enters(now):
    probe = pending()
    assert not probe.price(12, 16, now=now).orders
    assert probe.state.get("pending_entry") is None


def test_live_quote_can_arrive_after_bar_polling_delay():
    probe = pending()
    output = probe.price(12, 16, now=datetime(2026, 10, 27, 9, 36, 7))
    assert output.orders and output.orders[0].kind == IntentKind.ENTRY


def test_signal_is_blocked_on_final_trading_day():
    probe = pending()
    assert not probe.price(12, 16, last_trading_day=date(2026, 10, 27)).orders


def test_gap_resets_history_and_cancels_late_pending_entry():
    probe = pending()
    assert not probe.price(12, 16, now=datetime(2026, 10, 27, 9, 42)).orders
    ctx = probe.ctx(12)
    from dataclasses import replace
    last = replace(ctx.bars[-1], time=ctx.bars[-1].time+timedelta(minutes=6))
    assert probe.strategy._today_bars(replace(ctx, bars=[*ctx.bars[:-1], last])) == [last]


def test_flatten_completes_only_after_actual_fill_and_retries_unprotected_remainder():
    probe = pending()
    held = Lot("2026-10-27-1", Side.BUY, 5, 16)
    now = datetime(2026,10,27,15,30)
    first = probe.price(12, 16, now=now, lots=[held])
    assert len(first.orders) == 1 and first.orders[0].kind == IntentKind.EXIT
    assert not probe.state["flatten_done"]
    # Rejected exit: no pending order and all quantity still held; retry is throttled.
    assert not probe.price(12, 16, now=now+timedelta(seconds=1), lots=[held]).orders
    retried = probe.price(12, 16, now=now+timedelta(seconds=6), lots=[held])
    assert len(retried.orders) == 1 and retried.orders[0].quantity == 5
    probe.price(12, 16, now=now+timedelta(seconds=7), lots=[])
    assert probe.state["flatten_done"]


def test_pending_exit_or_unknown_order_reserves_quantity_at_flatten():
    probe = pending()
    now = datetime(2026,10,27,15,30)
    held = Lot("2026-10-27-1", Side.BUY, 5, 16)
    order = OpenOrder("unknown-1", Side.SELL, 5, 0, IntentKind.EXIT, held.entry_id, now)
    assert not probe.price(12,16,now=now,lots=[held],open_orders=[order]).orders


def test_final_day_exit_is_not_duplicated_by_stop_check():
    probe = pending()
    held = Lot("2026-10-27-1", Side.BUY, 5, 16)
    output = probe.price(12, 9, lots=[held], last_trading_day=date(2026,10,27))
    assert len(output.orders) == 1 and output.orders[0].kind == IntentKind.EXIT
