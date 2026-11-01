"""모의매매가 쓰는 NH 기능의 묶음. 세션은 이 인터페이스만 알고, 테스트는 가짜로 바꿔 끼운다."""

from datetime import date
from typing import Protocol

from app.nh.client import NHClient
from app.nh.domestic.account import (
    Deposit,
    OrderableQuantity,
    OrderRecord,
    Position,
    fetch_deposit,
    fetch_orderable_quantity,
    fetch_orders,
    fetch_positions,
)
from app.nh.domestic.orders import cancel_order, place_order
from app.nh.domestic.quotes import Quote, fetch_minute_bars, fetch_quote
from strategy_base.models import Bar, Side


class Broker(Protocol):
    """모두 동기 호출이다. 세션이 별도 스레드에서 부른다."""

    environment: str

    def fetch_bars(self, day: date) -> list[Bar]: ...

    def fetch_quote(self) -> Quote: ...

    def positions(self) -> list[Position]: ...

    def open_orders(self) -> list[OrderRecord]: ...

    def orders(self) -> list[OrderRecord]: ...

    def deposit(self) -> Deposit: ...

    def orderable(self, side: Side, price: float) -> OrderableQuantity: ...

    def place(self, side: Side, quantity: int) -> str: ...

    def cancel(self, side: Side, quantity: int, order_no: str) -> str: ...


class NHBroker:
    """한 종목에 대한 NH 호출."""

    def __init__(self, client: NHClient, code: str, minutes: int):
        self._client = client
        self.code = code
        self.minutes = minutes
        self.environment = client.environment

    def fetch_bars(self, day: date) -> list[Bar]:
        return fetch_minute_bars(self._client, self.code, minutes=self.minutes, start=day, end=day)

    def fetch_quote(self) -> Quote:
        return fetch_quote(self._client, self.code)

    def positions(self) -> list[Position]:
        return fetch_positions(self._client)

    def open_orders(self) -> list[OrderRecord]:
        return fetch_orders(self._client, open_only=True)

    def orders(self) -> list[OrderRecord]:
        return fetch_orders(self._client)

    def deposit(self) -> Deposit:
        return fetch_deposit(self._client)

    def orderable(self, side: Side, price: float) -> OrderableQuantity:
        return fetch_orderable_quantity(self._client, self.code, side, price)

    def place(self, side: Side, quantity: int) -> str:
        return place_order(self._client, self.code, side, quantity)

    def cancel(self, side: Side, quantity: int, order_no: str) -> str:
        return cancel_order(self._client, self.code, side, quantity, order_no)
