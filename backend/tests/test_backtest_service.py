import json
import threading
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.runners.service import BacktestRejected, LoadedData
from strategy_base.models import Bar
from tests.test_registry import make_folder

STRATEGY = """
from strategy_base.interface import BaseStrategy
from strategy_base.models import IntentKind, OrderIntent, Side, StrategyOutput


class Strategy(BaseStrategy):
    def on_bar(self, ctx):
        if len(ctx.bars) == 1:
            order = OrderIntent(Side.BUY, 1, IntentKind.ENTRY, ctx.now.strftime("%Y%m%d") + "-e", "테스트")
            return StrategyOutput(orders=[order])
        if len(ctx.bars) == 3 and ctx.lots:
            lot = ctx.lots[0]
            order = OrderIntent(Side.SELL, lot.quantity, IntentKind.EXIT, lot.entry_id, "테스트")
            return StrategyOutput(orders=[order])
        return StrategyOutput()
"""
MANIFEST = {
    "name": "서비스 테스트 전략",
    "description": "테스트용",
    "instruments": [{"name": "삼성전자선물", "market": "domestic", "code": "A116B000", "multiplier": 10}],
    "bar": {"unit": "minute", "size": 3},
    "parameters": {"quantity": {"default": 1, "description": "수량"}},
}
START, END = date(2026, 10, 20), date(2026, 10, 23)


def day_bars(day):
    first = datetime(day.year, day.month, day.day, 9, 0)
    rows = [(100000, 100500, 99500, 100000), (100500, 101000, 100000, 100500),
            (100500, 102000, 100500, 101500), (102000, 102500, 101500, 102000), (102000, 102000, 102000, 102000)]
    return [Bar(first + timedelta(minutes=3 * n), h, l, c, 100, o) for n, (o, h, l, c) in enumerate(rows)]


class FakeProbe:
    """분봉이 있는 날짜를 정해 둔 가짜 조회."""

    def __init__(self, first=date(2026, 10, 1), last=date(2026, 10, 27), last_trading_day=date(2026, 11, 12), few=None):
        self.first, self.last, self.ltd = first, last, last_trading_day
        self.few = few or {}
        self.calls = 0

    def bars_on(self, day):
        self.calls += 1
        if not (self.first <= day <= self.last and day.weekday() < 5):
            return 0
        return self.few.get(day, 130)

    def last_trading_day(self):
        return self.ltd


def good_loader(code, minutes, start, end, on_progress):
    days = {}
    current = start
    while current <= end:
        days[current] = day_bars(current)
        on_progress(len(days), (end - start).days + 1)
        current += timedelta(days=1)
    return LoadedData(days, date(2026, 11, 12))


@pytest.fixture
def make_client(tmp_path):
    def build(loader=good_loader, manifest=MANIFEST, probe=None, **settings_kwargs):
        strategies = tmp_path / "strategies"
        strategies.mkdir(exist_ok=True)
        if (strategies / "week02_stub").exists():
            import shutil

            shutil.rmtree(strategies / "week02_stub")
        make_folder(strategies, "week02_stub", manifest=manifest, strategy=STRATEGY)
        values = {"trading_env": "mock", "nh_app_key": "k", "nh_app_secret": "s",
                  "strategies_dir": strategies, "runs_dir": tmp_path / "runs"}
        app = create_app(Settings(**{**values, **settings_kwargs}))
        app.state.backtests._loader_factory = lambda: loader
        app.state.backtests._probe_factory = lambda code, minutes: probe or FakeProbe()
        return TestClient(app), app.state.backtests

    return build


def body(**overrides):
    return {"strategy_id": "week02_stub", "start_date": START.isoformat(), "end_date": END.isoformat(),
            "initial_capital": 100_000_000, **overrides}


def run_detail(client, started):
    return client.get(f"/api/runs/{started['strategy_id']}/{started['mode']}/{started['run_id']}").json()


