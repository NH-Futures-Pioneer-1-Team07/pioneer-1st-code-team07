"""백테스트 실행 서비스. 요청을 검증하고, 백그라운드에서 데이터 준비와 시뮬레이션을 돌린다."""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from app.config import Settings
from app.nh.auth import KST
from app.nh.client import NHClient
from app.nh.errors import NHError
from app.nh.quotes import fetch_minute_bars, fetch_quote
from app.records.store import RunRecorder, RunStore
from app.runners.availability import AvailableRange, NHProbe, ProbeSource, RangeCache, sparse_below
from app.runners.backtest import Assumptions, BacktestEngine, daily_bars, infer_tick
from strategy_base.manifest import Manifest
from strategy_base.models import Bar
from strategy_base.registry import RegisteredStrategy, StrategyRegistry

DEFAULT_FEE_RATE = 0.000085
FEE_SOURCE = "NH선물 수수료 부과 기준(2026-09-07 개정) 개별주식선물 온라인 매매 표준수수료 0.0085%"
MAX_DAYS = 366
MAX_SLIPPAGE_TICKS = 20


class BacktestRejected(Exception):
    """요청을 받아들이지 않았다. `status_code`는 API 응답 코드다."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass(frozen=True)
class LoadedData:
    days: dict[date, list[Bar]]
    last_trading_day: date | None


# (종목코드, 봉 분 단위, 시작일, 종료일, 진행 알림(완료 일수, 전체 일수)) -> 데이터
DataLoader = Callable[[str, int, date, date, Callable[[int, int], None]], LoadedData]


def describe_assumptions(
    settings: Settings, tick_size: float | None = None, slippage_ticks: int | None = None
) -> dict[str, Any]:
    """백테스트의 비용·체결 가정. 실행 기록과 수수료 조회 API가 같은 내용을 쓴다."""
    rate = settings.backtest_fee_rate
    return {
        "fee": {
            "rate": rate,
            "basis": "체결대금(체결가 × 거래승수 × 수량)",
            "source": FEE_SOURCE if rate == DEFAULT_FEE_RATE else "환경변수 BACKTEST_FEE_RATE로 지정",
        },
        "slippage": {
            "ticks": settings.backtest_slippage_ticks if slippage_ticks is None else slippage_ticks,
            "tick_size": tick_size,
            "direction": "시장가 체결마다 불리한 방향",
        },
        "fill": {
            "on_bar": "봉 마감 판단의 시장가 주문은 다음 봉 시가에 전량 체결(그날 마지막 봉이면 그 봉 종가)",
            "on_price": "장중 가격 판단의 시장가 주문은 그 가격에 전량 체결",
            "intrabar_path": "봉마다 시가 → 불리한 극단 → 유리한 극단 → 종가 순으로 호가 단위씩 이동",
        },
        "margin": "증거금과 주문가능수량을 제한하지 않음",
    }


def nh_loader(client: NHClient) -> DataLoader:
    def load(code: str, minutes: int, start: date, end: date, on_progress: Callable[[int, int], None]) -> LoadedData:
        quote = fetch_quote(client, code)
        weekdays = [start + timedelta(days=n) for n in range((end - start).days + 1)]
        weekdays = [day for day in weekdays if day.weekday() < 5]
        days: dict[date, list[Bar]] = {}
        for number, day in enumerate(weekdays, 1):
            bars = fetch_minute_bars(client, code, minutes=minutes, start=day, end=day)
            if bars:
                days[day] = bars
            on_progress(number, len(weekdays))
        return LoadedData(days, quote.last_trading_day)

    return load


class BacktestService:
    def __init__(
        self,
        settings: Settings,
        registry: StrategyRegistry,
        store: RunStore,
        *,
        loader_factory: Callable[[], DataLoader] | None = None,
        probe_factory: Callable[[str, int], ProbeSource] | None = None,
    ):
        self._settings = settings
        self._registry = registry
        self._store = store
        self._loader_factory = loader_factory or (lambda: nh_loader(NHClient(settings)))
        self._probe_factory = probe_factory or (lambda code, minutes: NHProbe(NHClient(settings), code, minutes))
        self._ranges = RangeCache(lambda: datetime.now(KST).date())
        self._lock = threading.Lock()
        self._current: dict[str, str] | None = None
        self._thread: threading.Thread | None = None

    def assumptions(self) -> dict[str, Any]:
        return describe_assumptions(self._settings)

    def available_range(self, strategy_id: str) -> dict[str, Any]:
        """전략의 첫 번째 종목으로 백테스트할 수 있는 기간."""
        registered = self._registry.get(strategy_id)
        if registered is None:
            raise BacktestRejected(404, "전략을 찾을 수 없습니다")
        instrument = registered.manifest.instruments[0]
        if not instrument.code:
            raise BacktestRejected(422, "전략의 종목에 종목코드가 필요합니다")
        if not (self._settings.nh_app_key and self._settings.nh_app_secret):
            raise BacktestRejected(503, "NH_APP_KEY, NH_APP_SECRET 환경변수를 설정하세요")
        found = self._range(instrument.code, registered.manifest.bar.size)
        return {
            "strategy_id": strategy_id,
            "instrument": {"name": instrument.name, "code": instrument.code},
            "start": found.start.isoformat() if found else None,
            "end": found.end.isoformat() if found else None,
            "last_trading_day": found.last_trading_day.isoformat() if found and found.last_trading_day else None,
            "sparse_days": {day.isoformat(): bars for day, bars in found.sparse_days.items()} if found else {},
        }

    def _range(self, code: str, minutes: int) -> AvailableRange | None:
        try:
            return self._ranges.get(code, self._probe_factory(code, minutes), sparse_below(minutes))
        except NHError as error:
            raise BacktestRejected(502, f"가능 기간을 확인하지 못했습니다: {type(error).__name__}") from error

    def current(self) -> dict[str, str] | None:
        """실행 중인 백테스트의 식별자. 없으면 `None`."""
        with self._lock:
            return dict(self._current) if self._current else None

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def start(
        self,
        strategy_id: str,
        start: date,
        end: date,
        initial_capital: float,
        params: dict[str, Any] | None = None,
        slippage_ticks: int | None = None,
    ) -> dict[str, str]:
        registered = self._registry.get(strategy_id)
        if registered is None:
            raise BacktestRejected(404, "전략을 찾을 수 없습니다")
        manifest = registered.manifest
        instrument = manifest.instruments[0]
        if manifest.bar.unit != "minute":
            raise BacktestRejected(422, "분봉 전략만 백테스트할 수 있습니다")
        if not instrument.code or not instrument.multiplier:
            raise BacktestRejected(422, "전략의 종목에 종목코드와 거래승수가 필요합니다")
        self._validate_period(start, end, initial_capital)
        if slippage_ticks is not None and not 0 <= slippage_ticks <= MAX_SLIPPAGE_TICKS:
            raise BacktestRejected(422, f"슬리피지는 0틱부터 {MAX_SLIPPAGE_TICKS}틱까지 입력할 수 있습니다")
        merged = self._merge_params(manifest, params)
        if not (self._settings.nh_app_key and self._settings.nh_app_secret):
            raise BacktestRejected(503, "NH_APP_KEY, NH_APP_SECRET 환경변수를 설정하세요")
        available = self._range(instrument.code, manifest.bar.size)
        if available is None:
            raise BacktestRejected(422, "백테스트할 수 있는 분봉이 없습니다")
        if start < available.start or end > available.end:
            raise BacktestRejected(
                422, f"백테스트할 수 있는 기간은 {available.start.isoformat()}부터 {available.end.isoformat()}까지입니다"
            )

        with self._lock:
            if self._current is not None:
                raise BacktestRejected(409, "이미 실행 중인 백테스트가 있습니다")
            recorder = self._store.start_run(
                strategy_id=strategy_id,
                strategy_name=manifest.name,
                mode="backtest",
                instrument={"name": instrument.name, "code": instrument.code, "multiplier": instrument.multiplier},
                params=merged,
                period={"start": start.isoformat(), "end": end.isoformat()},
                initial_capital=initial_capital,
                assumptions=describe_assumptions(self._settings, slippage_ticks=slippage_ticks),
            )
            self._current = {"strategy_id": strategy_id, "mode": "backtest", "run_id": recorder.run_id}
            self._thread = threading.Thread(
                target=self._job,
                args=(recorder, registered, merged, start, end, initial_capital, slippage_ticks),
                daemon=True,
            )
            self._thread.start()
            return dict(self._current)

    def _validate_period(self, start: date, end: date, initial_capital: float) -> None:
        if initial_capital <= 0:
            raise BacktestRejected(422, "초기자금은 0보다 커야 합니다")
        if start > end:
            raise BacktestRejected(422, "시작일이 종료일보다 늦습니다")
        if end >= datetime.now(KST).date():
            raise BacktestRejected(422, "종료일은 오늘보다 이전이어야 합니다")
        if (end - start).days + 1 > MAX_DAYS:
            raise BacktestRejected(422, f"기간은 {MAX_DAYS}일 이하여야 합니다")

    def _merge_params(self, manifest: Manifest, overrides: dict[str, Any] | None) -> dict[str, Any]:
        unknown = sorted(set(overrides or {}) - set(manifest.parameters))
        if unknown:
            raise BacktestRejected(422, f"전략에 없는 파라미터입니다: {', '.join(unknown)}")
        return {**manifest.default_params(), **(overrides or {})}

    # ---- 백그라운드 실행 ----

    def _job(
        self,
        recorder: RunRecorder,
        registered: RegisteredStrategy,
        params: dict[str, Any],
        start: date,
        end: date,
        initial_capital: float,
        slippage_ticks: int | None,
    ) -> None:
        try:
            self._run(recorder, registered, params, start, end, initial_capital, slippage_ticks)
        except Exception as error:
            recorder.record("event", level="error", text=f"백테스트가 오류로 멈췄습니다: {type(error).__name__}: {error}")
            recorder.finish(status="error")
        finally:
            with self._lock:
                self._current = None

    def _run(
        self,
        recorder: RunRecorder,
        registered: RegisteredStrategy,
        params: dict[str, Any],
        start: date,
        end: date,
        initial_capital: float,
        slippage_ticks: int | None,
    ) -> None:
        manifest = registered.manifest
        instrument = manifest.instruments[0]
        minutes = manifest.bar.size
        recorder.record("event", text="백테스트 시작", start=start.isoformat(), end=end.isoformat())

        def prepare(done: int, total: int) -> None:
            recorder.update_meta(progress={"stage": "prepare", "done": done, "total": total})

        recorder.update_meta(progress={"stage": "prepare", "done": 0, "total": 0})
        loaded = self._loader_factory()(instrument.code or "", minutes, start, end, prepare)
        if not loaded.days:
            raise RuntimeError("조회 기간에 분봉 데이터가 없습니다")

        tick = infer_tick(loaded.days)
        recorder.update_meta(assumptions=describe_assumptions(self._settings, tick, slippage_ticks))
        assumptions = Assumptions(
            fee_rate=self._settings.backtest_fee_rate,
            slippage_ticks=self._settings.backtest_slippage_ticks if slippage_ticks is None else slippage_ticks,
            multiplier=instrument.multiplier or 1,
            tick_size=tick,
        )
        engine = BacktestEngine(
            registered.strategy_class(params),
            recorder,
            assumptions,
            initial_capital=initial_capital,
            minutes=minutes,
            last_trading_day=loaded.last_trading_day,
        )

        def compute(done: int, total: int) -> None:
            recorder.update_meta(progress={"stage": "compute", "done": done, "total": total})

        compute(0, len(loaded.days))
        result = engine.run(loaded.days, compute)
        result["daily_bars"] = daily_bars(loaded.days)
        recorder.record("event", text="백테스트 완료", net_pnl=result["net_pnl"], trades=result["trade_count"])
        recorder.update_meta(progress={"stage": "done", "done": len(loaded.days), "total": len(loaded.days)})
        recorder.finish(result)
