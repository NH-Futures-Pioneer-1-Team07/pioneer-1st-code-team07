import json
from datetime import datetime, timedelta, timezone

import pytest

from app.records.store import KST, RecordError, RunNotFound, RunStore

STARTED = datetime(2026, 10, 28, 9, 30, 12, tzinfo=KST)
INSTRUMENT = {"name": "삼성전자선물 2026년 11월물", "code": "A116B000"}


def start(store, mode="backtest", strategy_id="week02_sample", started_at=STARTED, **kwargs):
    return store.start_run(
        strategy_id=strategy_id,
        strategy_name="샘플 전략",
        mode=mode,
        instrument=INSTRUMENT,
        params={"quantity": 5},
        started_at=started_at,
        **kwargs,
    )


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_실행을_시작하면_전략과_모드별_폴더가_생기고_meta가_저장된다(tmp_path):
    recorder = start(RunStore(tmp_path), period={"start": "2026-10-20", "end": "2026-10-27"}, initial_capital=1e8)

    folder = tmp_path / "week02_sample" / "backtest" / "20261028_093012"
    assert recorder.folder == folder
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta == {
        "run_id": "20261028_093012",
        "strategy_id": "week02_sample",
        "strategy_name": "샘플 전략",
        "mode": "backtest",
        "instrument": INSTRUMENT,
        "params": {"quantity": 5},
        "started_at": "2026-10-28T09:30:12+09:00",
        "ended_at": None,
        "status": "running",
        "period": {"start": "2026-10-20", "end": "2026-10-27"},
        "initial_capital": 1e8,
        "assumptions": {"fee": None, "slippage": None, "fill": None},
    }


def test_백테스트_메타에_비용과_체결_가정을_담을_수_있다(tmp_path):
    recorder = start(RunStore(tmp_path), assumptions={"fee": 0.00003, "fill": "다음 봉 시가"})

    assumptions = recorder.meta["assumptions"]
    assert assumptions == {"fee": 0.00003, "slippage": None, "fill": "다음 봉 시가"}


def test_모의매매_메타에는_백테스트_항목이_없다(tmp_path):
    recorder = start(RunStore(tmp_path), mode="paper")

    assert "period" not in recorder.meta
    assert "assumptions" not in recorder.meta


def test_같은_초에_시작한_실행은_폴더가_겹치지_않는다(tmp_path):
    store = RunStore(tmp_path)

    first, second = start(store), start(store)

    assert first.run_id == "20261028_093012"
    assert second.run_id == "20261028_093012-1"


def test_기록은_날짜별_파일에_덧붙고_공통_필드가_있다(tmp_path):
    recorder = start(RunStore(tmp_path))
    first = datetime(2026, 10, 27, 10, 3, tzinfo=KST)

    recorder.record("decision", time=first, result="buy", reason="돌파", quantity=12)
    recorder.record("fill", time=first, side="buy", quantity=12, price=70500)
    recorder.record("event", time=first + timedelta(days=1), text="다음 날")

    journal = recorder.folder / "journal"
    day1 = read_lines(journal / "2026-10-27.jsonl")
    day2 = read_lines(journal / "2026-10-28.jsonl")
    assert [line["kind"] for line in day1] == ["decision", "fill"]
    assert [line["seq"] for line in day1 + day2] == [1, 2, 3]
    for line in day1 + day2:
        assert line["run_id"] == "20261028_093012"
        assert line["strategy_id"] == "week02_sample"
        assert line["mode"] == "backtest"
    assert day1[0]["time"] == "2026-10-27T10:03:00+09:00"
    assert day1[0]["reason"] == "돌파"


def test_시간대가_없는_시각은_한국_시간으로_본다(tmp_path):
    recorder = start(RunStore(tmp_path))

    line = recorder.record("event", time=datetime(2026, 10, 27, 15, 30), text="x")

    assert line["time"] == "2026-10-27T15:30:00+09:00"


