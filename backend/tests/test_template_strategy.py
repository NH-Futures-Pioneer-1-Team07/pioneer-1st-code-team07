from datetime import datetime

from app.config import BACKEND_DIR
from strategy_base.models import DecisionResult, IntentKind, Lot, Side
from strategy_base.registry import load_strategy
from strategy_base.testing import make_bars, run_on_bars

START = datetime(2026, 10, 27, 9, 0)


def build_strategy():
    registered = load_strategy(BACKEND_DIR / "strategies" / "_template")
    return registered.strategy_class(registered.manifest.default_params())


def test_템플릿_매니페스트와_전략이_등록_규칙을_통과한다():
    registered = load_strategy(BACKEND_DIR / "strategies" / "_template")

    assert registered.manifest.bar.size == 3


def test_종가가_직전_고가를_넘으면_매수_의도를_낸다():
    bars = make_bars([(10, 8, 9, 100), (12, 9, 11, 120)], START)

    steps = run_on_bars(build_strategy(), bars)

    assert not steps[0].output.orders
    second = steps[1].output
    assert [(o.side, o.quantity, o.kind, o.valid_bars) for o in second.orders] == [
        (Side.BUY, 1, IntentKind.ENTRY, 1)
    ]
    assert second.decisions[0].result == DecisionResult.BUY
    assert second.state == {"entry_count": 1}


def test_종가가_직전_고가_이하이면_보류한다():
    bars = make_bars([(10, 8, 9, 100), (10, 8, 10, 100)], START)

    output = run_on_bars(build_strategy(), bars)[1].output

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.HOLD


def test_보유_중이면_새_진입을_하지_않는다():
    bars = make_bars([(10, 8, 9, 100), (12, 9, 11, 120)], START)
    lots = [Lot("entry-1", Side.BUY, 1, 10.0)]

    steps = run_on_bars(build_strategy(), bars, lots=lots)

    assert not any(step.output.orders for step in steps)


def test_청산_시각이_되면_보유분을_전량_청산한다():
    bars = make_bars([(10, 8, 9, 100), (10, 8, 9, 100)], datetime(2026, 10, 27, 15, 24))
    lots = [Lot("entry-1", Side.BUY, 3, 10.0)]

    output = run_on_bars(build_strategy(), bars, lots=lots)[1].output

    assert [(o.side, o.quantity, o.kind, o.entry_id) for o in output.orders] == [
        (Side.SELL, 3, IntentKind.EXIT, "entry-1")
    ]
