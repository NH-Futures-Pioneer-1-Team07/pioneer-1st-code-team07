from datetime import date, datetime, timedelta

from app.config import BACKEND_DIR
from strategy_base.models import (
    Bar,
    Context,
    DecisionResult,
    IntentKind,
    Lot,
    OpenOrder,
    Side,
)
from strategy_base.registry import load_strategy
from strategy_base.testing import make_bars, run_on_bars

STRATEGY_DIR = BACKEND_DIR / "strategies" / "week02_samsung_futures_intraday"
DAY = date(2026, 10, 27)
LAST_DAY = date(2026, 11, 12)

# 상승 추세 시나리오. 고점 14 → 17, 저점 7 → 8로 모두 높아지고, 마지막 봉이 기준 고점 17을 종가로 돌파한다.
# (고가, 저가, 종가, 거래량)
UP_ROWS = [
    (10, 8, 9, 100),
    (11, 9, 10, 100),
    (14, 10, 13, 100),
    (12, 9, 10, 100),
    (11, 7, 8, 100),
    (12, 8, 11, 100),
    (13, 9, 12, 100),
    (17, 11, 16, 100),
    (15, 10, 12, 100),
    (13, 8, 9, 100),
    (14, 9, 13, 100),
    (15, 10, 14, 100),
    (16, 12, 15, 100),
    (19, 14, 18, 250),
]


def mirror(rows, center=40):
    """위아래를 뒤집어 하락 추세 시나리오로 만든다."""
    return [(center - low, center - high, center - close, volume) for high, low, close, volume in rows]


def build(params=None):
    registered = load_strategy(STRATEGY_DIR)
    values = {**registered.manifest.default_params(), **(params or {})}
    return registered.strategy_class(values)


def bars_at(rows, start=datetime(2026, 10, 27, 9, 0)):
    return make_bars(rows, start)


def run_last(rows, start=datetime(2026, 10, 27, 9, 0), **kwargs):
    kwargs.setdefault("last_trading_day", LAST_DAY)
    params = kwargs.pop("params", None)
    return run_on_bars(build(params), bars_at(rows, start), **kwargs)[-1].output


def make_ctx(strategy, bars, now, **kwargs):
    kwargs.setdefault("last_trading_day", LAST_DAY)
    return Context(now=now, bars=bars, params=strategy.params, **kwargs)


def lot(entry_id, side, quantity):
    return Lot(entry_id, side, quantity, 10.0)


def exit_order(order_id, side, quantity, filled=0, entry_id="a"):
    return OpenOrder(order_id, side, quantity, filled, IntentKind.EXIT, entry_id, datetime(2026, 10, 27, 15, 20))


def entry_order(order_id, side, quantity):
    return OpenOrder(order_id, side, quantity, 0, IntentKind.ENTRY, "x", datetime(2026, 10, 27, 15, 20))


def summarize(output):
    return [(o.side, o.quantity, o.kind, o.entry_id) for o in output.orders]


def test_매니페스트의_파라미터가_전략_문서의_이름과_기본값이다():
    manifest = load_strategy(STRATEGY_DIR).manifest

    assert manifest.default_params() == {
        "bar_minutes": 3,
        "swing_side_bars": 2,
        "trend_compare_count": 2,
        "volume_avg_bars": 10,
        "quantity_factor": 5,
        "order_valid_bars": 1,
        "entry_cutoff_time": "15:24",
        "flatten_time": "15:30",
    }
    assert manifest.instruments[0].code == "A116B000"


# ---- 신호 ----


def test_상승_추세에서_기준_고점을_종가로_돌파하면_매수한다():
    output = run_last(UP_ROWS)

    assert len(output.orders) == 1
    order = output.orders[0]
    assert (order.side, order.kind, order.valid_bars) == (Side.BUY, IntentKind.ENTRY, 1)
    assert order.quantity == 12  # floor(5 × 250 / 100) = floor(12.5)
    assert output.decisions[0].result == DecisionResult.BUY
    assert output.decisions[0].detail["reference_high"] == 17