def test_백테스트를_시작하면_식별자를_바로_돌려주고_끝나면_결과가_저장된다(make_client):
    client, service = make_client()

    response = client.post("/api/backtests", json=body())
    service.join(10)

    assert response.status_code == 202
    started = response.json()
    assert started["mode"] == "backtest" and started["strategy_id"] == "week02_stub"
    detail = run_detail(client, started)
    assert detail["meta"]["status"] == "completed"
    assert detail["meta"]["progress"] == {"stage": "done", "done": 4, "total": 4}
    assert detail["meta"]["period"] == {"start": "2026-10-20", "end": "2026-10-23"}
    assert detail["result"]["trade_count"] == 4
    assert detail["result"]["initial_capital"] == 100_000_000
    bars = detail["result"]["daily_bars"]
    assert [row["date"] for row in bars] == ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]
    assert bars[0] == {"date": "2026-10-20", "open": 100000, "high": 102500, "low": 99500, "close": 102000, "volume": 500}
    assert client.get("/api/backtests/current").json() == {"run": None}


def test_비용과_체결_가정이_실행_정보에_기록된다(make_client):
    client, service = make_client()

    started = client.post("/api/backtests", json=body()).json()
    service.join(10)

    assumptions = run_detail(client, started)["meta"]["assumptions"]
    assert assumptions["fee"]["rate"] == 0.000085
    assert "0.0085%" in assumptions["fee"]["source"]
    assert assumptions["slippage"] == {"ticks": 1, "tick_size": 500.0, "direction": "시장가 체결마다 불리한 방향"}
    assert "다음 봉 시가" in assumptions["fill"]["on_bar"]
    assert assumptions["margin"]


def test_요청한_슬리피지가_체결_가격과_실행_정보에_반영된다(make_client):
    client, service = make_client(backtest_slippage_ticks=1)
    results = {}
    for ticks in (None, 0, 3):
        started = client.post("/api/backtests", json=body(**({} if ticks is None else {"slippage_ticks": ticks}))).json()
        service.join(10)
        detail = run_detail(client, started)
        results[ticks] = (detail["meta"]["assumptions"]["slippage"]["ticks"], detail["result"]["gross_pnl"])

    assert [results[key][0] for key in (None, 0, 3)] == [1, 0, 3]
    assert results[0][1] > results[None][1] > results[3][1]


def test_슬리피지가_범위를_벗어나면_거부한다(make_client):
    client, _ = make_client()

    for ticks in (-1, 21):
        response = client.post("/api/backtests", json=body(slippage_ticks=ticks))
        assert response.status_code == 422 and "0틱부터 20틱" in response.json()["detail"]
    assert client.post("/api/backtests", json=body(slippage_ticks=20)).status_code == 202


def test_기록에_판단_주문_체결_거래가_남는다(make_client):
    client, service = make_client()
    started = client.post("/api/backtests", json=body()).json()
    service.join(10)
    url = f"/api/runs/{started['strategy_id']}/backtest/{started['run_id']}/journal"

    kinds = {line["kind"] for line in client.get(url, params={"limit": 1000}).json()["items"]}

    assert kinds == {"order", "fill", "trade", "event"}


def test_수수료_가정은_시작_전에_조회할_수_있고_환경변수로_바꿀_수_있다(make_client):
    client, _ = make_client()
    assert client.get("/api/backtests/assumptions").json()["fee"]["rate"] == 0.000085

    client, _ = make_client(backtest_fee_rate=0.0001, backtest_slippage_ticks=2)
    shown = client.get("/api/backtests/assumptions").json()

    assert shown["fee"]["rate"] == 0.0001 and "환경변수" in shown["fee"]["source"]
    assert shown["slippage"]["ticks"] == 2


def test_실행_중에는_다시_시작할_수_없고_현재_실행을_알려_준다(make_client):
    release = threading.Event()

    def blocking(code, minutes, start, end, on_progress):
        release.wait(10)
        return good_loader(code, minutes, start, end, on_progress)

    client, service = make_client(loader=blocking)
    first = client.post("/api/backtests", json=body())

    second = client.post("/api/backtests", json=body())
    running = client.get("/api/backtests/current").json()
    release.set()
    service.join(10)

    assert first.status_code == 202
    assert second.status_code == 409
    assert running["run"] == first.json()
    assert client.post("/api/backtests", json=body()).status_code == 202
    service.join(10)


