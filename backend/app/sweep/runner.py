"""조합을 백테스트하고 결과를 저장한다. 서버 없이 엔진을 직접 부르며, 같은 기간의 분봉은 한 번만 받는다."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from time import monotonic
from typing import Any

from app.config import Settings
from app.data.vix import load as load_vix
from app.nh.auth import KST
from app.runners.backtest import Assumptions, BacktestEngine, infer_tick
from app.runners.inputs import ExtraInputs
from app.runners.minute_backtest import MinuteBacktestEngine
from app.runners.series import DailyFetcher, days_needed, warmup_start
from app.runners.service import HISTORY_DAYS, MAX_SLIPPAGE_TICKS, DataLoader, LoadedData
from app.sweep.recorder import SweepRecorder
from app.sweep.spec import Combo, SweepSpec, expand
from app.sweep.store import SweepStore, combo_id
from strategy_base.models import Bar
from strategy_base.registry import RegisteredStrategy, StrategyRegistry

SUMMARY_FIELDS = (
    "net_pnl",
    "gross_pnl",
    "fee",
    "return_rate",
    "final_equity",
    "max_drawdown",
    "max_drawdown_rate",
    "trade_count",
    "win_count",
    "loss_count",
    "days",
    "bars",
)


class SweepError(Exception):
    """요청을 실행할 수 없다. 데이터를 받기 전에 확인할 수 있는 문제다."""


@dataclass
class SweepReport:
    ran: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class _Planned:
    combo: Combo
    params: dict[str, Any]
    result_id: str


class SweepRunner:
    def __init__(
        self,
        settings: Settings,
        registry: StrategyRegistry,
        store: SweepStore,
        loader: DataLoader,
        daily_fetcher: DailyFetcher,
        *,
        today: Callable[[], date] | None = None,
        log: Callable[[str], None] = lambda message: None,
    ):
        self._settings = settings
        self._registry = registry
        self._store = store
        self._loader = loader
        self._daily_fetcher = daily_fetcher
        self._today = today or (lambda: datetime.now(KST).date())
        self._log = log

    def plan(self, spec: SweepSpec) -> tuple[RegisteredStrategy, int, list[_Planned], list[_Planned]]:
        """요청을 검증하고 (전략, 슬리피지, 실행할 조합, 건너뛸 조합)을 돌려준다. 데이터는 받지 않는다."""
        registered = self._registry.get(spec.strategy_id)
        if registered is None:
            raise SweepError(f"전략을 찾을 수 없습니다: {spec.strategy_id}")
        manifest = registered.manifest
        instrument = manifest.instruments[0]
        if manifest.bar.unit != "minute":
            raise SweepError("분봉 전략만 백테스트할 수 있습니다")
        if not instrument.code or not instrument.multiplier:
            raise SweepError("전략의 종목에 종목코드와 거래승수가 필요합니다")
        slippage = self._settings.backtest_slippage_ticks if spec.slippage_ticks is None else spec.slippage_ticks
        if not 0 <= slippage <= MAX_SLIPPAGE_TICKS:
            raise SweepError(f"슬리피지는 0틱부터 {MAX_SLIPPAGE_TICKS}틱까지 입력할 수 있습니다")
        for period in spec.periods:
            if period.end >= self._today():
                raise SweepError(f"종료일은 오늘보다 이전이어야 합니다: {period.end}")

        known = self._store.ids(spec.strategy_id)
        todo: list[_Planned] = []
        skip: list[_Planned] = []
        for combo in expand(spec):
            problem = manifest.override_problem(combo.overrides)
            if problem:
                raise SweepError(f"{combo.overrides}: {problem}")
            params = {**manifest.default_params(), **combo.overrides}
            if manifest.backtest and "tick_size" in params and params["tick_size"] != manifest.backtest.tick_size:
                raise SweepError("전략의 틱 간격과 백테스트의 틱 간격이 일치해야 합니다")
            result_id = combo_id(
                spec.strategy_id,
                params,
                combo.period.start.isoformat(),
                combo.period.end.isoformat(),
                slippage,
                spec.initial_capital,
                self._settings.backtest_fee_rate,
            )
            planned = _Planned(combo, params, result_id)
            (skip if result_id in known else todo).append(planned)
        return registered, slippage, todo, skip

    def run(self, spec: SweepSpec) -> SweepReport:
        registered, slippage, todo, skip = self.plan(spec)
        report = SweepReport(skipped=[item.result_id for item in skip])
        if not todo:
            return report
        manifest = registered.manifest
        instrument = manifest.instruments[0]
        minutes = manifest.bar.size
        code = instrument.code or ""
        first = min(item.combo.period.start for item in todo)
        last = max(item.combo.period.end for item in todo)

        self._log(f"분봉 준비: {first} ~ {last}")
        warm_from = warmup_start(first, HISTORY_DAYS) if manifest.history_bars else first
        loaded = self._loader(code, minutes, warm_from, last, lambda done, total: None)
        prices: LoadedData | None = None
        if manifest.backtest is not None:
            prices = self._loader(code, manifest.backtest.price_minutes, first, last, lambda done, total: None)
        series: dict[str, list[Bar]] = {}
        if manifest.series:
            bars = self._daily_fetcher(instrument, days_needed(first, self._today()))
            series = {name: bars for name in manifest.series}
        extras = ExtraInputs(series=series, vix=load_vix(), margin=instrument.margin)

        for number, item in enumerate(todo, 1):
            label = f"[{number}/{len(todo)}] {item.result_id} {item.combo.overrides or '기본값'} {item.combo.period.start}~{item.combo.period.end}"
            try:
                started = monotonic()
                line, trades = self._run_one(registered, item, slippage, spec.initial_capital, loaded, prices, extras)
                line["elapsed_seconds"] = round(monotonic() - started, 2)
                self._store.append(spec.strategy_id, line, trades)
                report.ran.append(item.result_id)
                self._log(f"{label} 순손익 {line['summary']['net_pnl']:,.0f} 거래 {line['summary']['trade_count']} ({line['elapsed_seconds']}초)")
            except Exception as error:  # 조합 하나의 실패가 나머지를 막지 않게 한다
                report.failed[item.result_id] = f"{type(error).__name__}: {error}"
                self._log(f"{label} 실패 — {report.failed[item.result_id]}")
        return report

    def _run_one(
        self,
        registered: RegisteredStrategy,
        item: _Planned,
        slippage: int,
        initial_capital: float,
        loaded: LoadedData,
        prices: LoadedData | None,
        extras: ExtraInputs,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        manifest = registered.manifest
        instrument = manifest.instruments[0]
        minutes = manifest.bar.size
        period = item.combo.period
        days = {day: loaded.days[day] for day in sorted(loaded.days) if period.start <= day <= period.end}
        if not days:
            raise RuntimeError("조회 기간에 분봉 데이터가 없습니다")
        extra: dict[str, Any] = {}
        engine_type: type[BacktestEngine] = BacktestEngine
        if prices is not None:
            minute_days = {day: bars for day, bars in prices.days.items() if day in days}
            if set(minute_days) != set(days):
                raise ValueError("신호 봉과 1분 가격 자료의 거래일이 일치하지 않습니다")
            extra["minute_days"] = minute_days
            engine_type = MinuteBacktestEngine
        if manifest.history_bars:
            before = [bar for day in sorted(loaded.days) if day < period.start for bar in loaded.days[day]]
            extra["history"] = before
            extra["history_bars"] = manifest.history_bars
        tick = manifest.backtest.tick_size if manifest.backtest else instrument.tick_size or infer_tick(days)
        recorder = SweepRecorder()
        engine = engine_type(
            registered.strategy_class(item.params),
            recorder,  # type: ignore[arg-type]
            Assumptions(
                fee_rate=self._settings.backtest_fee_rate,
                slippage_ticks=slippage,
                multiplier=instrument.multiplier or 1,
                tick_size=tick,
            ),
            initial_capital=initial_capital,
            minutes=minutes,
            last_trading_day=loaded.last_trading_day,
            extras=extras,
            **extra,
        )
        result = engine.run(days)
        if len(recorder.trades) != result["trade_count"]:
            raise RuntimeError(f"거래 기록 {len(recorder.trades)}건이 결과의 거래 수 {result['trade_count']}건과 다릅니다")
        line = {
            "id": item.result_id,
            "strategy_id": registered.id,
            "params": item.params,
            "start": period.start.isoformat(),
            "end": period.end.isoformat(),
            "slippage_ticks": slippage,
            "initial_capital": initial_capital,
            "fee_rate": self._settings.backtest_fee_rate,
            "summary": {name: result[name] for name in SUMMARY_FIELDS},
            "daily_equity": result["equity_curve"],
            "created_at": datetime.now(KST).isoformat(timespec="seconds"),
        }
        return line, [*recorder.trades, *recorder.fills]
