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
from app.nh.overseas import account as overseas_account
from app.nh.overseas import orders as overseas_orders
from app.nh.overseas import quotes as overseas_quotes
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


class OverseasNHBroker:
    """한 해외 종목에 대한 NH 호출. 결과 형식은 `NHBroker`와 같다."""

    def __init__(self, client: NHClient, exchange: str, code: str, minutes: int, currency: str = "USD"):
        self._client = client
        self.exchange = exchange
        self.code = code
        self.minutes = minutes
        self.currency = currency
        self.environment = client.environment

    def fetch_bars(self, day: date) -> list[Bar]:
        return overseas_quotes.fetch_minute_bars(
            self._client, self.exchange, self.code, minutes=self.minutes, start=day, end=day
        )

    def fetch_quote(self) -> Quote:
        return overseas_quotes.fetch_quote(self._client, self.exchange, self.code)

    def positions(self) -> list[Position]:
        return overseas_account.fetch_positions(self._client)

    def open_orders(self) -> list[OrderRecord]:
        return overseas_account.fetch_orders(self._client, open_only=True)

    def orders(self) -> list[OrderRecord]:
        return overseas_account.fetch_orders(self._client)

    def deposit(self) -> Deposit:
        return overseas_account.fetch_deposit(self._client, self.currency)

    def orderable(self, side: Side, price: float) -> OrderableQuantity:
        return overseas_account.fetch_orderable_quantity(self._client, self.code, side, price)

    def place(self, side: Side, quantity: int) -> str:
        return overseas_orders.place_order(self._client, self.code, side, quantity)

    def cancel(self, side: Side, quantity: int, order_no: str) -> str:
        return overseas_orders.cancel_order(self._client, self.code, side, quantity, order_no)
