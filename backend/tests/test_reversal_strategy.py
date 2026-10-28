from datetime import date, datetime, timedelta

from app.config import BACKEND_DIR
from strategy_base.models import Context, DecisionResult, IntentKind, Lot, OpenOrder, Side
from strategy_base.registry import load_strategy
from strategy_base.testing import make_bars

STRATEGY_DIR = BACKEND_DIR / "strategies" / "week02_samsung_futures_reversal"
START = datetime(2026, 10, 27, 9, 0)
LAST_DAY = date(2026, 11, 12)

# (고가, 저가, 종가, 거래량)
# 인덱스 4가 저점 12, 인덱스 2가 고점 24(둘 다 후보 봉 시작 전에 확정).
# 인덱스 10이 저점 12를 깼다가 14로 회복한 매수 후보 봉, 11이 종가 16으로 기준 저점 12 위에서 마감한 확인 봉이다.
BUY_ROWS = [
    (20, 18, 19, 100),
    (21, 17, 20, 100),
    (24, 16, 22, 100),
    (22, 15, 18, 100),
    (20, 12, 15, 100),
    (19, 13, 17, 100),
    (21, 14, 19, 100),
    (22, 15, 20, 100),
    (23, 16, 21, 100),
    (22, 17, 20, 100),
    (21, 11, 14, 100),
    (18, 13, 16, 80),
]
# 진입 뒤 인덱스 13에서 새 고점 26이 만들어지고 15에서 확정된다.
AFTER_ENTRY = [(22, 18, 20, 100), (26, 19, 25, 100), (24, 20, 22, 100), (23, 19, 21, 100)]


def mirror(rows, center=40):
    return [(center - low, center - high, center - close, volume) for high, low, close, volume in rows]


def with_row(rows, index, row):
    rows = list(rows)
    rows[index] = row
    return rows


def build(**params):
    registered = load_strategy(STRATEGY_DIR)
    values = {**registered.manifest.default_params(), "stop_offset": 2, **params}
    return registered.strategy_class(values)


class Run:
    """봉을 하나씩 마감시키며 전략을 호출하고 상태를 이어 준다."""

    def __init__(self, strategy, rows, start=START, **ctx_kwargs):
        self.strategy = strategy
        self.bars = make_bars(rows, start)
        self.state = {}
        self.ctx_kwargs = {"last_trading_day": LAST_DAY, **ctx_kwargs}

    def ctx(self, count, **overrides):
        kwargs = {**self.ctx_kwargs, **overrides}
        now = overrides.pop("now", None) or self.bars[count - 1].time + timedelta(minutes=3)
        kwargs.pop("now", None)
        return Context(now=now, bars=self.bars[:count], params=self.strategy.params, state=self.state, **kwargs)

    def bar(self, count, **overrides):
        output = self.strategy.on_bar(self.ctx(count, **overrides))
        self._keep(output)
        return output

    def price(self, count, price, **overrides):
        output = self.strategy.on_price(self.ctx(count, price=price, **overrides))
        self._keep(output)
        return output

    def through(self, count):
        outputs = [self.bar(n) for n in range(1, count + 1)]
        return outputs

    def _keep(self, output):
        if output.state is not None:
            self.state = output.state


def lot(entry_id, side, quantity=5, price=16.0):
    return Lot(entry_id, side, quantity, price)


def open_order(order_id, side, quantity, kind, entry_id, filled=0, hour=15, minute=20):
    return OpenOrder(order_id, side, quantity, filled, kind, entry_id, datetime(2026, 10, 27, hour, minute))


def summarize(output):
    return [(o.side, o.quantity, o.kind, o.entry_id) for o in output.orders]


def entered(rows=BUY_ROWS, **params):
    """확인 봉까지 진행해 진입 주문을 낸 상태를 만든다."""
    run = Run(build(**params), rows)
    outputs = run.through(len(rows))
    return run, outputs[-1]


ENTRY_ID = "2026-10-27-1"