@pytest.mark.parametrize(
    "overrides, status",
    [
        ({"strategy_id": "nope"}, 404),
        ({"start_date": "2026-10-24"}, 422),  # 시작일이 종료일보다 늦음
        ({"end_date": "2099-01-01"}, 422),  # 오늘 이후
        ({"initial_capital": 0}, 422),
        ({"params": {"unknown": 1}}, 422),
        ({"start_date": "2024-01-01"}, 422),  # 기간이 너무 김
    ],
)
def test_잘못된_요청은_거부하고_실행_기록을_만들지_않는다(make_client, overrides, status, tmp_path):
    client, _ = make_client()

    response = client.post("/api/backtests", json=body(**overrides))

    assert response.status_code == status
    assert client.get("/api/runs").json() == []


def test_종료일이_오늘이면_거부한다(make_client):
    client, _ = make_client()
    today = datetime.now().date().isoformat()

    assert client.post("/api/backtests", json=body(end_date=today)).status_code == 422


def test_종목_정보가_모자란_전략은_거부한다(make_client):
    no_multiplier = {**MANIFEST, "instruments": [{"name": "삼성전자선물", "market": "domestic", "code": "A116B000"}]}
    client, _ = make_client(manifest=no_multiplier)

    response = client.post("/api/backtests", json=body())

    assert response.status_code == 422
    assert "거래승수" in response.json()["detail"]


def test_해외_종목은_아직_지원하지_않아_거부한다(make_client):
    overseas = {**MANIFEST, "instruments": [{"name": "미국 10년 국채", "market": "overseas", "code": "ZNZ26", "multiplier": 1000}]}
    client, _ = make_client(manifest=overseas)

    response = client.post("/api/backtests", json=body())

    assert response.status_code == 422
    assert "해외" in response.json()["detail"]


def test_일봉_전략은_거부한다(make_client):
    daily = {**MANIFEST, "bar": {"unit": "day", "size": 1}}
    client, _ = make_client(manifest=daily)

    assert client.post("/api/backtests", json=body()).status_code == 422


def test_인증_정보가_없으면_503이다(make_client):
    client, _ = make_client(nh_app_key=None, nh_app_secret=None)

    response = client.post("/api/backtests", json=body())

    assert response.status_code == 503
    assert "NH_APP_KEY" in response.json()["detail"]


def test_전략_파라미터를_덮어쓸_수_있고_기록에_남는다(make_client):
    client, service = make_client()

    started = client.post("/api/backtests", json=body(params={"quantity": 3})).json()
    service.join(10)

    assert run_detail(client, started)["meta"]["params"] == {"quantity": 3}


def test_조회_기간에_데이터가_없으면_오류로_끝난다(make_client):
    client, service = make_client(loader=lambda *args: LoadedData({}, None))

    started = client.post("/api/backtests", json=body()).json()
    service.join(10)

    detail = run_detail(client, started)
    assert detail["meta"]["status"] == "error" and detail["result"] is None
    url = f"/api/runs/week02_stub/backtest/{started['run_id']}/journal"
    events = client.get(url, params={"kind": "event"}).json()["items"]
    assert any(e.get("level") == "error" and "분봉 데이터가 없습니다" in e["text"] for e in events)
    assert client.get("/api/backtests/current").json() == {"run": None}


def test_데이터_조회가_실패하면_오류로_끝나고_다시_시작할_수_있다(make_client):
    def failing(*args):
        raise RuntimeError("조회 실패")

    client, service = make_client(loader=failing)
    started = client.post("/api/backtests", json=body()).json()
    service.join(10)

    assert run_detail(client, started)["meta"]["status"] == "error"
    assert client.post("/api/backtests", json=body()).status_code == 202
    service.join(10)