def test_하락_추세에서_기준_저점을_종가로_돌파하면_매도한다():
    output = run_last(mirror(UP_ROWS))

    assert [(o.side, o.quantity) for o in output.orders] == [(Side.SELL, 12)]
    assert output.decisions[0].detail["reference_low"] == 23


def test_돌파_직전_봉_종가가_기준_고점_초과이면_신호가_아니다():
    rows = list(UP_ROWS)
    rows[-2] = (16, 12, 18, 100)  # 직전 봉 종가가 이미 기준 고점 17 위

    output = run_last(rows)

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.HOLD


def test_종가가_기준_고점과_같으면_돌파가_아니다():
    rows = list(UP_ROWS)
    rows[-1] = (19, 14, 17, 250)

    assert not run_last(rows).orders


def test_기준_위에_계속_머무는_다음_봉은_다시_주문하지_않는다():
    rows = UP_ROWS + [(20, 17, 19, 250)]

    steps = run_on_bars(build(), bars_at(rows), last_trading_day=LAST_DAY)

    assert [bool(step.output.orders) for step in steps].count(True) == 1
    assert not steps[-1].output.orders


def test_고점과_저점의_방향이_엇갈리면_추세_판단을_보류한다():
    rows = list(UP_ROWS)
    rows[9] = (13, 6, 9, 100)  # 두 번째 저점이 7에서 6으로 낮아져 저점은 하락, 고점은 상승

    output = run_last(rows)

    assert not output.orders
    assert output.decisions[0].reason == "추세 판단 보류"


def test_확정된_고점이나_저점이_2개보다_적으면_추세_판단을_보류한다():
    output = run_last(UP_ROWS[:6])

    assert not output.orders
    assert output.decisions[0].reason == "추세 판단 보류"


def test_추세_확인_뒤의_돌파만_신호다():
    # 같은 봉 마감에서 추세가 확인되고 돌파도 일어나면 신호다. 추세 확인 전 돌파는 신호가 아니다.
    steps = run_on_bars(build(), bars_at(UP_ROWS), last_trading_day=LAST_DAY)

    assert not any(step.output.orders for step in steps[:-1])
    assert steps[-1].output.orders


def test_전일_봉은_신호_계산에_쓰지_않는다():
    yesterday = datetime(2026, 10, 26, 9, 0)
    old = make_bars(UP_ROWS[:11], yesterday)
    today = make_bars(UP_ROWS[11:], datetime(2026, 10, 27, 9, 0))
    strategy = build()
    ctx = make_ctx(strategy, old + today, datetime(2026, 10, 27, 9, 9))

    output = strategy.on_bar(ctx)

    assert not output.orders


# ---- 수량 ----


def test_수량은_소수점을_버린다():
    rows = UP_ROWS[:-1] + [(19, 14, 18, 239)]  # 5 × 239 / 100 = 11.95

    assert run_last(rows).orders[0].quantity == 11


def test_계산_수량이_0이면_주문하지_않는다():
    rows = UP_ROWS[:-1] + [(19, 14, 18, 19)]  # 5 × 19 / 100 = 0.95

    output = run_last(rows)

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP
    assert output.decisions[0].reason == "계산된 수량이 0"


def test_직전_봉이_평균_개수보다_적으면_건너뛴다():
    output = run_last(UP_ROWS, params={"volume_avg_bars": 14})

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP


def test_평균_거래량이_0이면_건너뛴다():
    rows = [(h, l, c, 0) for h, l, c, _ in UP_ROWS[:-1]] + [UP_ROWS[-1]]

    output = run_last(rows)

    assert not output.orders
    assert output.decisions[0].reason == "평균 거래량이 0"