def test_매니페스트의_파라미터가_전략_문서의_이름과_기본값이다():
    manifest = load_strategy(STRATEGY_DIR).manifest

    assert manifest.default_params() == {
        "bar_minutes": 3,
        "swing_side_bars": 2,
        "volume_avg_bars": 10,
        "volume_min_ratio": 0.5,
        "entry_quantity": 5,
        "stop_offset": 1500,
        "order_valid_bars": 1,
        "target_mode": "갱신",
        "entry_cutoff_time": "15:24",
        "flatten_time": "15:30",
    }
    assert manifest.instruments[0].code == "A116B000"


def test_목표_관리_방식이_잘못되면_만들_수_없다():
    import pytest

    with pytest.raises(ValueError):
        build(target_mode="없음")


# ---- 신호 ----


def test_후보_봉에서는_주문하지_않고_다음_봉에서_확인한다():
    run = Run(build(), BUY_ROWS)
    outputs = run.through(len(BUY_ROWS))

    assert not any(output.orders for output in outputs[:-1])
    assert outputs[10].decisions[0].result == DecisionResult.HOLD
    assert "후보" in outputs[10].decisions[0].reason


def test_저점을_깼다가_기준_저점_위에서_확인되면_고정_5계약을_매수한다():
    run, output = entered()

    assert [(o.side, o.quantity, o.kind, o.valid_bars) for o in output.orders] == [
        (Side.BUY, 5, IntentKind.ENTRY, 1)
    ]
    assert DecisionResult.BUY in [d.result for d in output.decisions]
    position = run.state["positions"][ENTRY_ID]
    assert (position["stop"], position["target"]) == (10, 24)  # 기준 저점 12 − 2, 반대쪽 확정 고점 24


def test_고점을_넘었다가_기준_고점_아래에서_확인되면_매도한다():
    run, output = entered(mirror(BUY_ROWS))

    assert [(o.side, o.quantity, o.kind) for o in output.orders] == [(Side.SELL, 5, IntentKind.ENTRY)]
    position = run.state["positions"][ENTRY_ID]
    assert (position["stop"], position["target"]) == (30, 16)  # 기준 고점 28 + 2, 반대쪽 확정 저점 16


def test_확인_봉_종가가_기준_저점_이하이면_신호가_아니다():
    for close in (12, 11):
        rows = with_row(BUY_ROWS, 11, (18, 11, close, 80))
        _, output = entered(rows)

        assert not output.orders
        assert output.decisions[0].reason == "확인 봉 종가가 기준을 넘지 못해 신호가 아님"


def test_후보_봉의_종가가_기준_저점_이하이면_후보가_아니다():
    rows = with_row(BUY_ROWS, 10, (21, 11, 12, 100))  # 종가가 기준 저점과 같음

    run = Run(build(), rows)
    outputs = run.through(len(rows))

    assert not outputs[-1].orders
    assert run.state["candidate"] is None


def test_후보_봉의_저가가_기준_저점보다_높으면_후보가_아니다():
    rows = with_row(BUY_ROWS, 10, (21, 13, 14, 100))

    _, output = entered(rows)

    assert not output.orders


def test_같은_봉에서_매수_후보와_매도_후보가_동시에_나오면_건너뛴다():
    rows = with_row(BUY_ROWS, 10, (25, 11, 18, 100))

    run = Run(build(), rows)
    outputs = run.through(len(rows))

    assert outputs[10].decisions[0].result == DecisionResult.SKIP
    assert not outputs[-1].orders


def test_반대쪽_확정_고점이_없으면_매수_신호를_건너뛴다():
    # 고가가 계속 올라 확정된 고점이 없고, 저점 12만 확정된다.
    rows = [
        (20, 18, 19, 100),
        (21, 17, 18, 100),
        (22, 16, 17, 100),
        (23, 15, 16, 100),
        (24, 12, 15, 100),
        (25, 13, 16, 100),
        (26, 14, 17, 100),
        (27, 15, 18, 100),
        (28, 16, 19, 100),
        (29, 17, 20, 100),
        (30, 11, 14, 100),
        (31, 13, 16, 80),
    ]

    run = Run(build(), rows)
    outputs = run.through(len(rows))

    assert outputs[10].decisions[0].result == DecisionResult.SKIP
    assert "반대쪽 확정 고점" in outputs[10].decisions[0].reason
    assert not outputs[-1].orders


