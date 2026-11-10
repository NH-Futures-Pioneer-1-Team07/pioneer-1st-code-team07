from datetime import date, datetime, timedelta

import pytest

from app.runners.service import LoadedData
from strategy_base.models import Bar
from app.nh.auth import KST
from tests.test_backtest_service import FakeProbe, body, make_client, run_detail  # noqa: F401

SPREAD_MANIFEST = {
    "name": "스프레드 서비스 테스트 전략",
    "description": "테스트용",
    "instruments": [
        {
            "name": "테스트 스프레드",
            "market": "overseas",
            "exchange": "FCME",
            "code": "AAA-BBB",
            "multiplier": 1000,
            "tick_size": 0.0546875,
            "legs": [{"code": "AAA", "ratio": 3}, {"code": "BBB", "ratio": -2}],
        }
    ],
    "bar": {"unit": "minute", "size": 3},
    "parameters": {"quantity": {"default": 1, "description": "수량"}},
}
CLOSES = {"AAA": 104.0, "BBB": 106.0}


def weekdays_back(count):
    """오늘 이전의 평일 `count`일 중 가장 오래된 날과 가장 최근 날."""
    day, found = datetime.now(KST).date(), []
    while len(found) < count:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            found.append(day)
    return found[-1], found[0]


FIRST, LAST = weekdays_back(20)
PERIOD = {"start_date": FIRST.isoformat(), "end_date": (FIRST + timedelta(days=3)).isoformat()}


class FullDays(FakeProbe):
    """해외 하루 정상 봉 수(3분봉 약 460개)를 돌려주는 가짜 조회."""

    def bars_on(self, day):
        return 460 if self.first <= day <= self.last and day.weekday() < 5 else 0


def leg_bars(day, close):
    first = datetime(day.year, day.month, day.day, 9, 0)
    return [Bar(first + timedelta(minutes=3 * n), close, close, close, 100, close) for n in range(5)]


def make_loader(calls):
    def loader(code, minutes, start, end, on_progress):
        calls.append(code)
        days = {}
        current = start
        while current <= end:
            days[current] = leg_bars(current, CLOSES[code])
            current += timedelta(days=1)
        on_progress(1, 1)
        return LoadedData(days, None)

    return loader


def test_스프레드_종목이면_두_종목을_받아_합쳐_실행한다(make_client):
    calls = []
    client, service = make_client(
        loader=make_loader(calls),
        manifest=SPREAD_MANIFEST,
        nh_overseas_app_key="k",
        nh_overseas_app_secret="s",
        probe=FullDays(first=FIRST, last=LAST),
    )

    response = client.post("/api/backtests", json=body(**PERIOD))
    assert response.status_code == 202, response.text
    started = response.json()
    service.join(10)

    detail = run_detail(client, started)
    assert detail["meta"]["status"] == "completed"
    assert calls == ["AAA", "BBB"]
    bars = detail["result"]["daily_bars"]
    assert bars[0]["close"] == 3 * 104 - 2 * 106
    assert detail["result"]["trade_count"] == len(bars) * 1


def test_수수료는_두_종목_체결대금_합으로_계산하고_실행_가정에_기록한다(make_client):
    client, service = make_client(
        loader=make_loader([]),
        manifest=SPREAD_MANIFEST,
        nh_overseas_app_key="k",
        nh_overseas_app_secret="s",
        probe=FullDays(first=FIRST, last=LAST),
    )

    started = client.post("/api/backtests", json=body(**PERIOD)).json()
    service.join(10)

    detail = run_detail(client, started)
    notional = 3 * 104 + 2 * 106
    assumptions = detail["meta"]["assumptions"]
    assert "두 종목 체결대금의 합" in assumptions["fee"]["basis"]
    assert "두 종목 모두 1호가" in assumptions["slippage"]["direction"]
    expected_per_fill = notional * 1000 * 1 * 0.000085
    assert detail["result"]["fee"] == pytest.approx(expected_per_fill * 2 * detail["result"]["trade_count"])


def test_가능_기간은_두_종목_중_봉이_적은_쪽을_기준으로_한다(make_client):
    probes = {"AAA": FullDays(first=FIRST, last=LAST), "BBB": FullDays(first=FIRST + timedelta(days=7), last=LAST)}
    client, service = make_client(
        loader=make_loader([]),
        manifest=SPREAD_MANIFEST,
        nh_overseas_app_key="k",
        nh_overseas_app_secret="s",
    )
    service._probe_factory = lambda code, minutes: probes[code]

    found = client.get("/api/backtests/range", params={"strategy_id": "week02_stub"})
    assert found.status_code == 200, found.text
    assert found.json()["start"] == (FIRST + timedelta(days=7)).isoformat()


def test_조합_탐색도_두_종목을_받아_합쳐_실행한다(tmp_path):
    from app.config import Settings
    from app.sweep.runner import SweepRunner
    from app.sweep.spec import parse_spec
    from app.sweep.store import SweepStore
    from strategy_base.registry import StrategyRegistry
    from tests.test_registry import make_folder
    from tests.test_backtest_service import STRATEGY as STUB

    strategies = tmp_path / "strategies"
    strategies.mkdir()
    make_folder(strategies, "week02_stub", manifest=SPREAD_MANIFEST, strategy=STUB)
    settings = Settings(
        trading_env="mock",
        strategies_dir=strategies,
        runs_dir=tmp_path / "runs",
        sweeps_dir=tmp_path / "sweeps",
        reports_dir=tmp_path / "reports",
        minute_cache_dir=tmp_path / "cache",
    )
    calls = []
    runner = SweepRunner(
        settings,
        StrategyRegistry(strategies),
        SweepStore(settings.sweeps_dir),
        make_loader(calls),
        lambda instrument, quantity: [],
        today=lambda: date(2026, 11, 10),
    )
    request = parse_spec(
        {
            "strategy_id": "week02_stub",
            "initial_capital": 100_000_000,
            "periods": [{"start": "2026-10-20", "end": "2026-10-23"}],
        }
    )

    report = runner.run(request)

    assert report.failed == {}
    assert len(report.ran) == 1
    assert calls == ["AAA", "BBB"]