def test_신호_봉은_평균_거래량에서_제외한다():
    rows = UP_ROWS[:-1] + [(19, 14, 18, 1000)]

    assert run_last(rows).orders[0].quantity == 50  # 평균은 신호 봉을 뺀 100


def test_이전_주문이_미체결이면_새_신호를_건너뛴다():
    output = run_last(UP_ROWS, open_orders=[entry_order("o1", Side.BUY, 3)])

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP


def test_보유_중_같은_방향_신호는_계산한_수량만큼_추가한다():
    output = run_last(UP_ROWS, lots=[lot("a", Side.BUY, 4)])

    assert [(o.side, o.quantity, o.kind) for o in output.orders] == [(Side.BUY, 12, IntentKind.ENTRY)]


def test_진입마다_진입분_id가_늘어난다():
    strategy = build()
    bars = bars_at(UP_ROWS)
    first = strategy.on_bar(make_ctx(strategy, bars, bars[-1].time + timedelta(minutes=3)))
    second = strategy.on_bar(
        make_ctx(strategy, bars, bars[-1].time + timedelta(minutes=3), state=first.state)
    )

    assert first.orders[0].entry_id == "2026-10-27-1"
    assert second.orders[0].entry_id == "2026-10-27-2"


# ---- 반대 신호와 포지션 전환 ----

SELL_ROWS = mirror(UP_ROWS)


def sell_rows_with_volume(volume):
    return SELL_ROWS[:-1] + [(*SELL_ROWS[-1][:3], volume)]


def test_반대_신호가_보유량보다_작으면_일부_청산한다():
    output = run_last(sell_rows_with_volume(100), lots=[lot("a", Side.BUY, 10)])  # 수량 5

    assert summarize(output) == [(Side.SELL, 5, IntentKind.EXIT, "a")]
    assert output.state is None or not output.state.get("pending_flip")


def test_반대_신호가_보유량과_같으면_전량_청산한다():
    output = run_last(sell_rows_with_volume(200), lots=[lot("a", Side.BUY, 10)])  # 수량 10

    assert summarize(output) == [(Side.SELL, 10, IntentKind.EXIT, "a")]


def test_반대_신호_청산은_오래된_진입분부터다():
    output = run_last(
        sell_rows_with_volume(140),  # 수량 7
        lots=[lot("a", Side.BUY, 4), lot("b", Side.BUY, 6)],
    )

    assert summarize(output) == [(Side.SELL, 4, IntentKind.EXIT, "a"), (Side.SELL, 3, IntentKind.EXIT, "b")]


def test_반대_신호가_보유량보다_크면_전량_청산하고_초과분은_청산_뒤에_진입한다():
    strategy = build()
    bars = bars_at(sell_rows_with_volume(300))  # 수량 15
    now = bars[-1].time + timedelta(minutes=3)

    first = strategy.on_bar(make_ctx(strategy, bars, now, lots=[lot("a", Side.BUY, 10)]))

    assert [(o.side, o.quantity, o.kind) for o in first.orders] == [(Side.SELL, 10, IntentKind.EXIT)]
    assert first.state["pending_flip"]["quantity"] == 5

    # 청산이 끝나기 전에는 초과분을 진입하지 않는다.
    waiting = strategy.on_price(
        make_ctx(strategy, bars, now + timedelta(seconds=30), lots=[lot("a", Side.BUY, 3)], state=first.state)
    )
    assert not waiting.orders

    # 청산이 끝나면 기한 안에서 초과분만 반대 방향으로 진입한다.
    entered = strategy.on_price(
        make_ctx(strategy, bars, now + timedelta(minutes=1), state=first.state)
    )
    assert [(o.side, o.quantity, o.kind, o.valid_bars) for o in entered.orders] == [
        (Side.SELL, 5, IntentKind.ENTRY, 1)
    ]
    assert not entered.state["pending_flip"]