# ---- 진입 조건 ----


def test_확인_봉_거래량이_평균의_절반이면_진입하고_절반_미만이면_건너뛴다():
    _, at_boundary = entered(with_row(BUY_ROWS, 11, (18, 13, 16, 50)))
    _, below = entered(with_row(BUY_ROWS, 11, (18, 13, 16, 49)))

    assert at_boundary.orders
    assert not below.orders
    assert below.decisions[0].result == DecisionResult.SKIP


def test_확인_봉_거래량은_평균에서_제외한다():
    _, output = entered(with_row(BUY_ROWS, 11, (18, 13, 16, 100000)))

    assert output.orders  # 평균은 확인 봉을 뺀 직전 10개(100)로 계산한다


def test_직전_봉이_평균_개수보다_적으면_건너뛴다():
    _, output = entered(volume_avg_bars=12)

    assert not output.orders
    assert output.decisions[0].result == DecisionResult.SKIP


def test_평균_거래량이_0이면_건너뛴다():
    rows = [(h, l, c, 0) for h, l, c, _ in BUY_ROWS[:-1]] + [BUY_ROWS[-1]]

    _, output = entered(rows)

    assert not output.orders
    assert output.decisions[0].reason == "평균 거래량이 0"


def test_보유_중_같은_방향_신호는_추가_진입한다():
    run = Run(build(), BUY_ROWS, lots=[lot("2026-10-27-0", Side.BUY)])
    outputs = run.through(len(BUY_ROWS))

    assert [(o.side, o.quantity, o.kind) for o in outputs[-1].orders] == [(Side.BUY, 5, IntentKind.ENTRY)]


def test_보유_중_반대_방향_신호는_건너뛴다():
    run = Run(build(), BUY_ROWS, lots=[lot("2026-10-27-0", Side.SELL)])
    outputs = run.through(len(BUY_ROWS))

    assert not outputs[-1].orders
    assert outputs[-1].decisions[0].result == DecisionResult.SKIP


def test_미체결_주문이_있으면_진입_신호를_건너뛴다():
    orders = [open_order("o1", Side.BUY, 5, IntentKind.ENTRY, "x")]
    run = Run(build(), BUY_ROWS, open_orders=orders)
    outputs = run.through(len(BUY_ROWS))

    assert not outputs[-1].orders


def test_청산_주문이_처리되는_동안에는_진입_신호를_건너뛴다():
    orders = [open_order("o1", Side.SELL, 5, IntentKind.EXIT, "x")]
    run = Run(build(), BUY_ROWS, lots=[lot("x", Side.BUY)], open_orders=orders)
    outputs = run.through(len(BUY_ROWS))

    assert not outputs[-1].orders


def test_전일_봉은_신호_계산에_쓰지_않는다():
    run = Run(build(), BUY_ROWS[:9], start=datetime(2026, 10, 26, 9, 0))
    run.bars += make_bars(BUY_ROWS[9:], datetime(2026, 10, 27, 9, 0))

    output = run.bar(len(run.bars))

    assert not output.orders


# ---- 목표와 손절 ----


def test_가격이_손절_기준_이하이면_해당_진입분을_손절한다():
    run, _ = entered()
    held = [lot(ENTRY_ID, Side.BUY)]

    output = run.price(12, 10, lots=held)

    assert summarize(output) == [(Side.SELL, 5, IntentKind.EXIT, ENTRY_ID)]
    assert output.decisions[0].reason == "손절"
    assert not run.price(12, 11, lots=held).orders


def test_가격이_목표_이상이면_이익_청산한다():
    run, _ = entered()
    held = [lot(ENTRY_ID, Side.BUY)]

    output = run.price(12, 24, lots=held)

    assert summarize(output) == [(Side.SELL, 5, IntentKind.EXIT, ENTRY_ID)]
    assert output.decisions[0].reason == "이익 청산 목표 도달"
    assert not run.price(12, 23, lots=held).orders


