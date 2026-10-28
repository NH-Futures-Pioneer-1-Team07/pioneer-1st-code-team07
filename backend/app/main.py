from fastapi import FastAPI

from app.api import health, runs, strategies
from app.config import Settings, load_settings
from app.records.store import RunStore
from strategy_base.registry import StrategyRegistry


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="모의매매·백테스트 API")
    app.state.settings = settings
    app.state.registry = StrategyRegistry(settings.strategies_dir)
    app.state.run_store = RunStore(settings.runs_dir)
    app.state.run_store.mark_interrupted()
    app.include_router(health.router)
    app.include_router(strategies.router)
    app.include_router(runs.router)
    return app
