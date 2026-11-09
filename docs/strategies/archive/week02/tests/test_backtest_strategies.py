"""실제 전략을 가짜 분봉으로 백테스트 엔진에 돌려 본다. 손익 계산이 기록과 맞는지 본다."""

import json
import random
from datetime import date, datetime, timedelta

import pytest

from app.config import BACKEND_DIR
from app.records.store import KST, RunStore
from app.runners.backtest import Assumptions, BacktestEngine, infer_tick
from strategy_base.models import Bar
from strategy_base.registry import StrategyRegistry

REGISTRY = StrategyRegistry(BACKEND_DIR / "strategies")
ASSUMPTIONS = Assumptions(fee_rate=0.000085, slippage_ticks=1, multiplier=10, tick_size=500)
LAST_TRADING_DAY = date(2026, 11, 12)


def random_day(day: date, seed: int) -> list[Bar]:
    """08:45부터 15:33까지 3분봉. 시가는 앞 봉 종가이고 가격은 500원 단위로 흔들린다."""
    rng = random.Random(seed)
    price = 240_000
    bars = []
    first = datetime(day.year, day.month, day.day, 8, 45)
    for number in range(137):
        open_ = price
        close = open_ + 500 * rng.randint(-6, 6)
        high = max(open_, close) + 500 * rng.randint(0, 3)
        low = min(open_, close) - 500 * rng.randint(0, 3)
        bars.append(Bar(first + timedelta(minutes=3 * number), high, low, close, rng.randint(800, 30000), open_))
        price = close
    return bars


def run_strategy(tmp_path, strategy_id, days):
    registered = REGISTRY.get(strategy_id)
    recorder = RunStore(tmp_path).start_run(
        strategy_id=strategy_id,
        strategy_name=registered.manifest.name,
        mode="backtest",
        instrument={"name": "삼성전자선물", "code": "A116B000"},
        params={},
        started_at=datetime(2026, 10, 28, 9, 0, tzinfo=KST),
    )
    engine = BacktestEngine(
        registered.strategy_class(registered.manifest.default_params()),
        recorder,
        Assumptions(**{**ASSUMPTIONS.__dict__, "tick_size": infer_tick(days)}),
        initial_capital=100_000_000,
        minutes=3,
        last_trading_day=LAST_TRADING_DAY,
    )
    result = engine.run(days)
    lines = []
    for path in sorted((recorder.folder / "journal").glob("*.jsonl")):
        lines += [json.loads(text) for text in path.read_text(encoding="utf-8").splitlines()]
    return engine, result, lines


@pytest.mark.parametrize("strategy_id", ["week02_samsung_futures_intraday"])
def test_실제_전략이_여러_날을_돌고_손익이_기록과_일치한다(tmp_path, strategy_id):
    days = {date(2026, 10, 19) + timedelta(days=n): random_day(date(2026, 10, 19) + timedelta(days=n), 100 + n)
            for n in range(5)}

    engine, result, lines = run_strategy(tmp_path, strategy_id, days)

    trades = [line for line in lines if line["kind"] == "trade"]
    fills = [line for line in lines if line["kind"] == "fill"]
    assert result["days"] == 5
    assert result["trade_count"] == len(trades) > 0
    assert engine.positions == {}
    assert result["net_pnl"] == pytest.approx(sum(t["net_pnl"] for t in trades))
    assert result["fee"] == pytest.approx(sum(f["fee"] for f in fills))
    assert result["final_equity"] == pytest.approx(100_000_000 + result["net_pnl"])
    assert result["win_count"] + result["loss_count"] <= result["trade_count"]
    assert result["max_drawdown"] >= 0
    assert not [line for line in lines if line.get("level") == "warning"]


@pytest.mark.parametrize("strategy_id", ["week02_samsung_futures_intraday"])
def test_전략은_15시_30분_이후에는_보유를_남기지_않는다(tmp_path, strategy_id):
    days = {date(2026, 10, 19): random_day(date(2026, 10, 19), 7), date(2026, 10, 20): random_day(date(2026, 10, 20), 8)}

    engine, result, lines = run_strategy(tmp_path, strategy_id, days)

    closing = [line for line in lines if line["kind"] == "fill" and line["source"] == "backtest_end"]
    assert closing == []  # 기간 종료 청산이 필요한 보유가 남지 않았다
    for fill in (line for line in lines if line["kind"] == "fill" and line["intent"] == "entry"):
        assert fill["time"][11:16] < "15:24"


def test_같은_데이터는_같은_결과를_낸다(tmp_path):
    days = {date(2026, 10, 19): random_day(date(2026, 10, 19), 11)}

    _, first, _ = run_strategy(tmp_path / "a", "week02_samsung_futures_intraday", days)
    _, second, _ = run_strategy(tmp_path / "b", "week02_samsung_futures_intraday", days)

    assert first == second
