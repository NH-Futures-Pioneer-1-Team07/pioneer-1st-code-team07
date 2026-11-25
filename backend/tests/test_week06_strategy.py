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


def described(registered, ctx):
    sections = registered.strategy_class(ctx.params).describe(ctx)["sections"]
    assert [s["title"] for s in sections] == ["중기 판단 (일봉)", "장중 판단 (5분봉)", "평단 판단 (당일)", "오늘 진입·보유"]
    assert not any("평단" in name for name, _ in sections[3]["rows"])
    section = sections[2]
    return section["headline"], section["tone"], dict(section["rows"])


@pytest.mark.parametrize(
    ("side", "ticks", "headline", "condition"),
    [
        (Side.BUY, -1, "평단보다 낮음", "충족"),
        (Side.BUY, 0, "평단과 같음", "미충족"),
        (Side.BUY, 1, "평단보다 높음", "미충족"),
        (Side.SELL, 1, "평단보다 높음", "충족"),
        (Side.SELL, 0, "평단과 같음", "미충족"),
        (Side.SELL, -1, "평단보다 낮음", "미충족"),
    ],
)
def test_판단_화면은_현재_가격이_당일_평단보다_유리한지_보여준다(registered, side, ticks, headline, condition):
    strategy = registered.strategy_class(registered.manifest.default_params())
    ctx = context(strategy, side, 112.5, fills=[EntryFill(NOW, side, 1, 112.5)])

    shown, tone, rows = described(registered, replace(ctx, price=112.5 + ticks * TICK))

    label = "매수" if side == Side.BUY else "매도"
    assert shown == headline and tone == (side.value if condition == "충족" else "neutral")
    assert rows[f"당일 {label} 평단"] == "112.5000" and rows[f"추가 {label} 조건"] == condition
    assert rows["평단과의 차이"] == f"{ticks * TICK:+.4f}" and rows["실제 판정"] == "교차봉 종가 기준"


def test_판단_화면은_첫_진입_전과_가격이_없을_때와_중립을_구분한다(registered):
    strategy = registered.strategy_class(registered.manifest.default_params())
    ctx = replace(context(strategy, Side.BUY, 112.5), price=112.25)

    headline, tone, rows = described(registered, ctx)
    assert (headline, tone, rows["당일 매수 평단"], rows["추가 매수 조건"]) == ("첫 진입 전", "neutral", "—", "없음 (시장가)")

    bought = replace(ctx, entry_fills=[EntryFill(NOW, Side.BUY, 1, 112.5)])
    headline, _, rows = described(registered, replace(bought, price=None))
    assert (headline, rows["현재 가격"], rows["추가 매수 조건"]) == ("현재 가격 대기", "—", "—")

    # 직전 거래일 종가가 이동평균 사이에 있으면 중립이다.
    neutral = [*RISING[:-1], replace(RISING[-1], close=RISING[-10].close)]
    headline, tone, rows = described(registered, replace(bought, series={"daily": neutral}))
    assert (headline, tone, rows["당일 매수 평단"], rows["당일 매도 평단"]) == ("진입 안 함", "neutral", "112.5000", "—")

    headline, _, _ = described(registered, replace(bought, series={"daily": []}))
    assert headline == "계산 불가"
