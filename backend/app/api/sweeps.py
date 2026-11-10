import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.sweep.store import SweepStore
from strategy_base.manifest import STRATEGY_ID_PATTERN

router = APIRouter(prefix="/api/sweeps")

RESULT_ID = re.compile(r"^[0-9a-f]{16}$")
MAX_IDS = 60


def _store(request: Request) -> SweepStore:
    return request.app.state.sweeps


def _strategy(strategy_id: str) -> str:
    if not STRATEGY_ID_PATTERN.match(strategy_id):
        raise HTTPException(404, "전략을 찾을 수 없습니다")
    return strategy_id


@router.get("/{strategy_id}/results")
def get_results(strategy_id: str, request: Request, ids: str = "") -> list[dict[str, Any]]:
    """지정한 조합 결과(정의, 요약, 일별 자산). `ids`는 쉼표로 구분한 결과 id이고 요청한 순서로 돌려준다. 없는 id는 빠진다."""
    strategy_id = _strategy(strategy_id)
    wanted = [item for item in ids.split(",") if item]
    if not wanted or len(wanted) > MAX_IDS:
        raise HTTPException(422, f"ids에 결과 id를 1개 이상 {MAX_IDS}개 이하로 쉼표로 구분해 적어야 합니다")
    if any(not RESULT_ID.match(item) for item in wanted):
        raise HTTPException(422, "결과 id는 16자리 소문자 16진수여야 합니다")
    found = {row["id"]: row for row in _store(request).read_results(strategy_id)}
    return [found[item] for item in wanted if item in found]


@router.get("/{strategy_id}/trades/{result_id}")
def get_trades(strategy_id: str, result_id: str, request: Request) -> dict[str, list[dict[str, Any]]]:
    """조합의 거래(`trades`)와 체결(`fills`). 거래는 청산 시각순이다."""
    strategy_id = _strategy(strategy_id)
    if not RESULT_ID.match(result_id):
        raise HTTPException(404, "거래 기록을 찾을 수 없습니다")
    lines = _store(request).read_trades(strategy_id, result_id)
    if not lines:
        raise HTTPException(404, "거래 기록을 찾을 수 없습니다")
    return {
        "trades": [line for line in lines if line.get("kind") == "trade"],
        "fills": [line for line in lines if line.get("kind") == "fill"],
    }