def test_초과분_진입_기한이_지나면_진입하지_않는다():
    strategy = build()
    bars = bars_at(sell_rows_with_volume(300))
    now = bars[-1].time + timedelta(minutes=3)
    first = strategy.on_bar(make_ctx(strategy, bars, now, lots=[lot("a", Side.BUY, 10)]))

    late = strategy.on_price(make_ctx(strategy, bars, now + timedelta(minutes=3), state=first.state))

    assert not late.orders
    assert not late.state["pending_flip"]
    assert late.decisions[0].result == DecisionResult.SKIP


def test_전략_문서의_포지션_전환_예시를_따른다():
    # 매수 10계약 보유 중 매도 신호 5, 7, 5계약이 모두 체결되면 매수 5 → 매도 2 → 매도 7
    strategy = build()
    bars5 = bars_at(sell_rows_with_volume(100))
    bars7 = bars_at(sell_rows_with_volume(140))
    now = bars5[-1].time + timedelta(minutes=3)

    first = strategy.on_bar(make_ctx(strategy, bars5, now, lots=[lot("a", Side.BUY, 10)]))
    assert summarize(first) == [(Side.SELL, 5, IntentKind.EXIT, "a")]

    second = strategy.on_bar(make_ctx(strategy, bars7, now, lots=[lot("a", Side.BUY, 5)]))
    assert summarize(second) == [(Side.SELL, 5, IntentKind.EXIT, "a")]
    assert second.state["pending_flip"]["quantity"] == 2

    entered = strategy.on_price(
        make_ctx(strategy, bars7, now + timedelta(minutes=1), state=second.state)
    )
    assert [(o.side, o.quantity) for o in entered.orders] == [(Side.SELL, 2)]

    third = strategy.on_bar(make_ctx(strategy, bars5, now, lots=[lot("n", Side.SELL, 2)]))
    assert [(o.side, o.quantity, o.kind) for o in third.orders] == [(Side.SELL, 5, IntentKind.ENTRY)]


# ---- 시각·날짜 규칙 ----

# 신호 봉이 15:24에 마감되는 시나리오 (봉 14개 × 3분, 14:42 시작)
CUTOFF_START = datetime(2026, 10, 27, 14, 42)


def test_신규_진입_제한_시각_이후에는_신규_진입을_하지_않는다():
    output = run_last(UP_ROWS, start=CUTOFF_START)

    assert not output.orders
    skips = [d for d in output.decisions if d.result == DecisionResult.SKIP]
    assert skips and "신규 진입" in skips[0].reason


def test_신규_진입_제한_시각_이후에도_보유분을_줄이는_반대_거래는_한다():
    output = run_last(sell_rows_with_volume(100), start=CUTOFF_START, lots=[lot("a", Side.BUY, 10)])

    assert summarize(output) == [(Side.SELL, 5, IntentKind.EXIT, "a")]


def test_신규_진입_제한_시각_이후에는_반대_거래의_초과분으로_새_포지션을_열지_않는다():
    output = run_last(sell_rows_with_volume(300), start=CUTOFF_START, lots=[lot("a", Side.BUY, 10)])

    assert summarize(output) == [(Side.SELL, 10, IntentKind.EXIT, "a")]
    assert not (output.state or {}).get("pending_flip")


def test_신규_진입_제한_시각에_장중_미체결_주문을_취소하고_청산_주문의_남은_수량을_이어간다():
    strategy = build()
    bars = bars_at(UP_ROWS[:2], start=datetime(2026, 10, 27, 15, 21))
    now = datetime(2026, 10, 27, 15, 24)
    ctx = make_ctx(
        strategy,
        bars,
        now,
        lots=[lot("a", Side.BUY, 6)],
        open_orders=[exit_order("o1", Side.SELL, 8, filled=2), entry_order("o2", Side.BUY, 3)],
    )

    output = strategy.on_price(ctx)

    assert [c.order_id for c in output.cancels] == ["o1", "o2"]
    assert summarize(output) == [(Side.SELL, 6, IntentKind.EXIT, "a")]
    assert output.state["cutoff_done"]


