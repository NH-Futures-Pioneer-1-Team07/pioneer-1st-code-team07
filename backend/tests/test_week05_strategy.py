import importlib.util
import json
from datetime import date, datetime, timedelta

from app.config import BACKEND_DIR
from app.runners.basis import attach_index
from strategy_base.manifest import Instrument, Manifest
from strategy_base.models import Bar, Context, DecisionResult, IntentKind, Lot, OpenOrder, Side

FOLDER = BACKEND_DIR / "strategies" / "week05_kospi200_basis_zscore"
START = datetime(2026, 11, 17, 9, 0)


def load(params=None):
    manifest = Manifest.model_validate(json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8")))
    spec = importlib.util.spec_from_file_location("week05_strategy", FOLDER / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Strategy({**manifest.default_params(), **(params or {})}), manifest


def bars(basis_values, start=START, spot=770.0):
    """베이시스 값마다 5분봉 하나. 선물 종가는 지수 + 베이시스다."""
    return [
        Bar(start + timedelta(minutes=5 * n), spot + b, spot + b, spot + b, 10, spot + b, reference=spot)
        for n, b in enumerate(basis_values)
    ]


# 베이시스가 -1.0과 1.0을 번갈아 나오는 22봉: 평균 0, 모표준편차 1
FLAT = [(-1.0 if n % 2 else 1.0) for n in range(22)]
PARAMS = {"window_bars": 20, "entry_z": 2.0}


def ctx(strategy, series, *, lots=(), open_orders=(), state=None, pnl=None, last_day=None):
    return Context(
        now=series[-1].time + timedelta(minutes=5),
        bars=series,
        params=strategy.params,
        lots=lots,
        open_orders=open_orders,
        state=state or {},
        margin=40_463_850,
        unrealized_pnl=pnl,
        last_trading_day=last_day,
    )


def test_manifest_and_defaults():
    _, manifest = load()
    assert manifest.default_params() == {"window_bars": 60, "entry_z": 1.5, "exit_return_pct": 10}
    assert manifest.instruments[0].index_code == "KRD020020016"
    assert manifest.override_problem({"window_bars": 5}) is not None
    assert manifest.override_problem({"entry_z": 0}) is not None
    assert manifest.override_problem({"exit_return_pct": 20, "entry_z": 1.5}) is None


def test_index_code_only_for_plain_domestic():
    base = {"name": "x", "code": "A", "index_code": "I"}
    assert Instrument.model_validate({**base, "market": "domestic"}).index_code == "I"
    try:
        Instrument.model_validate({**base, "market": "overseas", "exchange": "FCME"})
    except ValueError:
        return
    raise AssertionError("해외 종목에 index_code가 허용됨")


def test_attach_index_pairs_by_time():
    futures = bars([1.0, 2.0, 3.0])
    index = [Bar(futures[0].time, 1, 1, 770.0, 1), Bar(futures[2].time, 1, 1, 0.0, 1)]
    result = attach_index(
        [Bar(b.time, b.high, b.low, b.close, b.volume, b.open) for b in futures], index
    )
    assert [bar.reference for bar in result] == [770.0, None, None]
    assert [bar.close for bar in result] == [bar.close for bar in futures]


def test_buys_when_z_falls_below_negative_entry():
    strategy, _ = load(PARAMS)
    series = bars(FLAT + [-3.0])
    output = strategy.on_bar(ctx(strategy, series))
    order = output.orders[0]
    assert (order.side, order.quantity, order.kind) == (Side.BUY, 1, IntentKind.ENTRY)
    assert output.decisions[0].result == DecisionResult.BUY
    assert output.decisions[0].score == -3.0


def test_sells_when_z_rises_above_entry():
    strategy, _ = load(PARAMS)
    output = strategy.on_bar(ctx(strategy, bars(FLAT + [2.5])))
    assert output.orders[0].side == Side.SELL


def test_boundary_z_enters_and_inside_holds():
    strategy, _ = load(PARAMS)
    assert strategy.on_bar(ctx(strategy, bars(FLAT + [2.0]))).orders
    output = strategy.on_bar(ctx(strategy, bars(FLAT + [1.9])))
    assert not output.orders and output.decisions[0].result == DecisionResult.HOLD


def test_no_repeat_entry_while_previous_bar_already_outside():
    strategy, _ = load(PARAMS)
    output = strategy.on_bar(ctx(strategy, bars(FLAT + [3.0, 3.0])))
    assert not output.orders
    assert "돌파 아님" in output.decisions[0].reason


def test_skips_until_window_filled_and_when_std_zero():
    strategy, _ = load(PARAMS)
    output = strategy.on_bar(ctx(strategy, bars(FLAT[:10] + [5.0])))
    assert not output.orders and output.decisions[0].result == DecisionResult.SKIP
    output = strategy.on_bar(ctx(strategy, bars([1.0] * 22 + [5.0])))
    assert not output.orders and output.decisions[0].result == DecisionResult.SKIP


def test_bars_without_index_or_outside_signal_hours_are_ignored():
    strategy, _ = load(PARAMS)
    series = bars(FLAT + [-3.0])
    for n in range(5):
        series[n] = Bar(series[n].time, 1, 1, series[n].close, 10, reference=None)
    assert strategy.on_bar(ctx(strategy, series)).decisions[0].result == DecisionResult.SKIP  # 유효 봉 20개 미만
    late = bars(FLAT + [-3.0], start=datetime(2026, 11, 17, 13, 40))  # 마지막 봉이 15:20 이후
    assert not strategy.on_bar(ctx(strategy, late)).orders


def test_no_entry_on_last_trading_day_or_with_open_order():
    strategy, _ = load(PARAMS)
    series = bars(FLAT + [-3.0])
    assert not strategy.on_bar(ctx(strategy, series, last_day=date(2026, 11, 17))).orders
    pending = OpenOrder("1", Side.BUY, 1, 0, IntentKind.ENTRY, "e", series[-1].time)
    assert not strategy.on_bar(ctx(strategy, series, open_orders=[pending])).orders


def test_exits_at_profit_and_loss_threshold_for_both_sides():
    strategy, _ = load({**PARAMS, "exit_return_pct": 10})
    series = bars(FLAT + [0.0])
    margin = 40_463_850
    long_lot, short_lot = Lot("e", Side.BUY, 1, 770.0), Lot("e", Side.SELL, 1, 770.0)
    for lot, pnl, exit_side in [
        (long_lot, margin * 0.10, Side.SELL),
        (long_lot, -margin * 0.10, Side.SELL),
        (short_lot, margin * 0.10, Side.BUY),
        (short_lot, -margin * 0.10, Side.BUY),
    ]:
        output = strategy.on_bar(ctx(strategy, series, lots=[lot], pnl=pnl))
        assert [(o.side, o.kind, o.entry_id) for o in output.orders] == [(exit_side, IntentKind.EXIT, "e")]
        assert output.state["rearm_at"]


def test_holds_inside_threshold_and_uses_user_threshold():
    strategy, _ = load({**PARAMS, "exit_return_pct": 20})
    series = bars(FLAT + [0.0])
    lot = Lot("e", Side.BUY, 1, 770.0)
    assert not strategy.on_bar(ctx(strategy, series, lots=[lot], pnl=40_463_850 * 0.19)).orders
    assert strategy.on_bar(ctx(strategy, series, lots=[lot], pnl=40_463_850 * 0.20)).orders


def test_rearm_blocks_until_two_bars_after_exit():
    strategy, _ = load(PARAMS)
    series = bars(FLAT + [-3.0])
    after_exit = {"rearm_at": series[-2].time.isoformat()}  # 직전 봉이 청산 판단 이후에 시작함
    blocked = strategy.on_bar(ctx(strategy, series, state={"rearm_at": series[-1].time.isoformat()}))
    assert not blocked.orders and "재진입" in blocked.decisions[0].reason
    assert strategy.on_bar(ctx(strategy, series, state=after_exit)).orders


def test_describe_returns_sections():
    strategy, _ = load(PARAMS)
    sections = strategy.describe(ctx(strategy, bars(FLAT + [-3.0])))["sections"]
    assert sections[0]["tone"] == "buy"
    assert dict(sections[0]["rows"])["z-score"] == "-3.00"
