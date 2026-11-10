"""쌓인 조합 결과로 비교표를 만든다. 조합(파라미터)이 행이고, 기간마다 지표 열이 붙는다.

파생 지표(승률, 수수료 비중, 일별 자산 변화율의 샤프 비율)는 저장하지 않고 표를 만들 때 계산한다.
"""

import csv
import json
import math
from pathlib import Path
from typing import Any

from app.sweep.store import SweepStore

METRICS = ("net_pnl", "return_rate", "max_drawdown_rate", "trade_count", "win_rate", "fee_ratio", "sharpe")
SUMMARY_COLUMNS = ("period_count", "positive_periods", "worst_net_pnl", "total_net_pnl")


def win_rate(summary: dict[str, Any]) -> float | None:
    count = summary["trade_count"]
    return summary["win_count"] / count if count else None


def fee_ratio(summary: dict[str, Any]) -> float | None:
    """총손익 대비 수수료. 총손익이 0 이하이면 의미가 없어 비운다."""
    gross = summary["gross_pnl"]
    return summary["fee"] / gross if gross > 0 else None


def sharpe(daily_equity: list[dict[str, Any]], initial_capital: float) -> float | None:
    """일별 자산의 변화율로 계산한 평균/표준편차에 √252를 곱한 값. 변화가 없거나 점이 모자라면 비운다."""
    values = [initial_capital, *[point["equity"] for point in daily_equity]]
    changes = [(b - a) / a for a, b in zip(values, values[1:]) if a]
    if len(changes) < 2:
        return None
    mean = sum(changes) / len(changes)
    variance = sum((c - mean) ** 2 for c in changes) / (len(changes) - 1)
    return mean / math.sqrt(variance) * math.sqrt(252) if variance > 0 else None


def period_label(row: dict[str, Any]) -> str:
    return f"{row['start']}~{row['end']}"


def build_table(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """(열 이름, 행 목록). 조합이 하나도 없으면 열만 돌려준다."""
    identity: dict[str, dict[str, Any]] = {}
    cells: dict[str, dict[str, dict[str, Any]]] = {}
    periods: list[str] = []
    for row in rows:
        key = json.dumps(
            [row["params"], row["slippage_ticks"], row["initial_capital"]], sort_keys=True, ensure_ascii=False
        )
        identity[key] = {**row["params"], "slippage_ticks": row["slippage_ticks"], "initial_capital": row["initial_capital"]}
        label = period_label(row)
        if label not in periods:
            periods.append(label)
        summary = row["summary"]
        cells.setdefault(key, {})[label] = {
            "net_pnl": summary["net_pnl"],
            "return_rate": summary["return_rate"],
            "max_drawdown_rate": summary["max_drawdown_rate"],
            "trade_count": summary["trade_count"],
            "win_rate": win_rate(summary),
            "fee_ratio": fee_ratio(summary),
            "sharpe": sharpe(row["daily_equity"], row["initial_capital"]),
        }
    periods.sort()

    names = list(dict.fromkeys(name for item in identity.values() for name in item))
    varying = [name for name in names if len({json.dumps(item.get(name), sort_keys=True) for item in identity.values()}) > 1]
    columns = [*varying, *SUMMARY_COLUMNS, *[f"{metric}[{label}]" for label in periods for metric in METRICS]]

    table: list[dict[str, Any]] = []
    for key, item in identity.items():
        line: dict[str, Any] = {
            name: json.dumps(item[name], ensure_ascii=False) if isinstance(item[name], list | dict) else item[name]
            for name in varying
        }
        per_period = cells[key]
        pnls = [cell["net_pnl"] for cell in per_period.values()]
        line["period_count"] = len(pnls)
        line["positive_periods"] = sum(1 for value in pnls if value > 0)
        line["worst_net_pnl"] = min(pnls)
        line["total_net_pnl"] = sum(pnls)
        for label in periods:
            for metric in METRICS:
                line[f"{metric}[{label}]"] = per_period.get(label, {}).get(metric)
        table.append(line)
    table.sort(key=lambda line: line["total_net_pnl"], reverse=True)
    return columns, table


def write_table(store: SweepStore, strategy_id: str, path: Path) -> int:
    """`path`에 CSV를 쓰고 행 수를 돌려준다."""
    columns, table = build_table(store.read_results(strategy_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for line in table:
            writer.writerow({name: ("" if value is None else value) for name, value in line.items()})
    return len(table)
