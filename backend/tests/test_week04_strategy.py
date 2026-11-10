import importlib.util
import json
from datetime import datetime, timedelta

import pytest

from app.config import BACKEND_DIR
from strategy_base.manifest import Manifest
from strategy_base.models import Bar, Context, DecisionResult, IntentKind, Lot, OpenOrder, Side
from strategy_base.registry import StrategyRegistry

FOLDER = BACKEND_DIR / "strategies" / "week04_zf_zn_spread"
DAY = datetime(2026, 11, 11)


def load(params=None):
    manifest = Manifest.model_validate(json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8")))
    spec = importlib.util.spec_from_file_location("week04_strategy", FOLDER / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Strategy({**manifest.default_params(), **(params or {})}), manifest


def daily(values):
    start = datetime(2026, 9, 1)
    return [Bar(start + timedelta(days=n), v, v, v, 100, v) for n, v in enumerate(values)]


def minute_bars(values, start=datetime(2026, 11, 11, 9, 0)):
    return [Bar(start + timedelta(minutes=5 * n), v, v, v, 10, v) for n, v in enumerate(values)]


# 일봉 40개: 100.0, 100.1, ... 103.9 (최저 100.0, 최고 103.9, 중앙값 101.95)
DAILY = daily([100 + n / 10 for n in range(40)])


def ctx(strategy, bars, daily_bars=DAILY, *, lots=(), open_orders=(), state=None):
    return Context(
        now=bars[-1].time + timedelta(minutes=5),
        bars=bars,
        params=strategy.params,
        lots=lots,
        open_orders=open_orders,
        state=state or {},
        series={"daily": daily_bars},
    )


def lot(side):
    return Lot("e-1", side, 1, 101.0)


def test_manifest_and_defaults():
    strategy, manifest = load()
    assert manifest.default_params() == {"window_days": 40, "entry_pct": 0, "exit_buffer_ratio": 0.001}
    assert manifest.instruments[0].legs[1].ratio == -2
    assert manifest.override_problem({"window_days": 4}) is not None
    assert manifest.override_problem({"entry_pct": 0.5}) is not None
    assert manifest.override_problem({"entry_pct": 0.05, "window_days": 60}) is None


def test_registry_accepts_strategy():
    registry = StrategyRegistry(BACKEND_DIR / "strategies")
    registry.scan()
    assert registry.get("week04_zf_zn_spread") is not None


def test_breakout_above_upper_sells_spread():
    strategy, _ = load()
    output = strategy.on_bar(ctx(strategy, minute_bars([102.0, 104.0])))
    order = output.orders[0]
    assert (order.side, order.quantity, order.kind) == (Side.SELL, 1, IntentKind.ENTRY)
    assert output.decisions[0].result == DecisionResult.SELL
    assert output.decisions[0].detail["band"]["entry_upper"] == pytest.approx(103.9)


def test_breakout_below_lower_buys_spread():
    strategy, _ = load()
    output = strategy.on_bar(ctx(strategy, minute_bars([102.0, 99.9])))
    assert output.orders[0].side == Side.BUY


def test_already_outside_band_does_not_enter():
    strategy, _ = load()
    output = strategy.on_bar(ctx(strategy, minute_bars([104.5, 105.0])))
    assert not output.orders
    assert output.decisions[0].result == DecisionResult.HOLD


def test_inside_band_holds():
    strategy, _ = load()
    output = strategy.on_bar(ctx(strategy, minute_bars([102.0, 102.5])))
    assert not output.orders


def test_first_bar_of_day_has_no_previous_bar():
    strategy, _ = load()
    assert not strategy.on_bar(ctx(strategy, minute_bars([104.0]))).orders


def test_gap_between_bars_blocks_entry():
    strategy, _ = load()
    bars = minute_bars([102.0]) + minute_bars([104.0], start=datetime(2026, 11, 11, 9, 20))
    assert not strategy.on_bar(ctx(strategy, bars)).orders


def test_previous_day_bar_is_not_a_previous_bar():
    strategy, _ = load()
    bars = minute_bars([102.0], start=datetime(2026, 11, 10, 23, 55)) + minute_bars([104.0], start=datetime(2026, 11, 11, 0, 0))
    assert not strategy.on_bar(ctx(strategy, bars)).orders


def test_short_daily_history_skips():
    strategy, _ = load()
    output = strategy.on_bar(ctx(strategy, minute_bars([102.0, 104.0]), DAILY[:39]))
    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP


def test_entry_pct_uses_interpolated_quantile():
    strategy, _ = load({"entry_pct": 0.05})
    output = strategy.on_bar(ctx(strategy, minute_bars([102.0, 103.8])))
    # 40개의 상위 5% 분위수: 위치 0.95 * 39 = 37.05 -> 103.7 + 0.005
    assert output.decisions[0].detail["band"]["entry_upper"] == pytest.approx(103.705)
    assert output.orders[0].side == Side.SELL


def test_exit_band_around_median():
    strategy, _ = load({"exit_buffer_ratio": 0.01})
    band = strategy.on_bar(ctx(strategy, minute_bars([102.0, 102.1]))).decisions[0].detail["band"]
    assert band["median"] == pytest.approx(101.95)
    assert band["exit_upper"] == pytest.approx(101.95 * 1.01)
    assert band["exit_lower"] == pytest.approx(101.95 * 0.99)


def test_exit_short_spread_when_back_at_or_below_exit_upper():
    strategy, _ = load()
    held = [lot(Side.SELL)]
    stay = strategy.on_bar(ctx(strategy, minute_bars([104.0, 103.0]), lots=held))
    assert not stay.orders
    leave = strategy.on_bar(ctx(strategy, minute_bars([103.0, 102.0]), lots=held))
    assert leave.orders[0].side == Side.BUY
    assert leave.orders[0].kind == IntentKind.EXIT
    assert leave.state["rearm_at"] == (minute_bars([103.0, 102.0])[-1].time + timedelta(minutes=5)).isoformat()


def test_exit_long_spread_when_back_at_or_above_exit_lower():
    strategy, _ = load()
    held = [lot(Side.BUY)]
    assert not strategy.on_bar(ctx(strategy, minute_bars([100.0, 101.0]), lots=held)).orders
    leave = strategy.on_bar(ctx(strategy, minute_bars([101.0, 102.0]), lots=held))
    assert leave.orders[0].side == Side.SELL


def test_no_loss_stop():
    strategy, _ = load()
    output = strategy.on_bar(ctx(strategy, minute_bars([110.0, 115.0]), lots=[lot(Side.SELL)]))
    assert not output.orders


def test_open_order_blocks_new_entry():
    strategy, _ = load()
    pending = OpenOrder("1", Side.SELL, 1, 0, IntentKind.ENTRY, "e", DAY)
    output = strategy.on_bar(ctx(strategy, minute_bars([102.0, 104.0]), open_orders=[pending]))
    assert not output.orders


def test_reentry_needs_two_bars_after_exit():
    strategy, _ = load()
    exit_at = minute_bars([0.0] * 3)[-1].time + timedelta(minutes=5)  # 세 번째 봉이 마감된 시각
    state = {"rearm_at": exit_at.isoformat(), "sequence": 1}
    # 청산 판단 봉(세 번째)이 직전 봉이면 막힌다.
    blocked = strategy.on_bar(ctx(strategy, minute_bars([102.0, 102.0, 102.0, 104.0]), state=state))
    assert not blocked.orders
    # 청산 후 시작한 봉이 직전 봉이면 허용된다.
    allowed = strategy.on_bar(ctx(strategy, minute_bars([102.0, 102.0, 102.0, 102.0, 104.0]), state=state))
    assert allowed.orders[0].entry_id == "2026-11-11-2"


def test_describe_has_band_and_position():
    strategy, _ = load()
    sections = strategy.describe(ctx(strategy, minute_bars([102.0, 104.0])))["sections"]
    assert [s["title"] for s in sections] == ["밴드 (일봉 스프레드)", "현재 스프레드 (5분봉)", "보유"]
    assert sections[1]["headline"] == "진입 상단 위"
    short = strategy.describe(ctx(strategy, minute_bars([102.0, 104.0]), DAILY[:10]))["sections"][0]
    assert short["rows"][0][0] == "상태"
