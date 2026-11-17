"""엔진이 호출하는 `record`만 받는 메모리 기록기. 거래(`trade`)와 체결(`fill`)만 모으고 나머지는 버린다.

진입·청산 이유는 같은 `entry_id`의 체결에서 읽어 거래(`entry_reason`, `exit_reason`)에만 남긴다.

봉마다 남는 판단(`decision`)이 백테스트 기록 용량의 대부분이라 조합 탐색에서는 저장하지 않는다.
시장가 주문은 모두 체결되어 주문(`order`)은 체결과 같은 내용이므로 이것도 저장하지 않는다.
"""

from datetime import datetime
from typing import Any


class SweepRecorder:
    def __init__(self) -> None:
        self.fills: list[dict[str, Any]] = []
        self.trades: list[dict[str, Any]] = []
        self._entry_reason: dict[str, Any] = {}
        self._last_reason: dict[str, Any] = {}

    def record(self, kind: str, time: datetime | None = None, **fields: Any) -> None:
        if kind == "fill":
            self._fill(time, fields)
        elif kind == "trade":
            self._trade(time, fields)

    def _fill(self, time: datetime | None, fields: dict[str, Any]) -> None:
        entry_id = fields["entry_id"]
        if fields["intent"] == "entry":
            self._entry_reason.setdefault(entry_id, fields.get("reason"))
        self._last_reason[entry_id] = fields.get("reason")
        self.fills.append(
            {
                "kind": "fill",
                "time": time.isoformat() if time else None,
                "side": fields["side"],
                "quantity": fields["quantity"],
                "price": fields["price"],
                "raw_price": fields["raw_price"],
                "fee": fields["fee"],
                "intent": fields["intent"],
                "entry_id": entry_id,
                "source": fields.get("source"),
            }
        )

    def _trade(self, time: datetime | None, fields: dict[str, Any]) -> None:
        entry_id = fields["entry_id"]
        self.trades.append(
            {
                "kind": "trade",
                "entry_id": entry_id,
                "side": fields["side"],
                "quantity": fields["quantity"],
                "opened_at": fields.get("opened_at"),
                "closed_at": time.isoformat() if time else None,
                "entry_price": fields["entry_price"],
                "exit_price": fields["exit_price"],
                "gross_pnl": fields["gross_pnl"],
                "fee": fields["fee"],
                "net_pnl": fields["net_pnl"],
                "entry_reason": self._entry_reason.get(entry_id),
                "exit_reason": self._last_reason.get(entry_id),
            }
        )
