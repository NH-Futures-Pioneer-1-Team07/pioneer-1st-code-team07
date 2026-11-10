"""조합 결과 저장소.

    <root>/<전략 id>/results.jsonl       조합 하나당 한 줄
    <root>/<전략 id>/trades/<id>.jsonl   조합의 거래·체결 기록
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def combo_id(
    strategy_id: str,
    params: dict[str, Any],
    start: str,
    end: str,
    slippage_ticks: int,
    initial_capital: float,
    fee_rate: float,
) -> str:
    """조합의 정의가 같으면 같은 값이 나온다. 기본값과 같은 파라미터를 적어도 결과는 같다."""
    definition = {
        "strategy_id": strategy_id,
        "params": params,
        "start": start,
        "end": end,
        "slippage_ticks": slippage_ticks,
        "initial_capital": initial_capital,
        "fee_rate": fee_rate,
    }
    text = json.dumps(definition, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class SweepStore:
    def __init__(self, root: Path):
        self.root = root

    def folder(self, strategy_id: str) -> Path:
        return self.root / strategy_id

    def results_path(self, strategy_id: str) -> Path:
        return self.folder(strategy_id) / "results.jsonl"

    def trades_path(self, strategy_id: str, result_id: str) -> Path:
        return self.folder(strategy_id) / "trades" / f"{result_id}.jsonl"

    def read_results(self, strategy_id: str) -> list[dict[str, Any]]:
        path = self.results_path(strategy_id)
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    def ids(self, strategy_id: str) -> set[str]:
        return {row["id"] for row in self.read_results(strategy_id)}

    def read_trades(self, strategy_id: str, result_id: str) -> list[dict[str, Any]]:
        path = self.trades_path(strategy_id, result_id)
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    def append(self, strategy_id: str, result: dict[str, Any], trade_lines: list[dict[str, Any]]) -> None:
        """거래 파일을 먼저 쓰고 결과 줄을 덧붙인다. 결과 줄이 있으면 거래 파일도 있다."""
        trades = self.trades_path(strategy_id, result["id"])
        trades.parent.mkdir(parents=True, exist_ok=True)
        temp = trades.with_name(trades.name + ".tmp")
        temp.write_text(
            "".join(json.dumps(line, ensure_ascii=False, default=str) + "\n" for line in trade_lines),
            encoding="utf-8",
        )
        os.replace(temp, trades)
        with self.results_path(strategy_id).open("a", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