def test_다른_시간대의_시각은_한국_시간으로_바꿔_날짜를_정한다(tmp_path):
    recorder = start(RunStore(tmp_path))
    utc = datetime(2026, 10, 27, 16, 0, tzinfo=timezone.utc)  # 한국 시간 다음 날 01:00

    recorder.record("event", time=utc, text="x")

    assert (recorder.folder / "journal" / "2026-10-28.jsonl").exists()


def test_알_수_없는_종류나_공통_필드와_겹치는_이름은_기록할_수_없다(tmp_path):
    recorder = start(RunStore(tmp_path))

    with pytest.raises(RecordError):
        recorder.record("memo", text="x")
    with pytest.raises(RecordError):
        recorder.record("event", seq=99)


def test_기록에서_비밀정보_필드를_제거한다(tmp_path):
    recorder = start(RunStore(tmp_path))

    recorder.record("order", request={"headers": {"authorization": "Bearer x"}, "qty": 1}, account_no="123-45")

    line = read_lines(next((recorder.folder / "journal").glob("*.jsonl")))[0]
    assert line["request"] == {"headers": {}, "qty": 1}
    assert "account_no" not in line
    assert "Bearer" not in json.dumps(line)


def test_메타와_결과에서도_비밀정보를_제거한다(tmp_path):
    store = RunStore(tmp_path)
    recorder = store.start_run(
        strategy_id="week02_sample",
        strategy_name="샘플",
        mode="paper",
        instrument=INSTRUMENT,
        params={"quantity": 5, "appkey": "k"},
        started_at=STARTED,
    )

    recorder.finish({"net_pnl": 1, "account_number": "1"})

    assert "appkey" not in (recorder.folder / "meta.json").read_text(encoding="utf-8")
    assert "account_number" not in (recorder.folder / "result.json").read_text(encoding="utf-8")


def test_종료하면_결과와_상태가_확정된다(tmp_path):
    recorder = start(RunStore(tmp_path))

    recorder.finish({"net_pnl": 1250000, "fee": 84000, "trade_count": 14})

    meta = json.loads((recorder.folder / "meta.json").read_text(encoding="utf-8"))
    result = json.loads((recorder.folder / "result.json").read_text(encoding="utf-8"))
    assert meta["status"] == "completed"
    assert meta["ended_at"] is not None
    assert result["net_pnl"] == 1250000


def test_오류로_끝낼_수_있고_실행_중으로는_끝낼_수_없다(tmp_path):
    recorder = start(RunStore(tmp_path))

    with pytest.raises(RecordError):
        recorder.finish(status="running")
    recorder.finish(status="error")

    assert recorder.meta["status"] == "error"


def test_서버가_멈춰_실행_중으로_남은_기록은_중단으로_바꾼다(tmp_path):
    store = RunStore(tmp_path)
    running = start(store)
    done = start(store, mode="paper")
    done.finish({"net_pnl": 0})

    changed = RunStore(tmp_path).mark_interrupted()

    assert changed == [str(running.folder)]
    assert store.get_run("week02_sample", "backtest", running.run_id)["meta"]["status"] == "interrupted"
    assert store.get_run("week02_sample", "paper", done.run_id)["meta"]["status"] == "completed"


def test_이력_목록은_최근_시작한_순서이고_모드와_전략으로_거를_수_있다(tmp_path):
    store = RunStore(tmp_path)
    old = start(store, started_at=STARTED)
    new = start(store, mode="paper", started_at=STARTED + timedelta(hours=1))
    other = start(store, strategy_id="week02_other", started_at=STARTED + timedelta(hours=2))
    old.finish({"net_pnl": 500})

    runs = store.list_runs()

    assert [r["run_id"] for r in runs] == [other.run_id, new.run_id, old.run_id]
    assert [r["mode"] for r in store.list_runs(mode="paper")] == ["paper"]
    assert [r["strategy_id"] for r in store.list_runs(strategy_id="week02_sample")] == ["week02_sample"] * 2
    assert {r["run_id"]: r["net_pnl"] for r in runs} == {other.run_id: None, new.run_id: None, old.run_id: 500}


