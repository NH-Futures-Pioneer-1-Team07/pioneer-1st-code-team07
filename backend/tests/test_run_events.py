import asyncio
import threading
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.records.events import QUEUE_SIZE, RESYNC, RunEvents
from app.records.store import KST, RunStore

STARTED = datetime(2026, 10, 28, 9, 30, 12, tzinfo=KST)
INSTRUMENT = {"name": "삼성전자선물 2026년 11월물", "code": "A116B000"}


def start(store, mode="paper"):
    return store.start_run(
        strategy_id="week02_sample", strategy_name="샘플 전략", mode=mode,
        instrument=INSTRUMENT, params={}, started_at=STARTED,
    )


async def collect(subscriber, count):
    return [await asyncio.wait_for(subscriber.queue.get(), 1) for _ in range(count)]


def test_시작_기록_종료가_구독자에게_순서대로_전달된다(tmp_path):
    asyncio.run(_test_시작_기록_종료가_구독자에게_순서대로_전달된다(tmp_path))


async def _test_시작_기록_종료가_구독자에게_순서대로_전달된다(tmp_path):
    store = RunStore(tmp_path)
    subscriber = store.events.subscribe(asyncio.get_running_loop(), "paper")

    recorder = start(store)
    recorder.record("fill", side="buy", quantity=5, price=243000)
    recorder.finish({"net_pnl": 1200.0})

    started, journal, finished = await collect(subscriber, 3)
    assert started["type"] == "run" and started["run"]["status"] == "running"
    assert started["run"]["net_pnl"] is None
    assert journal["type"] == "journal" and journal["line"]["kind"] == "fill"
    assert journal["line"]["seq"] == 1
    assert finished["run"]["status"] == "completed" and finished["run"]["net_pnl"] == 1200.0


def test_모드가_다른_실행의_메시지는_받지_않는다(tmp_path):
    asyncio.run(_test_모드가_다른_실행의_메시지는_받지_않는다(tmp_path))


async def _test_모드가_다른_실행의_메시지는_받지_않는다(tmp_path):
    store = RunStore(tmp_path)
    subscriber = store.events.subscribe(asyncio.get_running_loop(), "paper")

    start(store, mode="backtest").record("decision", result="hold")
    paper = start(store, mode="paper")

    (message,) = await collect(subscriber, 1)
    assert message["run"]["run_id"] == paper.run_id
    assert subscriber.queue.empty()


def test_현재_순손익을_알린다(tmp_path):
    asyncio.run(_test_현재_순손익을_알린다(tmp_path))


async def _test_현재_순손익을_알린다(tmp_path):
    store = RunStore(tmp_path)
    subscriber = store.events.subscribe(asyncio.get_running_loop(), "paper")
    recorder = start(store)
    await collect(subscriber, 1)

    recorder.notify_pnl(-350.0)

    (message,) = await collect(subscriber, 1)
    assert message == {"type": "pnl", "strategy_id": "week02_sample", "mode": "paper",
                       "run_id": recorder.run_id, "net_pnl": -350.0}


def test_다른_스레드에서_쓴_기록도_구독자_루프로_전달된다(tmp_path):
    asyncio.run(_test_다른_스레드에서_쓴_기록도_구독자_루프로_전달된다(tmp_path))


async def _test_다른_스레드에서_쓴_기록도_구독자_루프로_전달된다(tmp_path):
    store = RunStore(tmp_path)
    subscriber = store.events.subscribe(asyncio.get_running_loop(), "paper")
    recorder = start(store)
    await collect(subscriber, 1)

    thread = threading.Thread(target=lambda: recorder.record("event", text="다른 스레드"))
    thread.start()
    thread.join()

    (message,) = await collect(subscriber, 1)
    assert message["line"]["text"] == "다른 스레드"


def test_구독자가_밀리면_resync_하나만_남긴다():
    asyncio.run(_test_구독자가_밀리면_resync_하나만_남긴다())


async def _test_구독자가_밀리면_resync_하나만_남긴다():
    events = RunEvents()
    subscriber = events.subscribe(asyncio.get_running_loop())

    for index in range(QUEUE_SIZE + 5):
        events.publish({"type": "journal", "line": {"mode": "paper", "seq": index}})
    await asyncio.sleep(0.05)

    assert subscriber.queue.qsize() == 1
    assert subscriber.queue.get_nowait() is RESYNC


def test_구독을_끊으면_더_받지_않는다():
    asyncio.run(_test_구독을_끊으면_더_받지_않는다())


async def _test_구독을_끊으면_더_받지_않는다():
    events = RunEvents()
    subscriber = events.subscribe(asyncio.get_running_loop())
    events.unsubscribe(subscriber)

    events.publish({"type": "run", "run": {"mode": "paper"}})
    await asyncio.sleep(0.01)

    assert subscriber.queue.empty()


def client(tmp_path):
    settings = Settings(trading_env="mock", nh_app_key="k", nh_app_secret="s",
                        strategies_dir=tmp_path / "s", runs_dir=tmp_path / "r")
    return TestClient(create_app(settings))


def test_웹소켓은_ready를_먼저_보내고_이후_변경을_전달한다(tmp_path):
    with client(tmp_path) as test_client:
        with test_client.websocket_connect("/ws/runs?mode=paper") as socket:
            assert socket.receive_json() == {"type": "ready"}
            recorder = start(test_client.app.state.run_store)
            assert socket.receive_json()["run"]["run_id"] == recorder.run_id
            recorder.record("decision", result="hold", reason="돌파 없음")
            message = socket.receive_json()
            assert message["type"] == "journal" and message["line"]["reason"] == "돌파 없음"


def test_웹소켓은_알_수_없는_모드를_거부한다(tmp_path):
    with client(tmp_path) as test_client:
        with test_client.websocket_connect("/ws/runs?mode=live") as socket:
            with pytest.raises(Exception):
                socket.receive_json()
