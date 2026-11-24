import json
from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from app.config import BACKEND_DIR
from app.data.vix import VixHistory
from app.records.store import RunStore
from app.runners.backtest import Assumptions, BacktestEngine
from app.runners.inputs import ExtraInputs
from strategy_base.models import Context, DecisionResult, EntryFill, IntentKind, OpenOrder, OrderType, Side
from strategy_base.registry import StrategyRegistry
from tests.test_week03_strategy import FALLING, RISING, minute_bars

STRATEGY_ID = "week06_zn_intraday_average_entry"
NOW = datetime(2026, 11, 3, 11, 45)
TICK = 0.015625


@pytest.fixture
def registered():
    registry = StrategyRegistry(BACKEND_DIR / "strategies")
    assert not registry.errors
    return registry.strategies[STRATEGY_ID]


def context(strategy, side, close, *, fills=(), now=NOW):
    prior_close = close - TICK if side == Side.BUY else close + TICK
    return Context(
        now=now,
        bars=minute_bars([prior_close] * 20 + [close], start=now - timedelta(minutes=105)),
        params=strategy.params,
        series={"daily": RISING if side == Side.BUY else FALLING},
        vix=22,
        tick_size=TICK,
        entry_fills=fills,
    )


@pytest.mark.parametrize("side", [Side.BUY, Side.SELL])
def test_당일_같은_방향_체결이_없으면_첫_진입은_시장가(registered, side):
    strategy = registered.strategy_class(registered.manifest.default_params())
    other = Side.SELL if side == Side.BUY else Side.BUY
    ctx = context(strategy, side, 112.5, fills=[EntryFill(NOW, other, 1, 112.5)])

    [order] = strategy.on_bar(ctx).orders

    assert (order.kind, order.side, order.quantity, order.order_type) == (IntentKind.ENTRY, side, 1, OrderType.MARKET)
    assert order.limit_price is None and order.expires_at is None


@pytest.mark.parametrize(("side", "step"), [(Side.BUY, -TICK), (Side.SELL, TICK)])
def test_평단과_같거나_불리한_교차봉을_거르고_가장_가까운_유리한_호가를_쓴다(registered, side, step):
    strategy = registered.strategy_class(registered.manifest.default_params())
    fills = [EntryFill(NOW, side, 1, 112.5)]
    for close in (112.5, 112.5 - step):
        output = strategy.on_bar(context(strategy, side, close, fills=fills))
        assert not output.orders and output.decisions[0].result == DecisionResult.SKIP

    output = strategy.on_bar(context(strategy, side, 112.5 + step, fills=fills))
    [order] = output.orders
    assert (order.side, order.order_type, order.limit_price) == (side, OrderType.LIMIT, 112.5 + step)
    assert order.valid_bars == 1 and order.expires_at == NOW + timedelta(minutes=5)

    # 수량 가중 평단이 호가 사이에 있어도 같은 유리한 호가를 쓴다.
    fills = [EntryFill(NOW, side, 2, 112.5), EntryFill(NOW, side, 1, 112.5 + step)]
    output = strategy.on_bar(context(strategy, side, 112.5 + step, fills=fills))
    assert output.orders[0].limit_price == 112.5 + step
    assert output.decisions[0].detail["today"]["entry_average"] == pytest.approx(112.5 + step / 3)


def test_첫_진입_주문이_열려_있으면_시장가를_중복_제출하지_않는다(registered):
    strategy = registered.strategy_class(registered.manifest.default_params())
    ctx = context(strategy, Side.BUY, 112.5)
    pending = OpenOrder("1", Side.BUY, 1, 0, IntentKind.ENTRY, "entry", NOW)

    assert not strategy.on_bar(replace(ctx, open_orders=[pending])).orders


def test_자정을_넘는_교차봉의_추가_진입을_건너뛴다(registered):
    strategy = registered.strategy_class(registered.manifest.default_params())
    midnight = datetime(2026, 11, 4)
    ctx = context(strategy, Side.BUY, 112.5 - TICK, now=midnight, fills=[EntryFill(midnight, Side.BUY, 1, 112.5)])

    assert not strategy.on_bar(ctx).orders


def test_등록된_전략이_다음_봉에서_시장가_첫_진입과_지정가_추가_매수를_체결한다(registered, tmp_path):
    strategy = registered.strategy_class(registered.manifest.default_params())
    day = date(2026, 11, 3)
    recorder = RunStore(tmp_path).start_run(
        strategy_id=STRATEGY_ID,
        strategy_name=registered.manifest.name,
        mode="backtest",
        instrument={"name": "ZN", "code": "ZNZ26"},
        params=strategy.params,
        started_at=NOW,
    )
    engine = BacktestEngine(
        strategy,
        recorder,
        Assumptions(fee_rate=0.0, slippage_ticks=1, multiplier=1000, tick_size=TICK),
        initial_capital=100_000.0,
        minutes=5,
        last_trading_day=None,
        history_bars=20,
        history=minute_bars([112.0] * 20, start=datetime(2026, 11, 2, 21)),
        extras=ExtraInputs(series={"daily": RISING}, vix=VixHistory({date(2026, 11, 2): 22}), margin=2083),
    )
    bars = minute_bars([112 + TICK, 112 - TICK, 112 + 2 * TICK, 112 + 2 * TICK], start=datetime(2026, 11, 3, 9))
    bars[1] = replace(bars[1], open=112.125, high=112.125)
    bars[3] = replace(bars[3], open=112.25, high=112.25)

    engine.run({day: bars})

    rows = [
        json.loads(line)
        for journal in (recorder.folder / "journal").glob("*.jsonl")
        for line in journal.read_text(encoding="utf-8").splitlines()
    ]
    fills = [row for row in rows if row["kind"] == "fill" and row["intent"] == "entry"]
    assert [(fill["time"][11:19], fill["price"], fill["source"]) for fill in fills] == [
        ("09:05:00", 112.125 + TICK, "next_open"),
        ("09:19:59", 112.125, "limit_touch"),
    ]
