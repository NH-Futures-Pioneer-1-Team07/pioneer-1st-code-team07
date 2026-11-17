import csv
import json
from datetime import date, timedelta

import pytest

from app.config import Settings
from app.records.store import RunStore
from app.runners.service import BacktestService, LoadedData
from app.sweep.cache import CachedLoader
from app.sweep.runner import SweepError, SweepRunner
from app.sweep.spec import SpecError, expand, parse_spec
from app.sweep.store import SweepStore, combo_id
from app.sweep.table import build_table, sharpe, write_table
from strategy_base.registry import StrategyRegistry
from tests.test_backtest_service import FakeProbe, day_bars, good_loader
from tests.test_registry import make_folder

STRATEGY = """
from strategy_base.interface import BaseStrategy
from strategy_base.models import IntentKind, OrderIntent, Side, StrategyOutput


class Strategy(BaseStrategy):
    def on_bar(self, ctx):
        quantity = self.params["quantity"]
        if len(ctx.bars) == 1:
            order = OrderIntent(Side.BUY, quantity, IntentKind.ENTRY, ctx.now.strftime("%Y%m%d") + "-e", "진입 신호")
            return StrategyOutput(orders=[order])
        if len(ctx.bars) == 3 and ctx.lots:
            lot = ctx.lots[0]
            order = OrderIntent(Side.SELL, lot.quantity, IntentKind.EXIT, lot.entry_id, "청산 신호")
            return StrategyOutput(orders=[order])
        return StrategyOutput()
"""
MANIFEST = {
    "name": "조합 탐색 테스트 전략",
    "description": "테스트용",
    "instruments": [{"name": "삼성전자선물", "market": "domestic", "code": "A116B000", "multiplier": 10}],
    "bar": {"unit": "minute", "size": 3},
    "parameters": {"quantity": {"default": 1, "description": "수량", "min": 1, "max": 5}},
}
START, END = date(2026, 10, 20), date(2026, 10, 23)
TODAY = date(2026, 11, 10)


class CountingLoader:
    def __init__(self):
        self.calls = []

    def __call__(self, code, minutes, start, end, on_progress):
        self.calls.append((start, end))
        return good_loader(code, minutes, start, end, on_progress)


@pytest.fixture
def env(tmp_path):
    strategies = tmp_path / "strategies"
    strategies.mkdir()
    make_folder(strategies, "week02_stub", manifest=MANIFEST, strategy=STRATEGY)
    settings = Settings(
        trading_env="mock",
        nh_app_key="k",
        nh_app_secret="s",
        strategies_dir=strategies,
        runs_dir=tmp_path / "runs",
        sweeps_dir=tmp_path / "sweeps",
        reports_dir=tmp_path / "reports",
        minute_cache_dir=tmp_path / "cache",
    )
    registry = StrategyRegistry(strategies)
    store = SweepStore(settings.sweeps_dir)
    loader = CountingLoader()
    runner = SweepRunner(settings, registry, store, loader, lambda instrument, quantity: [], today=lambda: TODAY)
    return settings, registry, store, loader, runner


def spec(**overrides):
    raw = {
        "strategy_id": "week02_stub",
        "initial_capital": 100_000_000,
        "periods": [{"start": START.isoformat(), "end": END.isoformat()}],
        **overrides,
    }
    return parse_spec(raw)


# ---- 요청 파일 ----


def test_params와_grid가_조합으로_펼쳐지고_중복은_합쳐진다():
    parsed = parse_spec(
        {
            "strategy_id": "s",
            "initial_capital": 1000,
            "periods": [{"start": "2026-10-01", "end": "2026-10-10"}, {"start": "2026-10-11", "end": "2026-10-20"}],
            "params": [{"a": 1}, {"a": 1}],
            "grid": {"a": [1, 2], "b": [10, 20]},
        }
    )

    combos = expand(parsed)

    assert [c.overrides for c in combos[::2]] == [{"a": 1}, {"a": 1, "b": 10}, {"a": 1, "b": 20}, {"a": 2, "b": 10}, {"a": 2, "b": 20}]
    assert len(combos) == 10


def test_params와_grid가_없으면_기본_파라미터_하나만_실행한다():
    assert [c.overrides for c in expand(spec())] == [{}]


@pytest.mark.parametrize(
    "change",
    [
        {"initial_capital": 0},
        {"periods": []},
        {"periods": [{"start": "2026-10-10", "end": "2026-10-01"}]},
        {"periods": [{"start": "10월", "end": "2026-10-01"}]},
        {"grid": {"a": []}},
        {"slippage_ticks": -1},
    ],
)
def test_잘못된_요청_파일은_거절한다(change):
    with pytest.raises(SpecError):
        spec(**change)


# ---- 실행과 저장 ----