def test_시작_거부_예외는_상태_코드를_담는다(make_client):
    _, service = make_client()

    with pytest.raises(BacktestRejected) as error:
        service.start("nope", START, END, 1)

    assert error.value.status_code == 404


# ---- 가능 기간 ----


def test_가능_기간_조회는_분봉이_있는_첫_날과_마지막_날과_최종거래일을_돌려준다(make_client):
    client, _ = make_client()

    response = client.get("/api/backtests/range", params={"strategy_id": "week02_stub"})

    assert response.status_code == 200
    assert response.json() == {
        "strategy_id": "week02_stub",
        "instrument": {"name": "삼성전자선물", "market": "domestic", "code": "A116B000"},
        "start": "2026-10-01",
        "end": "2026-10-27",
        "last_trading_day": "2026-11-12",
        "sparse_days": {},
    }


def test_가능_기간_조회는_봉이_적은_날과_그날의_봉_수를_함께_돌려준다(make_client):
    client, _ = make_client(probe=FakeProbe(few={date(2026, 10, 6): 20, date(2026, 10, 8): 69, date(2026, 10, 9): 70}))

    shown = client.get("/api/backtests/range", params={"strategy_id": "week02_stub"}).json()

    assert shown["sparse_days"] == {"2026-10-06": 20, "2026-10-08": 69}


def test_분봉이_전혀_없으면_가능_기간이_없고_시작도_거부한다(make_client):
    client, _ = make_client(probe=FakeProbe(first=date(2030, 1, 1), last=date(2030, 1, 2)))

    shown = client.get("/api/backtests/range", params={"strategy_id": "week02_stub"}).json()
    started = client.post("/api/backtests", json=body())

    assert (shown["start"], shown["end"]) == (None, None)
    assert started.status_code == 422 and "분봉이 없습니다" in started.json()["detail"]


def test_가능_기간_밖의_시작일_종료일은_거부하고_사유에_가능_기간을_적는다(make_client):
    client, _ = make_client(probe=FakeProbe(first=date(2026, 10, 1), last=date(2026, 10, 20)))

    early = client.post("/api/backtests", json=body(start_date="2026-09-28", end_date="2026-10-02"))
    late = client.post("/api/backtests", json=body(start_date="2026-10-15", end_date="2026-10-23"))

    for response in (early, late):
        assert response.status_code == 422
        assert "2026-10-01부터 2026-10-20까지" in response.json()["detail"]
    assert client.get("/api/runs").json() == []


def test_가능_기간_경계_날짜는_허용한다(make_client):
    client, service = make_client()

    response = client.post("/api/backtests", json=body(start_date="2026-10-01", end_date="2026-10-02"))
    service.join(10)

    assert response.status_code == 202


def test_가능_기간_조회의_오류를_처리한다(make_client):
    from app.nh.errors import TransportError

    class Broken(FakeProbe):
        def bars_on(self, day):
            raise TransportError("조회 실패")

    client, _ = make_client(probe=Broken())
    no_keys, _ = make_client(nh_app_key=None, nh_app_secret=None)

    assert client.get("/api/backtests/range", params={"strategy_id": "nope"}).status_code == 404
    assert client.get("/api/backtests/range", params={"strategy_id": "week02_stub"}).status_code == 502
    assert client.post("/api/backtests", json=body()).status_code == 502
    assert no_keys.get("/api/backtests/range", params={"strategy_id": "week02_stub"}).status_code == 503


def test_같은_종목의_가능_기간은_하루_동안_다시_조회하지_않는다(make_client):
    probe = FakeProbe()
    client, _ = make_client(probe=probe)

    client.get("/api/backtests/range", params={"strategy_id": "week02_stub"})
    calls = probe.calls
    client.get("/api/backtests/range", params={"strategy_id": "week02_stub"})
    client.post("/api/backtests", json=body(start_date="2026-10-20", end_date="2026-10-21"))

    assert calls > 0 and probe.calls == calls
