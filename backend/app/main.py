from fastapi import FastAPI

from app.api import health, strategies
from app.config import Settings, load_settings
from strategy_base.registry import StrategyRegistry


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="모의매매·백테스트 API")
    app.state.settings = settings
    app.state.registry = StrategyRegistry(settings.strategies_dir)
    app.include_router(health.router)
    app.include_router(strategies.router)
    return app