def test_매도_포지션은_가격이_올라_손절_기준에_닿으면_손절하고_내려가_목표에_닿으면_이익_청산한다():
    run, _ = entered(mirror(BUY_ROWS))
    held = [lot(ENTRY_ID, Side.SELL)]

    stop = run.price(12, 30, lots=held)
    target = run.price(12, 16, lots=held)

    assert (stop.orders[0].side, stop.decisions[0].reason) == (Side.BUY, "손절")
    assert (target.orders[0].side, target.decisions[0].reason) == (Side.BUY, "이익 청산 목표 도달")


def test_목표와_손절을_동시에_만족하면_청산_이유를_손절로_한다():
    run = Run(build(), BUY_ROWS)
    run.state = {
        "day": "2026-10-27",
        "entry_count": 1,
        "candidate": None,
        "positions": {
            "p": {
                "side": "buy",
                "stop": 20,
                "target": 15,
                "target_index": 2,
                "since_index": 11,
                "expires": "2026-10-27T10:00:00",
            }
        },
    }

    output = run.price(12, 17, lots=[lot("p", Side.BUY)])

    assert len(output.orders) == 1
    assert output.decisions[0].reason == "손절"


def test_진입분마다_자기_손절_기준으로_청산한다():
    run = Run(build(), BUY_ROWS)
    position = {"side": "buy", "target": 100, "target_index": 2, "since_index": 11, "expires": "2026-10-27T10:00:00"}
    run.state = {
        "day": "2026-10-27",
        "entry_count": 2,
        "candidate": None,
        "positions": {"a": {**position, "stop": 10}, "b": {**position, "stop": 14}},
    }
    held = [lot("a", Side.BUY, 3), lot("b", Side.BUY, 2)]

    output = run.price(12, 13, lots=held)

    assert summarize(output) == [(Side.SELL, 2, IntentKind.EXIT, "b")]


def test_이미_청산_주문이_나간_진입분에는_다시_주문하지_않는다():
    run, _ = entered()
    held = [lot(ENTRY_ID, Side.BUY)]
    pending = [open_order("o1", Side.SELL, 5, IntentKind.EXIT, ENTRY_ID)]

    assert not run.price(12, 10, lots=held, open_orders=pending).orders


def test_청산이_일부만_체결되면_남은_수량을_계속_청산한다():
    run, _ = entered()

    output = run.price(12, 10, lots=[lot(ENTRY_ID, Side.BUY, 2)])

    assert summarize(output) == [(Side.SELL, 2, IntentKind.EXIT, ENTRY_ID)]


def test_거래량_조건은_손절과_이익_청산을_막지_않는다():
    run, _ = entered()
    thin = [(30, 5, 20, 0)]
    run.bars += make_bars(thin, START + timedelta(minutes=36))

    output = run.price(13, 10, lots=[lot(ENTRY_ID, Side.BUY)])

    assert output.orders


# ---- 목표 갱신 방식과 목표 고정 방식 ----


def advance(run, upto, **overrides):
    outputs = []
    for count in range(len(BUY_ROWS) + 1, upto + 1):
        outputs.append(run.bar(count, lots=[lot(ENTRY_ID, Side.BUY)], **overrides))
    return outputs


def test_목표_갱신_방식은_보유_중_새로_확정된_고점으로_목표를_바꾼다():
    run, _ = entered()
    run.bars += make_bars(AFTER_ENTRY, START + timedelta(minutes=36))

    advance(run, 15)  # 인덱스 13의 고점 26은 아직 확정 전
    assert run.state["positions"][ENTRY_ID]["target"] == 24  # 진입 전에 확정된 고점 23은 새 고점이 아니다
    advance(run, 16)

    assert run.state["positions"][ENTRY_ID]["target"] == 26


def test_목표_갱신_방식은_목표를_바꾼_시점에_가격이_이미_새_목표를_지났으면_즉시_청산한다():
    run, _ = entered()
    run.bars += make_bars(AFTER_ENTRY, START + timedelta(minutes=36))
    advance(run, 15)

    output = run.bar(16, lots=[lot(ENTRY_ID, Side.BUY)], price=27)

    assert summarize(output) == [(Side.SELL, 5, IntentKind.EXIT, ENTRY_ID)]
    assert output.decisions[0].reason.startswith("이익 청산 목표 도달")