def test_신규_진입_제한_시각의_취소는_하루_한_번만_한다():
    strategy = build()
    bars = bars_at(UP_ROWS[:2], start=datetime(2026, 10, 27, 15, 21))
    first = strategy.on_price(
        make_ctx(strategy, bars, datetime(2026, 10, 27, 15, 24), open_orders=[entry_order("o2", Side.BUY, 3)])
    )

    second = strategy.on_price(
        make_ctx(
            strategy,
            bars,
            datetime(2026, 10, 27, 15, 25),
            open_orders=[entry_order("o3", Side.BUY, 1)],
            state=first.state,
        )
    )

    assert first.cancels
    assert not second.cancels


def test_당일_청산_시각에_미체결_주문을_취소하고_보유분을_전량_시장가로_청산한다():
    strategy = build()
    bars = bars_at(UP_ROWS[:2], start=datetime(2026, 10, 27, 15, 24))
    now = datetime(2026, 10, 27, 15, 30)
    ctx = make_ctx(
        strategy,
        bars,
        now,
        lots=[lot("a", Side.BUY, 6), lot("b", Side.SELL, 2)],
        open_orders=[exit_order("o1", Side.SELL, 3)],
    )

    output = strategy.on_price(ctx)

    assert [c.order_id for c in output.cancels] == ["o1"]
    assert summarize(output) == [
        (Side.SELL, 6, IntentKind.EXIT, "a"),
        (Side.BUY, 2, IntentKind.EXIT, "b"),
    ]
    assert all(o.valid_bars is None for o in output.orders)
    assert output.state["flatten_done"]


def test_당일_청산은_거래량_조건과_무관하게_하고_하루_한_번만_한다():
    strategy = build()
    bars = bars_at([(10, 9, 9, 0)] * 3, start=datetime(2026, 10, 27, 15, 21))
    first = strategy.on_bar(
        make_ctx(strategy, bars, datetime(2026, 10, 27, 15, 30), lots=[lot("a", Side.BUY, 6)])
    )

    second = strategy.on_bar(
        make_ctx(
            strategy,
            bars,
            datetime(2026, 10, 27, 15, 33),
            lots=[lot("a", Side.BUY, 6)],
            state=first.state,
        )
    )

    assert summarize(first) == [(Side.SELL, 6, IntentKind.EXIT, "a")]
    assert not second.orders
    assert second.decisions[0].result == DecisionResult.SKIP


def test_최종거래일에는_신규_진입을_하지_않는다():
    output = run_last(UP_ROWS, last_trading_day=DAY)

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP


def test_최종거래일을_확인하지_못하면_신규_진입을_하지_않는다():
    output = run_last(UP_ROWS, last_trading_day=None)

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP


def test_최종거래일에_보유한_포지션은_청산을_시도한다():
    steps = run_on_bars(build(), bars_at(UP_ROWS), last_trading_day=DAY, lots=[lot("a", Side.BUY, 6)])

    assert summarize(steps[0].output) == [(Side.SELL, 6, IntentKind.EXIT, "a")]
    assert steps[0].output.state["final_exit_done"]
    assert not any(step.output.orders for step in steps[1:])


def test_최종거래일_청산은_이미_청산_주문이_있는_진입분은_건너뛴다():
    steps = run_on_bars(
        build(),
        bars_at(UP_ROWS),
        last_trading_day=DAY,
        lots=[lot("a", Side.BUY, 6), lot("b", Side.BUY, 2)],
        open_orders=[exit_order("o1", Side.SELL, 6, entry_id="a")],
    )

    assert summarize(steps[0].output) == [(Side.SELL, 2, IntentKind.EXIT, "b")]


def test_파라미터를_바꾸면_동작에_반영된다():
    assert run_last(UP_ROWS).orders
    assert not run_last(UP_ROWS, params={"swing_side_bars": 3}).orders
