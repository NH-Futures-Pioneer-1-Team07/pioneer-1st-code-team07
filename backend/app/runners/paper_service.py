"""모의매매 실행 서비스. 요청을 검증하고, 전용 스레드의 이벤트 루프에서 `PaperSession`을 돌린다."""

import asyncio
import dataclasses
import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any, Protocol

from app.config import Settings
from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.realtime import RealtimeConnection
from app.nh.realtime_data import Feed
from app.records.store import RunRecorder, RunStore
from app.runners.broker import Broker, NHBroker
from app.runners.paper import PaperConfig, PaperSession, StateChange, kst_now
from strategy_base.manifest import Manifest
from strategy_base.registry import StrategyRegistry


class TradingRejected(Exception):
    """요청을 받아들이지 않았다. `status_code`는 API 응답 코드다."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class Realtime(Protocol):
    async def subscribe(self, feed: Feed) -> None: ...

    def start(self) -> None: ...

    async def stop(self) -> None: ...


# (이벤트 전달 함수, 상태 전달 함수) -> 실시간 연결
RealtimeFactory = Callable[[Callable[[Any], None], Callable[[Any, str], None]], Realtime]
# (종목코드, 봉 분 단위) -> (NH 호출 묶음, 실시간 연결 만드는 함수)
ComponentsFactory = Callable[[str, int], tuple[Broker, RealtimeFactory]]


def nh_components(settings: Settings) -> ComponentsFactory:
    def build(code: str, minutes: int) -> tuple[Broker, RealtimeFactory]:
        client = NHClient(settings)
        return NHBroker(client, code, minutes), lambda on_event, on_state: RealtimeConnection(
            client, on_event=on_event, on_state=on_state
        )

    return build


class PaperService:
    def __init__(
        self,
        settings: Settings,
        registry: StrategyRegistry,
        store: RunStore,
        *,
        components: ComponentsFactory | None = None,
        clock: Callable[[], datetime] = kst_now,
        config_overrides: dict[str, Any] | None = None,
    ):
        self._settings = settings
        self._registry = registry
        self._store = store
        self._components = components or nh_components(settings)
        self._clock = clock
        self._overrides = config_overrides or {}
        self._lock = threading.Lock()
        self._session: PaperSession | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._run: dict[str, str] | None = None
        self._last: dict[str, Any] | None = None

    # ---- API ----

    def start(self, strategy_id: str, params: dict[str, Any] | None = None) -> dict[str, str]:
        registered = self._registry.get(strategy_id)
        if registered is None:
            raise TradingRejected(404, "전략을 찾을 수 없습니다")
        manifest = registered.manifest
        instrument = manifest.instruments[0]
        if manifest.bar.unit != "minute":
            raise TradingRejected(422, "분봉 전략만 운용할 수 있습니다")
        if not instrument.code or not instrument.multiplier:
            raise TradingRejected(422, "전략의 종목에 종목코드와 거래승수가 필요합니다")
        if self._settings.trading_env != "mock":
            raise TradingRejected(422, "모의매매는 모의 환경(TRADING_ENV=mock)에서만 운용할 수 있습니다")
        merged = self._merge_params(manifest, params)
        if not (self._settings.nh_app_key and self._settings.nh_app_secret):
            raise TradingRejected(503, "NH_APP_KEY, NH_APP_SECRET 환경변수를 설정하세요")

        with self._lock:
            if self._session is not None:
                raise TradingRejected(409, "이미 운용 중인 전략이 있습니다")
            broker, make_realtime = self._components(instrument.code, manifest.bar.size)
            deposit, last_trading_day = self._check_account(broker, instrument.code)
            started_at = self._clock()
            config = dataclasses.replace(
                PaperConfig(
                    code=instrument.code,
                    name=manifest.name,
                    multiplier=instrument.multiplier,
                    minutes=manifest.bar.size,
                    fee_rate=self._settings.backtest_fee_rate,
                ),
                **self._overrides,
            )
            recorder = self._store.start_run(
                strategy_id=strategy_id,
                strategy_name=manifest.name,
                mode="paper",
                instrument={"name": instrument.name, "code": instrument.code, "multiplier": instrument.multiplier},
                params=merged,
                assumptions=None,
            )
            recorder.record("event", text="운용 전 계좌", deposit=deposit)
            session = PaperSession(
                registered.strategy_class(merged),
                config,
                broker,
                recorder,
                started_at=started_at,
                last_trading_day=last_trading_day,
                deposit_before=deposit,
                clock=self._clock,
            )
            self._session = session
            self._run = {"strategy_id": strategy_id, "mode": "paper", "run_id": recorder.run_id}
            self._thread = threading.Thread(
                target=self._thread_main, args=(session, make_realtime, config.code, recorder), daemon=True
            )
            self._thread.start()
            return dict(self._run)

    def stop(self) -> dict[str, str]:
        with self._lock:
            session, loop = self._session, self._loop
            if session is None:
                raise TradingRejected(409, "운용 중인 전략이 없습니다")
        if loop is not None:
            loop.call_soon_threadsafe(session.begin_stop)
        else:
            session.begin_stop()
        return {"phase": "stopping"}

    def status(self) -> dict[str, Any]:
        with self._lock:
            session, run, last = self._session, self._run, self._last
        if session is None:
            return {"phase": "idle", "run": None, "last_run": last}
        snapshot = dict(session.snapshot) or {"phase": session.phase}
        return {**snapshot, "run": run, "strategy": session.config.name, "instrument": session.config.code}

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    # ---- 검증과 준비 ----

    def _merge_params(self, manifest: Manifest, overrides: dict[str, Any] | None) -> dict[str, Any]:
        unknown = sorted(set(overrides or {}) - set(manifest.parameters))
        if unknown:
            raise TradingRejected(422, f"전략에 없는 파라미터입니다: {', '.join(unknown)}")
        return {**manifest.default_params(), **(overrides or {})}

    def _check_account(self, broker: Broker, code: str) -> tuple[dict[str, Any], Any]:
        """운용을 시작하기 전에 계좌를 조회한다. 그 종목에 기존 포지션이나 미체결이 있으면 거부한다."""
        try:
            positions = [p for p in broker.positions() if p.code == code and (p.quantity or 0) != 0]
            orders = [o for o in broker.open_orders() if o.code == code]
            deposit = broker.deposit()
            quote = broker.fetch_quote()
        except NHError as error:
            raise TradingRejected(502, f"NH 모의계좌를 조회하지 못했습니다: {type(error).__name__}") from error
        if positions or orders:
            raise TradingRejected(
                409, "그 종목에 기존 포지션이나 미체결 주문이 있습니다. 전체 정리 후 시작하세요"
            )
        snapshot = {
            "cash": deposit.cash,
            "total_assets": deposit.total_assets,
            "fee": deposit.fee,
            "futures_realized_pnl": deposit.futures_realized_pnl,
            "total_pnl": deposit.total_pnl,
        }
        return snapshot, quote.last_trading_day

    # ---- 전용 스레드 ----

    def _thread_main(
        self, session: PaperSession, make_realtime: RealtimeFactory, code: str, recorder: RunRecorder
    ) -> None:
        async def main() -> None:
            self._loop = asyncio.get_running_loop()
            realtime = make_realtime(session.post, lambda state, detail: session.post(StateChange(str(state), detail)))
            try:
                await realtime.subscribe(Feed("KA", code))
                await realtime.subscribe(Feed("O1"))
                realtime.start()
                await session.run()
            finally:
                await realtime.stop()

        try:
            asyncio.run(main())
        except Exception as error:
            recorder.record("event", level="error", text=f"모의매매가 오류로 멈췄습니다: {type(error).__name__}: {error}")
            if session.final_status is None:
                recorder.finish(status="error")
        finally:
            with self._lock:
                self._last = {**(self._run or {}), "status": session.final_status or "error"}
                self._session, self._loop, self._run = None, None, None
