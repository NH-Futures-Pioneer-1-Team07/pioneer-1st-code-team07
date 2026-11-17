"""모의매매 실행 서비스. 요청을 검증하고, 전용 스레드의 이벤트 루프에서 `PaperSession`을 돌린다."""

import asyncio
import dataclasses
import logging
import threading
from collections.abc import Callable
from datetime import datetime, time
from typing import Any, Protocol

from app.config import Settings
from app.data.vix import load as load_vix
from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.realtime import RealtimeConnection
from app.nh.realtime_data import Feed
from app.records.store import RunRecorder, RunStore
from app.runners.broker import Broker, NHBroker, OverseasNHBroker
from app.runners.clearing import (
    AccountGateway,
    ClearConfig,
    NHAccountGateway,
    OverseasAccountGateway,
    account_view,
    run_clear,
)
from app.runners.inputs import ExtraInputs
from app.runners.overseas import has_keys, key_names, overseas_instrument_ready
from app.runners.paper import PaperConfig, PaperSession, StateChange, kst_now
from app.runners.series import DAILY_MARGIN, DailyFetcher, nh_daily_fetcher
from app.runners.spread import spread_daily_fetcher
from app.runners.spread_broker import SpreadBroker, SpreadPriceMux
from strategy_base.manifest import Instrument, Manifest
from strategy_base.registry import StrategyRegistry

logger = logging.getLogger(__name__)


# 스프레드 전략의 일봉 계열을 받을 때 두 종목 각각 조회하는 일봉 개수(파라미터 `window_days`의 최대값보다 크게)
SPREAD_DAILY_BARS = 200


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


# (종목, 봉 분 단위) -> (NH 호출 묶음, 실시간 연결 만드는 함수)
OverseasComponentsFactory = Callable[[Instrument, int], tuple[Broker, RealtimeFactory]]


def overseas_components(settings: Settings) -> OverseasComponentsFactory:
    """해외 종목은 해외 키로 실시간 체결(FA)을 받고, 연결이 끊긴 동안은 세션이 현재가를 조회한다."""

    def build(instrument: Instrument, minutes: int) -> tuple[Broker, RealtimeFactory]:
        client = NHClient(settings, market="overseas")
        if instrument.legs:
            legs = instrument.legs
            broker = SpreadBroker(
                [OverseasNHBroker(client, instrument.exchange or "", leg.code, minutes) for leg in legs],
                legs,
                instrument.code or "",
                name=instrument.name,
            )
            return broker, lambda on_event, on_state: RealtimeConnection(
                client, on_event=SpreadPriceMux(instrument.code or "", legs, on_event), on_state=on_state
            )
        broker = OverseasNHBroker(client, instrument.exchange or "", instrument.code or "", minutes)
        return broker, lambda on_event, on_state: RealtimeConnection(client, on_event=on_event, on_state=on_state)

    return build


