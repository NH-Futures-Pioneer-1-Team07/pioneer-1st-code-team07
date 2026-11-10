"""조합 탐색 명령.

    uv run python -m app.sweep run <요청.json> [--dry-run]
    uv run python -m app.sweep table <전략 id> [--name 이름] [--out 경로]
    uv run python -m app.sweep range <전략 id>
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from app.config import ConfigError, Settings, load_settings
from app.nh.auth import KST
from app.nh.client import NHClient
from app.records.store import RunStore
from app.runners.series import nh_daily_fetcher
from app.runners.service import BacktestRejected, BacktestService, nh_loader, overseas_loader
from app.sweep.cache import CachedLoader
from app.sweep.runner import SweepError, SweepRunner
from app.sweep.spec import SpecError, load_spec
from app.sweep.store import SweepStore
from app.sweep.table import write_table
from strategy_base.registry import StrategyRegistry


def _today():
    return datetime.now(KST).date()


def _loader(settings: Settings, instrument):
    if instrument.market == "overseas":
        inner = overseas_loader(NHClient(settings, market="overseas"), instrument.exchange or "")
    else:
        inner = nh_loader(NHClient(settings))
    return CachedLoader(inner, settings.minute_cache_dir, instrument.market, _today)


def _run(settings: Settings, args: argparse.Namespace) -> int:
    spec = load_spec(Path(args.spec))
    registry = StrategyRegistry(settings.strategies_dir)
    registered = registry.get(spec.strategy_id)
    if registered is None:
        raise SweepError(f"전략을 찾을 수 없습니다: {spec.strategy_id}")
    store = SweepStore(settings.sweeps_dir)
    runner = SweepRunner(
        settings,
        registry,
        store,
        _loader(settings, registered.manifest.instruments[0]),
        nh_daily_fetcher(settings),
        log=print,
    )
    if args.dry_run:
        _, slippage, todo, skip = runner.plan(spec)
        print(f"실행 {len(todo)}건, 건너뜀 {len(skip)}건 (슬리피지 {slippage}틱)")
        return 0
    report = runner.run(spec)
    print(f"완료 — 실행 {len(report.ran)}건, 건너뜀 {len(report.skipped)}건, 실패 {len(report.failed)}건")
    return 1 if report.failed else 0


def _table(settings: Settings, args: argparse.Namespace) -> int:
    store = SweepStore(settings.sweeps_dir)
    if not store.read_results(args.strategy_id):
        raise SweepError(f"저장된 조합 결과가 없습니다: {args.strategy_id}")
    path = Path(args.out) if args.out else settings.reports_dir / args.strategy_id / args.name / "table.csv"
    rows = write_table(store, args.strategy_id, path)
    print(f"{rows}개 조합을 {path}에 저장했습니다")
    return 0


def _range(settings: Settings, args: argparse.Namespace) -> int:
    service = BacktestService(settings, StrategyRegistry(settings.strategies_dir), RunStore(settings.runs_dir))
    try:
        print(json.dumps(service.available_range(args.strategy_id), ensure_ascii=False, indent=2))
    except BacktestRejected as rejected:
        raise SweepError(rejected.message) from rejected
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.sweep", description="전략 파라미터 조합 탐색")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="요청 파일의 조합을 백테스트하고 결과를 쌓는다")
    run.add_argument("spec", help="요청 JSON 파일")
    run.add_argument("--dry-run", action="store_true", help="데이터를 받지 않고 실행·건너뛸 조합 수만 보여준다")
    table = commands.add_parser("table", help="쌓인 결과로 비교표(CSV)를 만든다")
    table.add_argument("strategy_id")
    table.add_argument("--name", default="default", help="reports/<전략>/<이름>/table.csv의 이름")
    table.add_argument("--out", help="저장 경로를 직접 지정한다")
    available = commands.add_parser("range", help="전략 종목의 백테스트 가능 기간을 조회한다")
    available.add_argument("strategy_id")
    args = parser.parse_args(argv)
    try:
        settings = load_settings()
        return {"run": _run, "table": _table, "range": _range}[args.command](settings, args)
    except (ConfigError, SpecError, SweepError) as error:
        print(f"오류: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