def test_조합을_실행하면_결과와_거래_파일이_저장된다(env):
    _, _, store, _, runner = env

    report = runner.run(spec(params=[{"quantity": 1}, {"quantity": 2}]))

    assert len(report.ran) == 2 and report.failed == {}
    rows = store.read_results("week02_stub")
    assert [row["params"]["quantity"] for row in rows] == [1, 2]
    first = rows[0]
    assert first["start"] == "2026-10-20" and first["end"] == "2026-10-23"
    assert first["slippage_ticks"] == 1 and first["initial_capital"] == 100_000_000
    assert first["summary"]["trade_count"] == 4
    assert len(first["daily_equity"]) == 4
    lines = store.read_trades("week02_stub", first["id"])
    trades = [line for line in lines if line["kind"] == "trade"]
    fills = [line for line in lines if line["kind"] == "fill"]
    assert len(trades) == first["summary"]["trade_count"]
    assert len(fills) == 8
    assert trades[0]["entry_reason"] == "진입 신호" and trades[0]["exit_reason"] == "청산 신호"
    assert {"price", "raw_price", "fee", "intent", "entry_id", "source"} <= set(fills[0])


def test_같은_조합을_다시_실행하면_건너뛴다(env):
    _, _, store, loader, runner = env
    runner.run(spec(params=[{"quantity": 2}]))
    calls_before = len(loader.calls)

    report = runner.run(spec(params=[{"quantity": 2}]))

    assert report.ran == [] and len(report.skipped) == 1
    assert len(store.read_results("week02_stub")) == 1
    assert len(loader.calls) == calls_before  # 실행할 조합이 없으면 데이터도 받지 않는다


def test_기본값과_같은_파라미터를_적어도_같은_조합이다(env):
    _, _, store, _, runner = env
    runner.run(spec(params=[{}]))

    report = runner.run(spec(params=[{"quantity": 1}]))

    assert report.ran == [] and len(report.skipped) == 1


def test_새_조합만_추가로_실행한다(env):
    _, _, store, _, runner = env
    runner.run(spec(params=[{"quantity": 1}]))

    report = runner.run(spec(params=[{"quantity": 1}, {"quantity": 3}]))

    assert len(report.ran) == 1 and len(report.skipped) == 1
    assert [row["params"]["quantity"] for row in store.read_results("week02_stub")] == [1, 3]


def test_여러_조합과_기간을_실행해도_분봉은_한_번만_받는다(env):
    _, _, _, loader, runner = env
    periods = [{"start": "2026-10-20", "end": "2026-10-21"}, {"start": "2026-10-22", "end": "2026-10-23"}]

    report = runner.run(spec(periods=periods, params=[{"quantity": 1}, {"quantity": 2}]))

    assert len(report.ran) == 4
    assert loader.calls == [(START, END)]


def test_허용_범위를_벗어난_파라미터는_데이터를_받기_전에_거절한다(env):
    _, _, store, loader, runner = env

    with pytest.raises(SweepError, match="quantity"):
        runner.run(spec(params=[{"quantity": 1}, {"quantity": 9}]))

    assert loader.calls == [] and store.read_results("week02_stub") == []


@pytest.mark.parametrize("period", [{"start": "2026-11-01", "end": "2026-11-10"}])
def test_종료일이_오늘이면_거절한다(env, period):
    _, _, _, _, runner = env

    with pytest.raises(SweepError, match="오늘"):
        runner.run(spec(periods=[period]))


def test_없는_전략은_거절한다(env):
    _, _, _, _, runner = env

    with pytest.raises(SweepError, match="전략을 찾을 수 없습니다"):
        runner.run(spec(strategy_id="week02_none"))


def test_분봉이_없는_기간은_실패로_보고하고_나머지는_계속한다(env):
    _, _, store, _, runner = env
    periods = [{"start": "2026-10-20", "end": "2026-10-23"}, {"start": "2026-09-01", "end": "2026-09-02"}]
    runner._loader = lambda code, minutes, start, end, progress: LoadedData(
        {d: day_bars(d) for d in (START + timedelta(days=n) for n in range(4))}, TODAY
    )

    report = runner.run(spec(periods=periods))

    assert len(report.ran) == 1 and len(report.failed) == 1
    assert "분봉" in next(iter(report.failed.values()))
    assert len(store.read_results("week02_stub")) == 1


def test_기본_파라미터_결과가_기존_백테스트와_같다(env, tmp_path):
    settings, registry, store, _, runner = env
    runner.run(spec(params=[{}]))
    row = store.read_results("week02_stub")[0]

    service = BacktestService(
        settings,
        registry,
        RunStore(settings.runs_dir),
        loader_factory=lambda: good_loader,
        probe_factory=lambda code, minutes: FakeProbe(first=date(2026, 10, 1), last=date(2026, 10, 27)),
    )
    started = service.start("week02_stub", START, END, 100_000_000)
    service.join(10)
    result = json.loads((settings.runs_dir / "week02_stub" / "backtest" / started["run_id"] / "result.json").read_text(encoding="utf-8"))

    for name in ("net_pnl", "gross_pnl", "fee", "trade_count", "win_count", "loss_count", "max_drawdown", "days", "bars"):
        assert row["summary"][name] == result[name], name
    assert row["daily_equity"] == result["equity_curve"]


