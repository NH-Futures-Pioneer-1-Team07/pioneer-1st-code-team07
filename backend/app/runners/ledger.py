"""진입분별 포지션과 손익 계산. 백테스트와 모의매매가 같은 코드를 쓴다."""

from dataclasses import dataclass
from datetime import datetime

from strategy_base.models import Lot, Side


@dataclass
class Position:
    side: Side
    open_quantity: int = 0
    entry_quantity: int = 0
    entry_value: float = 0.0
    exit_quantity: int = 0
    exit_value: float = 0.0
    gross_pnl: float = 0.0
    fee: float = 0.0
    opened_at: datetime | None = None

    @property
    def avg_entry(self) -> float:
        return self.entry_value / self.entry_quantity if self.entry_quantity else 0.0


@dataclass(frozen=True)
class ClosedTrade:
    """진입분 하나의 진입부터 청산까지."""

    entry_id: str
    side: Side
    quantity: int
    entry_price: float
    exit_price: float
    gross_pnl: float
    fee: float
    net_pnl: float
    opened_at: datetime | None


@dataclass(frozen=True)
class Applied:
    """체결을 원장에 반영한 결과. `trade`는 이 체결로 진입분이 모두 청산됐을 때만 있다."""

    quantity: int
    fee: float
    trade: ClosedTrade | None = None


class Ledger:
    def __init__(self, *, multiplier: int, fee_rate: float, initial_capital: float = 0.0):
        self.multiplier = multiplier
        self.fee_rate = fee_rate
        self.initial_capital = initial_capital
        self.positions: dict[str, Position] = {}
        self.gross_pnl = 0.0
        self.fee = 0.0
        self.trades = 0
        self.wins = 0
        self.losses = 0

    def fee_for(self, price: float, quantity: int) -> float:
        return price * self.multiplier * quantity * self.fee_rate

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.fee

    def apply_entry(
        self, entry_id: str, side: Side, quantity: int, price: float, moment: datetime
    ) -> Applied | None:
        """진입 체결을 반영한다. 같은 진입분의 방향과 다르면 `None`이다."""
        position = self.positions.get(entry_id)
        if position is not None and position.side != side:
            return None
        if position is None:
            position = self.positions[entry_id] = Position(side, opened_at=moment)
        fee = self.fee_for(price, quantity)
        position.open_quantity += quantity
        position.entry_quantity += quantity
        position.entry_value += price * quantity
        position.fee += fee
        self.fee += fee
        return Applied(quantity, fee)

    def apply_exit(
        self, entry_id: str, side: Side, quantity: int, price: float, moment: datetime
    ) -> Applied | None:
        """청산 체결을 반영한다. 진입분이 없거나 방향이 같으면 `None`이다. 수량은 보유분까지만 반영한다."""
        position = self.positions.get(entry_id)
        if position is None or position.side == side:
            return None
        quantity = min(quantity, position.open_quantity)
        if quantity <= 0:
            return None
        sign = 1 if position.side == Side.BUY else -1
        gross = (price - position.avg_entry) * sign * quantity * self.multiplier
        fee = self.fee_for(price, quantity)
        position.open_quantity -= quantity
        position.exit_quantity += quantity
        position.exit_value += price * quantity
        position.gross_pnl += gross
        position.fee += fee
        self.gross_pnl += gross
        self.fee += fee
        trade = self._close(entry_id, position) if position.open_quantity == 0 else None
        return Applied(quantity, fee, trade)

    def _close(self, entry_id: str, position: Position) -> ClosedTrade:
        net = position.gross_pnl - position.fee
        self.trades += 1
        if net > 0:
            self.wins += 1
        elif net < 0:
            self.losses += 1
        trade = ClosedTrade(
            entry_id=entry_id,
            side=position.side,
            quantity=position.entry_quantity,
            entry_price=position.avg_entry,
            exit_price=position.exit_value / position.exit_quantity,
            gross_pnl=position.gross_pnl,
            fee=position.fee,
            net_pnl=net,
            opened_at=position.opened_at,
        )
        del self.positions[entry_id]
        return trade

    def lots(self) -> list[Lot]:
        return [
            Lot(entry_id, position.side, position.open_quantity, position.avg_entry)
            for entry_id, position in self.positions.items()
            if position.open_quantity > 0
        ]

    def net_quantity(self) -> int:
        """보유 순수량. 매수는 양수, 매도는 음수다."""
        return sum(
            position.open_quantity if position.side == Side.BUY else -position.open_quantity
            for position in self.positions.values()
        )

    def unrealized(self, price: float) -> float:
        return sum(
            (price - position.avg_entry)
            * (1 if position.side == Side.BUY else -1)
            * position.open_quantity
            * self.multiplier
            for position in self.positions.values()
        )

    def equity(self, price: float) -> float:
        return self.initial_capital + self.net_pnl + self.unrealized(price)