def test_이력_목록에는_모드별_요구_항목이_있다(tmp_path):
    store = RunStore(tmp_path)
    start(
        store,
        period={"start": "2026-10-20", "end": "2026-10-27"},
        initial_capital=1e8,
        assumptions={"slippage": {"ticks": 2}},
    ).finish({"net_pnl": 3})
    start(store, mode="paper", started_at=STARTED + timedelta(hours=1)).finish({"net_pnl": 4})

    paper, backtest = store.list_runs()

    assert {"strategy_name", "instrument", "started_at", "ended_at", "net_pnl"} <= paper.keys()
    assert backtest["period"] == {"start": "2026-10-20", "end": "2026-10-27"}
    assert backtest["initial_capital"] == 1e8
    assert backtest["assumptions"]["slippage"] == {"ticks": 2}


def test_이력_상세는_메타와_결과를_돌려준다(tmp_path):
    store = RunStore(tmp_path)
    recorder = start(store)
    assert store.get_run("week02_sample", "backtest", recorder.run_id)["result"] is None

    recorder.finish({"net_pnl": 7})
    detail = store.get_run("week02_sample", "backtest", recorder.run_id)

    assert detail["meta"]["params"] == {"quantity": 5}
    assert detail["result"] == {"net_pnl": 7}


@pytest.mark.parametrize(
    "ids",
    [
        ("../x", "backtest", "20261028_093012"),
        ("week02_sample", "live", "20261028_093012"),
        ("week02_sample", "backtest", "../../etc"),
        ("week02_sample", "backtest", "20261028_000000"),
    ],
)
def test_없거나_잘못된_실행은_찾을_수_없다(tmp_path, ids):
    store = RunStore(tmp_path)
    start(store)

    with pytest.raises(RunNotFound):
        store.get_run(*ids)


def make_journal(tmp_path):
    store = RunStore(tmp_path)
    recorder = start(store)
    base = datetime(2026, 10, 27, 9, 0, tzinfo=KST)
    for index in range(6):
        recorder.record("decision" if index % 2 == 0 else "fill", time=base + timedelta(minutes=3 * index), n=index)
    recorder.record("event", time=base + timedelta(days=1), n=6)
    return store, recorder


def test_기록을_종류로_거른다(tmp_path):
    store, recorder = make_journal(tmp_path)

    page = store.read_journal("week02_sample", "backtest", recorder.run_id, kind="fill")

    assert [line["n"] for line in page.items] == [1, 3, 5]
    assert page.total == 3


def test_기록을_구간으로_거른다_끝은_포함하지_않는다(tmp_path):
    store, recorder = make_journal(tmp_path)
    start_at = datetime(2026, 10, 27, 9, 3, tzinfo=KST)
    end_at = datetime(2026, 10, 27, 9, 12, tzinfo=KST)

    page = store.read_journal("week02_sample", "backtest", recorder.run_id, start=start_at, end=end_at)

    assert [line["n"] for line in page.items] == [1, 2, 3]


def test_여러_날짜에_걸친_기록을_시간순으로_돌려준다(tmp_path):
    store, recorder = make_journal(tmp_path)

    page = store.read_journal("week02_sample", "backtest", recorder.run_id)

    assert [line["n"] for line in page.items] == [0, 1, 2, 3, 4, 5, 6]


def test_기록을_나눠서_조회한다(tmp_path):
    store, recorder = make_journal(tmp_path)

    page = store.read_journal("week02_sample", "backtest", recorder.run_id, offset=2, limit=3)

    assert [line["n"] for line in page.items] == [2, 3, 4]
    assert (page.total, page.offset, page.limit) == (7, 2, 3)