class PaperService:
    def __init__(
        self,
        settings: Settings,
        registry: StrategyRegistry,
        store: RunStore,
        *,
        components: ComponentsFactory | None = None,
        overseas_factory: OverseasComponentsFactory | None = None,
        clock: Callable[[], datetime] = kst_now,
        config_overrides: dict[str, Any] | None = None,
        gateway_factory: Callable[[], AccountGateway] | None = None,
        clear_config: ClearConfig | None = None,
        daily_fetcher: DailyFetcher | None = None,
        overseas_gateway_factory: Callable[[], AccountGateway] | None = None,
    ):
        self._settings = settings
        self._registry = registry
        self._store = store
        self._components = components or nh_components(settings)
        self._overseas_components = overseas_factory or overseas_components(settings)
        self._clock = clock
        self._daily_fetcher = daily_fetcher or nh_daily_fetcher(settings)
        self._overrides = config_overrides or {}
        self._lock = threading.Lock()
        self._session: PaperSession | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._run: dict[str, str] | None = None
        self._last: dict[str, Any] | None = None
        self._recorder: RunRecorder | None = None
        self._gateway_factory = gateway_factory or (lambda: NHAccountGateway(NHClient(settings)))
        self._gateway: AccountGateway | None = None
        self._overseas_gateway_factory = overseas_gateway_factory or (
            lambda: OverseasAccountGateway(NHClient(settings, market="overseas"))
        )
        self._overseas_gateway: AccountGateway | None = None
        self._clear_config = clear_config or ClearConfig()
        self._clear: dict[str, Any] | None = None
        self._clear_thread: threading.Thread | None = None

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
        if instrument.market == "overseas":
            problem = overseas_instrument_ready(instrument)
            if problem:
                raise TradingRejected(422, problem)
        if not has_keys(self._settings, instrument.market):
            raise TradingRejected(503, f"{key_names(instrument.market)} 환경변수를 설정하세요")

        with self._lock:
            if self._session is not None:
                raise TradingRejected(409, "이미 운용 중인 전략이 있습니다")
            if instrument.market == "overseas":
                broker, make_realtime = self._overseas_components(instrument, manifest.bar.size)
            else:
                broker, make_realtime = self._components(instrument.code, manifest.bar.size)
            deposit, last_trading_day = self._check_account(
                broker, instrument.code, [leg.code for leg in instrument.legs or []]
            )
            fee_price = self._fee_price(broker)
            started_at = self._clock()
            config = dataclasses.replace(
                PaperConfig(
                    code=instrument.code,
                    name=manifest.name,
                    multiplier=instrument.multiplier,
                    minutes=manifest.bar.size,
                    fee_rate=self._settings.backtest_fee_rate,
                    history_bars=manifest.history_bars,
                    market=instrument.market,
                    fee_price=fee_price,
                    **({"session_anchor": time(0, 0)} if instrument.market == "overseas" else {}),
                ),
                **self._overrides,
            )
            recorder = self._store.start_run(
                strategy_id=strategy_id,
                strategy_name=manifest.name,
                mode="paper",
                instrument={"name": instrument.name, "market": instrument.market, "code": instrument.code, "multiplier": instrument.multiplier},
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
                extras=self._extra_inputs(manifest, instrument),
            )
            self._session = session
            self._recorder = recorder
            self._run = {"strategy_id": strategy_id, "mode": "paper", "run_id": recorder.run_id}
            # 국내는 체결과 주문/체결 알림을, 해외는 체결만 받는다(해외 주문 상태는 계좌 조회로 맞춘다).
            feeds = (
                [Feed("FA", leg.code) for leg in instrument.legs]
                if instrument.legs
                else [Feed("FA", config.code)]
                if instrument.market == "overseas"
                else [Feed("KA", config.code), Feed("O1")]
            )
            self._thread = threading.Thread(
                target=self._thread_main, args=(session, make_realtime, feeds, recorder), daemon=True
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
            session, run, last, clear = self._session, self._run, self._last, self._clear
        if session is None:
            status: dict[str, Any] = {"phase": "idle", "run": None, "last_run": last}
        else:
            snapshot = dict(session.snapshot) or {"phase": session.phase}
            status = {**snapshot, "run": run, "strategy": session.config.name, "instrument": session.config.code}
        if clear is not None:
            status["clear"] = clear
            if clear["state"] == "running":
                status["phase"] = "clearing"
        return status

    def account(self, market: str = "domestic") -> dict[str, Any]:
        """NH 모의계좌의 예탁금, 보유 포지션, 미체결 주문. `market`이 `overseas`이면 해외 모의계좌다."""
        gateway = self._account_gateway(market)
        try:
            return account_view(gateway)
        except NHError as error:
            raise TradingRejected(502, f"NH 모의계좌를 조회하지 못했습니다: {type(error).__name__}") from error

    def clear(self, market: str = "domestic") -> dict[str, str]:
        """미체결 주문을 모두 취소하고 남은 포지션을 모두 청산한다. 같은 시장에서 운용 중인 전략은 판단을 멈추고 끝낸다."""
        gateway = self._account_gateway(market)
        with self._lock:
            if self._clear is not None and self._clear["state"] == "running":
                raise TradingRejected(409, "이미 정리 중입니다")
            session, loop, recorder = self._session, self._loop, self._recorder
            if session is not None and session.config.market != market:
                session, loop, recorder = None, None, None  # 다른 시장의 운용은 건드리지 않는다
            self._clear = {"state": "running", "step": "start", "detail": "정리를 시작합니다", "result": None}
            if session is not None:
                self._call_in_loop(loop, session, session.begin_pause)
            self._clear_thread = threading.Thread(
                target=self._clear_main, args=(gateway, session, loop, recorder), daemon=True
            )
            self._clear_thread.start()
        return {"phase": "clearing"}

    def join(self, timeout: float | None = None) -> None:
        for thread in (self._thread, self._clear_thread):
            if thread is not None:
                thread.join(timeout)

    # ---- 검증과 준비 ----

    def _account_gateway(self, market: str = "domestic") -> AccountGateway:
        if self._settings.trading_env != "mock":
            raise TradingRejected(422, "모의 환경(TRADING_ENV=mock)에서만 쓸 수 있습니다")
        if not has_keys(self._settings, market):
            raise TradingRejected(503, f"{key_names(market)} 환경변수를 설정하세요")
        if market == "overseas":
            if self._overseas_gateway is None:
                self._overseas_gateway = self._overseas_gateway_factory()
            return self._overseas_gateway
        if self._gateway is None:
            self._gateway = self._gateway_factory()
        return self._gateway

    @staticmethod
    def _call_in_loop(loop: asyncio.AbstractEventLoop | None, session: PaperSession, call: Callable[..., None], *args: Any) -> None:
        if loop is not None:
            loop.call_soon_threadsafe(call, *args)
        else:
            call(*args)

    def _extra_inputs(self, manifest: Manifest, instrument: Any) -> ExtraInputs:
        loader = None
        if manifest.series:
            def loader(day):  # noqa: ANN001 - 날짜가 바뀔 때마다 일봉을 다시 받는다
                bars = spread_daily_fetcher(self._daily_fetcher)(instrument, SPREAD_DAILY_BARS if instrument.legs else DAILY_MARGIN)
                return {name: bars for name in manifest.series}

        return ExtraInputs(vix=load_vix(), margin=instrument.margin, loader=loader)

    def _merge_params(self, manifest: Manifest, overrides: dict[str, Any] | None) -> dict[str, Any]:
        problem = manifest.override_problem(overrides)
        if problem:
            raise TradingRejected(422, problem)
        return {**manifest.default_params(), **(overrides or {})}

    @staticmethod
    def _fee_price(broker: Broker) -> float | None:
        """스프레드 종목의 수수료 어림 가격(두 종목 체결대금의 합). 일반 종목이나 조회 실패면 `None`."""
        if not isinstance(broker, SpreadBroker):
            return None
        try:
            return broker.notional_price()
        except NHError:
            return None

    def _check_account(
        self, broker: Broker, code: str, leg_codes: list[str] | None = None
    ) -> tuple[dict[str, Any], Any]:
        """운용을 시작하기 전에 계좌를 조회한다. 그 종목(스프레드면 두 종목 모두)에 기존 포지션이나 미체결이 있으면 거부한다."""
        codes = {code, *(leg_codes or [])}
        try:
            positions = [p for p in broker.positions() if p.code in codes and (p.quantity or 0) != 0]
            orders = [o for o in broker.open_orders() if o.code in codes]
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
        self, session: PaperSession, make_realtime: RealtimeFactory, feeds: list[Feed], recorder: RunRecorder
    ) -> None:
        async def main() -> None:
            self._loop = asyncio.get_running_loop()
            realtime = make_realtime(session.post, lambda state, detail: session.post(StateChange(str(state), detail)))
            try:
                for feed in feeds:
                    await realtime.subscribe(feed)
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

    # ---- 계좌 전체 정리 ----

    def _clear_main(
        self,
        gateway: AccountGateway,
        session: PaperSession | None,
        loop: asyncio.AbstractEventLoop | None,
        recorder: RunRecorder | None,
    ) -> None:
        def active() -> bool:
            return session is not None and self._session is session

        def report(step: str, detail: str) -> None:
            self._clear = {"state": "running", "step": step, "detail": detail, "result": None}
            logger.info("계좌 전체 정리: %s", detail)
            if recorder is not None and active():
                recorder.record("event", text=f"계좌 전체 정리: {detail}", step=step)

        def stop_run() -> None:
            if session is not None and active():
                self._call_in_loop(loop, session, session.begin_stop, True)

        try:
            result = run_clear(gateway, self._clear_config, report=report, stop_run=stop_run, run_active=active)
        except Exception as error:
            result = {
                "status": "incomplete",
                "open_orders": [],
                "positions": [],
                "cancelled": 0,
                "closed": [],
                "problems": [f"정리 중 오류: {type(error).__name__}: {error}"],
            }
        if recorder is not None and session is not None:
            recorder.record("event", text="계좌 전체 정리 결과", status=result["status"], problems=result["problems"])
        self._clear = {"state": "done", "step": "done", "detail": result["status"], "result": result}