def test_목표_갱신은_손절_기준을_바꾸지_않는다():
    run, _ = entered()
    run.bars += make_bars(AFTER_ENTRY, START + timedelta(minutes=36))
    advance(run, 16)

    assert run.state["positions"][ENTRY_ID]["stop"] == 10


def test_목표_고정_방식은_목표를_바꾸지_않는다():
    run, _ = entered(target_mode="고정")
    run.bars += make_bars(AFTER_ENTRY, START + timedelta(minutes=36))

    advance(run, 16)

    assert run.state["positions"][ENTRY_ID]["target"] == 24


# ---- 시각·날짜 규칙 ----

CUTOFF_START = datetime(2026, 10, 27, 14, 48)  # 확인 봉이 15:24에 마감된다


def test_신규_진입_제한_시각_이후에는_진입하지_않는다():
    run = Run(build(), BUY_ROWS, start=CUTOFF_START)
    outputs = run.through(len(BUY_ROWS))

    assert not any(output.orders for output in outputs)
    skips = [d for d in outputs[-1].decisions if d.result == DecisionResult.SKIP]
    assert skips and "신규 진입" in skips[0].reason


def test_신규_진입_제한_시각에_장중_미체결_주문을_취소하고_청산_주문의_남은_수량을_이어간다():
    run = Run(build(), BUY_ROWS[:2], start=datetime(2026, 10, 27, 15, 21))
    orders = [
        open_order("o1", Side.SELL, 8, IntentKind.EXIT, "a", filled=2),
        open_order("o2", Side.BUY, 3, IntentKind.ENTRY, "b"),
    ]

    output = run.price(2, 20, now=datetime(2026, 10, 27, 15, 24), lots=[lot("a", Side.BUY, 6)], open_orders=orders)

    assert [c.order_id for c in output.cancels] == ["o1", "o2"]
    assert summarize(output) == [(Side.SELL, 6, IntentKind.EXIT, "a")]


def test_당일_청산_시각에_미체결_주문을_취소하고_보유분을_전량_청산한다():
    run = Run(build(), BUY_ROWS[:2], start=datetime(2026, 10, 27, 15, 24))
    held = [lot("a", Side.BUY, 6), lot("b", Side.SELL, 2)]
    orders = [open_order("o1", Side.SELL, 3, IntentKind.EXIT, "a")]

    first = run.price(2, 20, now=datetime(2026, 10, 27, 15, 30), lots=held, open_orders=orders)
    second = run.bar(2, now=datetime(2026, 10, 27, 15, 33), lots=held)

    assert [c.order_id for c in first.cancels] == ["o1"]
    assert summarize(first) == [(Side.SELL, 6, IntentKind.EXIT, "a"), (Side.BUY, 2, IntentKind.EXIT, "b")]
    assert not second.orders
    assert second.decisions[0].result == DecisionResult.SKIP


def test_최종거래일에는_신규_진입을_하지_않고_보유분을_청산한다():
    run = Run(build(), BUY_ROWS, last_trading_day=START.date(), lots=[lot("a", Side.BUY, 4)])
    outputs = run.through(len(BUY_ROWS))

    assert summarize(outputs[0]) == [(Side.SELL, 4, IntentKind.EXIT, "a")]
    assert not any(output.orders for output in outputs[1:])


def test_최종거래일을_확인하지_못하면_신규_진입을_하지_않는다():
    run = Run(build(), BUY_ROWS, last_trading_day=None)
    outputs = run.through(len(BUY_ROWS))

    assert not any(output.orders for output in outputs)


def test_주문도_보유도_없고_유효_시한이_지난_진입분_정보는_지운다():
    run, _ = entered()
    assert ENTRY_ID in run.state["positions"]

    run.bar(12, now=datetime(2026, 10, 27, 12, 0))

    assert run.state["positions"] == {}


def test_저장소의_전략_폴더에서_역매매_전략이_등록된다():
    from strategy_base.registry import StrategyRegistry

    registry = StrategyRegistry(BACKEND_DIR / "strategies")

    assert registry.errors == {}
    assert "week02_samsung_futures_reversal" in [item.id for item in registry.all()]
