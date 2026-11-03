import importlib.util
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.config import BACKEND_DIR
from strategy_base.indicators import simple_moving_average
from strategy_base.manifest import Manifest
from strategy_base.models import (
    Bar,
    Context,
    DecisionResult,
    IntentKind,
    Lot,
    OpenOrder,
    Side,
)

FOLDER = BACKEND_DIR / "strategies" / "week03_zn_treasury_futures"
NOW = datetime(2026, 11, 3, 10, 0)


def load_strategy():
    import json

    manifest = Manifest.model_validate(json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8")))
    spec = importlib.util.spec_from_file_location("week03_strategy", FOLDER / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Strategy(manifest.default_params()), manifest


def daily(closes, start=datetime(2026, 9, 1)):
    return [Bar(start + timedelta(days=n), c, c, c, 1000, c) for n, c in enumerate(closes)]


def minute_bars(closes, start=datetime(2026, 11, 3, 8, 0)):
    return [Bar(start + timedelta(minutes=5 * n), c, c, c, 100, c) for n, c in enumerate(closes)]


RISING = daily([100 + n for n in range(30)])  # 종가 > 15일선 > 30일선
FALLING = daily([200 - n for n in range(30)])  # 종가 < 15일선, 30일선
MIXED = daily([100] * 15 + [90] * 14 + [101])  # 종가 > 15일선이지만 15일선 < 30일선
FLAT20 = [100.0] * 20
CROSS_UP = FLAT20 + [101.0]  # 21번째 봉에서 단기선이 장기선을 상향 교차
CROSS_DOWN = FLAT20 + [99.0]


def context(bars, daily_bars=RISING, *, vix=12.0, margin=2083.0, lots=(), state=None, pnl=0.0, open_orders=()):
    return Context(
        now=NOW,
        bars=bars,
        params=STRATEGY.params,
        lots=lots,
        open_orders=open_orders,
        state=state or {},
        series={"daily": daily_bars},
        vix=vix,
        margin=margin,
        unrealized_pnl=pnl,
    )


STRATEGY, MANIFEST = load_strategy()


def decide(**kwargs):
    bars = kwargs.pop("bars", minute_bars(CROSS_UP))
    return STRATEGY.on_bar(context(bars, **kwargs))


# ---- 매니페스트 ----


def test_매니페스트가_해외_ZN과_일봉_5분봉_입력을_선언한다():
    instrument = MANIFEST.instruments[0]

    assert (instrument.market, instrument.exchange, instrument.code) == ("overseas", "FCME", "ZNZ26")
    assert MANIFEST.bar.size == 5 and MANIFEST.series["daily"].unit == "day" and MANIFEST.history_bars == 20
    assert MANIFEST.parameters["profit_loss_rate"].default == 0.2


# ---- 중기 신호와 진입 ----


def test_매수_허용일에_상향_교차하면_1계약_매수를_낸다():
    output = decide()

    [order] = output.orders
    assert (order.side, order.quantity, order.kind) == (Side.BUY, 1, IntentKind.ENTRY)
    assert order.entry_id == "2026-11-03-1"
    assert output.decisions[0].result == DecisionResult.BUY
    assert output.state["entered_today"] == 1


def test_매도_허용일에_하향_교차하면_1계약_매도를_낸다():
    output = decide(bars=minute_bars(CROSS_DOWN), daily_bars=FALLING)

    [order] = output.orders
    assert (order.side, order.quantity) == (Side.SELL, 1)


def test_허용_방향과_교차_방향이_다르면_진입하지_않는다():
    assert decide(daily_bars=FALLING).orders == ()
    assert decide(bars=minute_bars(CROSS_DOWN), daily_bars=RISING).orders == ()


def test_중기_신호가_중립이면_진입하지_않는다():
    output = decide(daily_bars=MIXED)

    assert output.orders == ()
    assert output.decisions[0].result == DecisionResult.HOLD


def test_일봉이_모자라면_신호를_계산하지_못해_진입하지_않는다():
    assert decide(daily_bars=RISING[-10:]).orders == ()


def test_교차가_없으면_진입하지_않는다():
    assert decide(bars=minute_bars(FLAT20 + [100.0])).orders == ()


def test_교차한_봉_종가가_두_선_바깥이_아니면_진입하지_않는다():
    prior = [105, 90, 120, 100, 100, 95, 105, 120, 110, 90, 95, 110, 105, 110, 90, 90, 120, 110, 95, 100]
    bars = minute_bars([float(price) for price in prior] + [95.0])
    # 단기선(104)이 장기선(102.5)을 상향 교차했지만 종가 95는 두 선 아래다
    assert simple_moving_average(bars[:-1], 5) <= simple_moving_average(bars[:-1], 20)
    assert simple_moving_average(bars, 5) > simple_moving_average(bars, 20)

    assert decide(bars=bars).orders == ()


def test_봉이_모자라면_장중_교차를_판단하지_않는다():
    assert decide(bars=minute_bars(CROSS_UP[-10:])).orders == ()


# ---- VIX 한도와 보유 한도 ----


@pytest.mark.parametrize(
    ("vix", "buy", "sell"),
    [(14.99, 1, 5), (15, 2, 4), (19.99, 2, 4), (20, 3, 3), (25, 4, 2), (29.99, 4, 2), (30, 5, 1), (80, 5, 1)],
)
def test_VIX_구간별_하루_신규_진입_한도(vix, buy, sell):
    assert STRATEGY._daily_limit(vix, "buy") == buy
    assert STRATEGY._daily_limit(vix, "sell") == sell


def test_하루_한도를_모두_쓰면_진입하지_않고_skip으로_기록한다():
    output = decide(vix=12.0, state={"day": "2026-11-03", "entered_today": 1, "sequence": 1})

    assert output.orders == ()
    assert output.decisions[0].result == DecisionResult.SKIP and "한도" in output.decisions[0].reason


def test_VIX_구간이_올라가면_매수_한도가_늘어난다():
    output = decide(vix=22.0, state={"day": "2026-11-03", "entered_today": 2, "sequence": 2})

    assert len(output.orders) == 1 and output.state["entered_today"] == 3


def test_날짜가_바뀌면_하루_진입_수량을_되돌린다():
    output = decide(vix=12.0, state={"day": "2026-11-02", "entered_today": 1, "sequence": 7})

    assert output.orders[0].entry_id == "2026-11-03-8"
    assert output.state["entered_today"] == 1


def test_VIX를_모르면_진입하지_않는다():
    output = decide(vix=None)

    assert output.orders == ()
    assert output.decisions[0].result == DecisionResult.SKIP


def test_전체_보유_한도에_도달하면_진입하지_않는다():
    lots = [Lot(f"e{n}", Side.BUY, 10, 100.0) for n in range(3)]

    output = decide(vix=40.0, lots=lots, pnl=0.0)

    assert output.orders == ()
    assert "보유 한도" in output.decisions[0].reason


def test_미체결_진입_주문도_보유_수량에_포함한다():
    lots = [Lot("e1", Side.BUY, 29, 100.0)]
    pending = OpenOrder("1", Side.BUY, 1, 0, IntentKind.ENTRY, "e2", NOW)

    assert decide(vix=40.0, lots=lots, open_orders=[pending]).orders == ()
    assert len(decide(vix=40.0, lots=lots).orders) == 1


# ---- 청산 ----


def test_중기_신호가_반대_방향이면_보유분을_전량_청산한다():
    lots = [Lot("a", Side.BUY, 2, 100.0), Lot("b", Side.BUY, 3, 101.0)]

    output = decide(bars=minute_bars(FLAT20 + [100.0]), daily_bars=FALLING, lots=lots)

    assert [(o.side, o.quantity, o.kind, o.entry_id) for o in output.orders] == [
        (Side.SELL, 2, IntentKind.EXIT, "a"),
        (Side.SELL, 3, IntentKind.EXIT, "b"),
    ]


def test_매도_보유분은_매수_허용_신호에서_청산한다():
    lots = [Lot("a", Side.SELL, 2, 100.0)]

    output = decide(bars=minute_bars(FLAT20 + [100.0]), daily_bars=RISING, lots=lots)

    assert [(o.side, o.quantity) for o in output.orders] == [(Side.BUY, 2)]


@pytest.mark.parametrize(("pnl", "exits"), [(900.0, True), (800.0, False), (-900.0, True), (-800.0, False)])
def test_증거금_대비_손익이_기준에_이르면_전량_청산한다(pnl, exits):
    lots = [Lot("a", Side.BUY, 2, 100.0)]
    # 2계약 × 증거금 2083 × 20% = 833.2
    output = decide(bars=minute_bars(FLAT20 + [100.0]), lots=lots, pnl=pnl)

    assert bool(output.orders) == exits


def test_손익_기준은_파라미터로_바꿀_수_있다():
    strategy, _ = load_strategy()
    strategy.params = {**strategy.params, "profit_loss_rate": 0.05}
    lots = [Lot("a", Side.BUY, 2, 100.0)]

    output = strategy.on_bar(replace(context(minute_bars(FLAT20 + [100.0]), lots=lots, pnl=250.0), params=strategy.params))

    assert [o.kind for o in output.orders] == [IntentKind.EXIT]


def test_증거금을_모르면_손익_청산은_건너뛴다():
    lots = [Lot("a", Side.BUY, 2, 100.0)]

    output = decide(bars=minute_bars(FLAT20 + [100.0]), lots=lots, margin=None, pnl=99999.0)

    assert output.orders == ()


def test_중기_중립이나_장중_역교차에서는_계속_보유한다():
    lots = [Lot("a", Side.BUY, 2, 100.0)]

    assert decide(bars=minute_bars(CROSS_DOWN), daily_bars=MIXED, lots=lots).orders == ()
    assert decide(bars=minute_bars(CROSS_DOWN), daily_bars=RISING, lots=lots).orders == ()


def test_청산해도_이미_쓴_하루_진입_수량은_되돌리지_않는다():
    lots = [Lot("a", Side.BUY, 1, 100.0)]
    state = {"day": "2026-11-03", "entered_today": 1, "sequence": 1}

    output = decide(bars=minute_bars(FLAT20 + [100.0]), daily_bars=FALLING, lots=lots, state=state)

    assert output.orders and output.state["entered_today"] == 1


# ---- 레지스트리·백테스트 엔진 연결 ----


def test_전략_폴더가_레지스트리에_등록된다():
    from strategy_base.registry import StrategyRegistry

    registry = StrategyRegistry(BACKEND_DIR / "strategies")

    assert registry.errors == {}
    assert registry.get("week03_zn_treasury_futures") is not None


def test_백테스트_엔진에서_전날_봉과_일봉으로_진입하고_다음날까지_보유한다(tmp_path):
    from datetime import date

    from app.data.vix import VixHistory
    from app.records.store import KST, RunStore
    from app.runners.backtest import Assumptions, BacktestEngine
    from app.runners.inputs import ExtraInputs

    recorder = RunStore(tmp_path).start_run(
        strategy_id="week03_zn_treasury_futures",
        strategy_name="ZN",
        mode="backtest",
        instrument={"name": "ZN", "code": "ZNZ26"},
        params={},
        started_at=datetime(2026, 11, 4, 9, 0, tzinfo=KST),
    )
    engine = BacktestEngine(
        STRATEGY,
        recorder,
        Assumptions(fee_rate=0.0, slippage_ticks=0, multiplier=1000, tick_size=0.015625),
        initial_capital=100_000.0,
        minutes=5,
        last_trading_day=None,
        history_bars=20,
        history=minute_bars([100.0] * 20, start=datetime(2026, 11, 2, 22, 0)),
        extras=ExtraInputs(
            series={"daily": RISING}, vix=VixHistory({date(2026, 11, 2): 12.0}), margin=2083.0
        ),
    )
    # 첫째 날 첫 봉(101)에서 바로 상향 교차한다. 전날 봉 20개가 이어져 장이 열리자마자 판단할 수 있다.
    day1 = minute_bars([101.0, 101.5, 102.0], start=datetime(2026, 11, 3, 0, 0))
    day2 = minute_bars([102.0, 102.0], start=datetime(2026, 11, 4, 0, 0))

    result = engine.run({date(2026, 11, 3): day1, date(2026, 11, 4): day2})

    entries = [fill for fill in _fills(recorder) if fill["intent"] == "entry"]
    assert entries and entries[0]["time"].startswith("2026-11-03T00:05")  # 교차한 봉 다음 봉 시가
    assert entries[0]["side"] == "buy" and entries[0]["quantity"] == 1
    assert result["trade_count"] == 1  # 기간 마지막에 남은 보유분을 종료 청산


def _fills(recorder):
    import json

    lines = []
    for path in sorted((recorder.folder / "journal").glob("*.jsonl")):
        lines += [json.loads(text) for text in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line["kind"] == "fill"]


# ---- 판단 설명과 기록 ----


def test_판단_기록의_detail에_중기와_장중_판단_수치가_담긴다():
    output = decide()

    detail = output.decisions[0].detail
    assert detail["mid"]["signal"] == "buy" and detail["mid"]["close"] == 129
    assert detail["mid"]["short_ma"] > detail["mid"]["long_ma"]
    assert detail["intraday"]["cross"] == "buy" and detail["intraday"]["position"] == "above"
    assert detail["today"]["vix"] == 12.0 and detail["today"]["limit"] == 1 and detail["today"]["entered"] == 1


def test_판단_문구와_주문_사유에_중기와_장중_요약이_붙는다():
    entry = decide()
    hold = decide(bars=minute_bars(FLAT20 + [100.0]))
    exit_ = decide(bars=minute_bars(FLAT20 + [100.0]), daily_bars=FALLING, lots=[Lot("a", Side.BUY, 1, 100.0)])

    assert "중기 매수 허용 · 장중 단기선 상향 교차" in entry.orders[0].reason
    assert hold.decisions[0].reason == "장중 이동평균 교차 없음 (중기 매수 허용 · 장중 단기선과 장기선이 같음)"
    assert "반대 방향" in exit_.orders[0].reason and "중기 매도 허용" in exit_.orders[0].reason


def test_describe는_세_구역으로_현재_판단을_설명한다():
    sections = STRATEGY.describe(context(minute_bars(CROSS_UP), pnl=0.0, lots=[Lot("a", Side.BUY, 2, 100.0)]))["sections"]

    assert [s["title"] for s in sections] == ["중기 판단 (일봉)", "장중 판단 (5분봉)", "오늘 진입·보유"]
    mid, intraday, today = sections
    assert (mid["headline"], mid["tone"]) == ("매수 허용", "buy")
    assert (intraday["headline"], intraday["tone"]) == ("단기선 상향 교차", "buy")
    assert ["진입 신호", "매수 교차"] in intraday["rows"]
    assert ["보유", "매수 2계약"] in today["rows"]
    assert today["headline"] == "신규 진입 0/1계약"
    assert ["증거금 대비 손익", "+0.0% (기준 ±20%)"] in today["rows"]


def test_describe는_값을_모르면_계산_불가와_대시로_표시한다():
    sections = STRATEGY.describe(context([], daily_bars=[], vix=None, margin=None))["sections"]

    assert sections[0]["headline"] == "계산 불가" and sections[0]["rows"][0] == ["직전 거래일 종가", "—"]
    assert sections[1]["headline"] == "계산 불가" and sections[1]["tone"] == "neutral"
    assert sections[2]["headline"] == "신규 진입 0/—계약" and ["VIX(직전 거래일 종가)", "—"] in sections[2]["rows"]
