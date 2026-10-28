from fastapi import FastAPI

from app.api import backtests, health, market, runs, strategies, trading
from app.config import Settings, load_settings
from app.nh.market import MarketService
from app.records.store import RunStore
from app.runners.paper_service import PaperService
from app.runners.service import BacktestService
from strategy_base.registry import StrategyRegistry


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="모의매매·백테스트 API")
    app.state.settings = settings
    app.state.registry = StrategyRegistry(settings.strategies_dir)
    app.state.run_store = RunStore(settings.runs_dir)
    app.state.run_store.mark_interrupted()
    app.state.backtests = BacktestService(settings, app.state.registry, app.state.run_store)
    app.state.trading = PaperService(settings, app.state.registry, app.state.run_store)
    app.state.market = MarketService(settings)
    app.include_router(health.router)
    app.include_router(strategies.router)
    app.include_router(runs.router)
    app.include_router(backtests.router)
    app.include_router(trading.router)
    app.include_router(market.router)
    return app