def test_조합_식별자는_정의가_같으면_같고_다르면_다르다():
    args = ("s", {"a": 1}, "2026-10-01", "2026-10-10", 1, 1000.0, 0.000085)

    assert combo_id(*args) == combo_id(*args)
    assert combo_id(*args) != combo_id("s", {"a": 2}, *args[2:])
    assert combo_id(*args) != combo_id(*args[:4], 2, *args[5:])


# ---- 분봉 저장 ----


def test_저장된_기간은_다시_받지_않고_모자란_구간만_받는다(tmp_path):
    inner = CountingLoader()
    loader = CachedLoader(inner, tmp_path, "domestic", lambda: TODAY)

    first = loader("A", 3, date(2026, 10, 20), date(2026, 10, 22), lambda *_: None)
    loader("A", 3, date(2026, 10, 20), date(2026, 10, 22), lambda *_: None)
    extended = loader("A", 3, date(2026, 10, 20), date(2026, 10, 25), lambda *_: None)

    assert inner.calls == [(date(2026, 10, 20), date(2026, 10, 22)), (date(2026, 10, 23), date(2026, 10, 25))]
    assert sorted(first.days) == [date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22)]
    assert len(extended.days) == 6
    assert extended.last_trading_day == date(2026, 11, 12)
    assert extended.days[date(2026, 10, 20)] == first.days[date(2026, 10, 20)]


def test_새로_만든_로더도_저장된_분봉을_쓴다(tmp_path):
    CachedLoader(CountingLoader(), tmp_path, "domestic", lambda: TODAY)("A", 3, START, END, lambda *_: None)
    inner = CountingLoader()

    loaded = CachedLoader(inner, tmp_path, "domestic", lambda: TODAY)("A", 3, START, END, lambda *_: None)

    assert inner.calls == [] and len(loaded.days) == 4


def test_오늘_이후_날짜는_저장하지_않는다(tmp_path):
    inner = CountingLoader()
    loader = CachedLoader(inner, tmp_path, "domestic", lambda: date(2026, 10, 22))

    loader("A", 3, date(2026, 10, 20), date(2026, 10, 23), lambda *_: None)
    loader("A", 3, date(2026, 10, 20), date(2026, 10, 23), lambda *_: None)

    assert inner.calls == [(date(2026, 10, 20), date(2026, 10, 23)), (date(2026, 10, 22), date(2026, 10, 23))]


# ---- 비교표 ----


def make_row(quantity, start, end, net, equity):
    return {
        "id": f"{quantity}{start}",
        "params": {"quantity": quantity, "levels": [1, 2]},
        "start": start,
        "end": end,
        "slippage_ticks": 1,
        "initial_capital": 1000,
        "summary": {"net_pnl": net, "gross_pnl": net + 10, "fee": 10, "return_rate": net / 1000, "max_drawdown_rate": 0.1, "trade_count": 10, "win_count": 6},
        "daily_equity": [{"time": "d", "equity": value} for value in equity],
    }


def test_비교표는_조합이_행이고_기간마다_지표_열이_붙는다():
    rows = [
        make_row(1, "2026-10-01", "2026-10-10", 50, [1010, 1020, 1050]),
        make_row(1, "2026-10-11", "2026-10-20", -20, [990, 980]),
        make_row(2, "2026-10-01", "2026-10-10", 200, [1100, 1200]),
    ]

    columns, table = build_table(rows)

    assert columns[:5] == ["quantity", "period_count", "positive_periods", "worst_net_pnl", "total_net_pnl"]
    assert "levels" not in columns  # 모든 조합에서 같은 파라미터는 열로 만들지 않는다
    assert "net_pnl[2026-10-01~2026-10-10]" in columns and "sharpe[2026-10-11~2026-10-20]" in columns
    assert [line["quantity"] for line in table] == [2, 1]  # 합산 순손익이 큰 순서
    quantity1 = table[1]
    assert quantity1["period_count"] == 2 and quantity1["positive_periods"] == 1
    assert quantity1["worst_net_pnl"] == -20 and quantity1["total_net_pnl"] == 30
    assert quantity1["win_rate[2026-10-01~2026-10-10]"] == 0.6
    assert quantity1["fee_ratio[2026-10-01~2026-10-10]"] == pytest.approx(10 / 60)
    assert table[0]["net_pnl[2026-10-11~2026-10-20]"] is None


def test_일별_자산이_모자라거나_변화가_없으면_샤프는_비운다():
    assert sharpe([{"equity": 1010}], 1000) is None
    assert sharpe([{"equity": 1000}, {"equity": 1000}], 1000) is None


def test_표를_CSV로_쓴다(env):
    settings, _, store, _, runner = env
    runner.run(spec(params=[{"quantity": 1}, {"quantity": 2}]))
    path = settings.reports_dir / "week02_stub" / "첫탐색" / "table.csv"

    count = write_table(store, "week02_stub", path)

    assert count == 2
    with path.open(encoding="utf-8", newline="") as file:
        lines = list(csv.DictReader(file))
    totals = [float(line["total_net_pnl"]) for line in lines]
    assert totals == sorted(totals, reverse=True)
    assert {"quantity", "total_net_pnl", "net_pnl[2026-10-20~2026-10-23]"} <= set(lines[0])
