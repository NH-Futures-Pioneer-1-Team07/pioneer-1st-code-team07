"""종목 시세·차트·호가 조회. 화면이 REST로 부른다."""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from app.config import Settings
from app.nh.auth import KST
from app.nh.client import NHClient
from app.nh.domestic.market_hours import market_session
from app.nh.domestic.quotes import MINUTE_PATH, PRICE_PATH, TimeMarks, parse_bar
from app.nh.errors import NHError
from app.nh.rate_limit import Limit
from app.nh.realtime_data import BookLevel, OrderBook
from app.nh.values import count, day, number, text

DAILY_PATH = "/trade/v1/domestic/chart-daily"
BOOK_PATH = "/trade/v1/domestic/price-bid"
DAY_SESSION_EXCHANGE = "KSP"
MINUTE_INTERVALS = (1, 3, 5, 10, 15, 30, 60)
INTERVALS = tuple(str(minutes) for minutes in MINUTE_INTERVALS) + ("day",)


@dataclass(frozen=True)
class QuoteDetail:
    code: str
    name: str
    contract: str | None
    expiry: date | None
    last_price: float | None
    change: float | None
    change_rate: float | None
    volume: int | None
    open: float | None
    high: float | None
    low: float | None
    prev_close: float | None
    upper_limit: float | None
    lower_limit: float | None
    multiplier: int | None
    remaining_days: int | None


@dataclass(frozen=True)
class Candle:
    """봉 하나. 분봉의 `time`은 봉이 시작한 시각, 일봉은 그날 0시다."""

    time: datetime
    open: float | None
    high: float
    low: float
    close: float
    volume: int


def _signed(value: Any, sign: str) -> float | None:
    parsed = number(value)
    if parsed is None:
        return None
    return -abs(parsed) if sign.strip() == "-" else parsed


def fetch_quote_detail(client: NHClient, code: str) -> QuoteDetail:
    body = client.call(PRICE_PATH, {"sym": code}, Limit.QUOTE)
    sign = text(body.get("chg_sign"))
    expiry = day(body.get("lst_trd_dt"))
    return QuoteDetail(
        code=code,
        name=" ".join(text(body.get("sym_nm")).split()),
        contract=f"{expiry.year}.{expiry.month:02d}" if expiry else None,
        expiry=expiry,
        last_price=number(body.get("last_pric")),
        change=_signed(body.get("chg"), sign),
        change_rate=_signed(body.get("rt"), sign),
        volume=count(body.get("trd_qty")),
        open=number(body.get("open_pric")),
        high=number(body.get("high_pric")),
        low=number(body.get("low_pric")),
        prev_close=number(body.get("ref_pric")),
        upper_limit=number(body.get("up")),
        lower_limit=number(body.get("lo")),
        multiplier=count(body.get("mltplr")),
        remaining_days=count(body.get("rem_dy")),
    )


def fetch_recent_bars(
    client: NHClient, code: str, *, minutes: int, quantity: int, time_marks: TimeMarks = "start"
) -> list[Candle]:
    """주간 분봉을 날짜와 관계없이 최근 `quantity`개, 오래된 순서로 돌려준다."""
    payload = {
        "nght_tp": "1",
        "sym": code,
        "inq_strt_dt": "00000000",
        "strt_tm": "000000",
        "inq_ed_dt": "99999999",
        "ed_tm": "235959",
        "req_qty": str(quantity),
        "dcnt": str(minutes),
        "cidx_yn": "0",
        "nxt_key": "99999999",
        "fut_cidx_exp_mod": "0",
    }
    body = client.call(MINUTE_PATH, payload, Limit.QUOTE)
    shift = timedelta(minutes=minutes) if time_marks == "end" else timedelta()
    bars = [bar for row in _rows(body) if (bar := parse_bar(row, shift)) is not None]
    bars.sort(key=lambda bar: bar.time)
    return [Candle(b.time, b.open, b.high, b.low, b.close, b.volume) for b in bars[-quantity:]]


def fetch_daily_bars(client: NHClient, code: str, *, quantity: int) -> list[Candle]:
    payload = {
        "nght_tp": "1",
        "sym": code,
        "inq_strt_dt": "00000000",
        "inq_ed_dt": "99999999",
        "req_qty": str(quantity),
        "cidx_yn": "0",
        "nxt_key": "99999999",
        "fut_cidx_exp_mod": "0",
    }
    body = client.call(DAILY_PATH, payload, Limit.QUOTE)
    candles = []
    for row in _rows(body):
        when = day(row.get("occurs1_ref_dt"))
        high, low, close = number(row.get("occurs1_high_pric")), number(row.get("occurs1_low_pric")), number(row.get("occurs1_close_pric"))
        volume = count(row.get("occurs1_cum_trd_qty"))
        if when is None or None in (high, low, close, volume):
            continue
        candles.append(
            Candle(datetime(when.year, when.month, when.day), number(row.get("occurs1_open_pric")), high, low, close, volume)
        )
    candles.sort(key=lambda candle: candle.time)
    return candles[-quantity:]


def fetch_book(client: NHClient, code: str) -> tuple[OrderBook, float | None, float | None]:
    """주간 호가. (호가, 현재가, 등락률)을 돌려준다."""
    body = client.call(BOOK_PATH, {"exch_cd": DAY_SESSION_EXCHANGE, "sym": code}, Limit.QUOTE)
    levels = [
        BookLevel(
            ask_price=number(row.get("occurs1_ask_best_pric")),
            ask_quantity=count(row.get("occurs1_ask_qty")),
            bid_price=number(row.get("occurs1_bid_best_pric")),
            bid_quantity=count(row.get("occurs1_bid_qty")),
        )
        for row in _rows(body)
    ]
    book = OrderBook(
        code=text(body.get("sym")) or code,
        time=text(body.get("qt_tm")),
        total_ask_quantity=count(body.get("ask_qty")),
        total_bid_quantity=count(body.get("bid_qty")),
        levels=levels,
    )
    return book, number(body.get("last_pric")), number(body.get("rt"))


def _rows(body: dict[str, Any]) -> list[dict[str, Any]]:
    rows = body.get("Occurs1") or []
    if not isinstance(rows, list):
        raise NHError("응답의 Occurs1 형식이 올바르지 않습니다")
    return rows


class TtlCache:
    """같은 요청이 몰려도 NH를 자주 부르지 않도록 짧게 보관한다."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._values: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any, ttl: float, make: Callable[[], Any]) -> Any:
        with self._lock:
            hit = self._values.get(key)
            now = self._clock()
            if hit is not None and now - hit[0] < ttl:
                return hit[1]
            value = make()
            self._values[key] = (now, value)
            return value


class MarketService:
    QUOTE_TTL = 1.0
    BOOK_TTL = 1.0
    CANDLE_TTL = 2.0

    def __init__(
        self,
        settings: Settings,
        *,
        client: NHClient | None = None,
        clock: Callable[[], float] = time.monotonic,
        now: Callable[[], datetime] = lambda: datetime.now(KST).replace(tzinfo=None),
    ):
        self._settings = settings
        self._now = now
        self._client = client
        self._cache = TtlCache(clock)

    def _nh(self) -> NHClient:
        if self._client is None:
            self._client = NHClient(self._settings)
        return self._client

    def has_credentials(self) -> bool:
        return bool(self._settings.nh_app_key and self._settings.nh_app_secret)

    def quote(self, code: str) -> dict[str, Any]:
        detail: QuoteDetail = self._cache.get(
            ("quote", code), self.QUOTE_TTL, lambda: fetch_quote_detail(self._nh(), code)
        )
        return {
            "code": detail.code,
            "name": detail.name,
            "contract": detail.contract,
            "expiry": detail.expiry.isoformat() if detail.expiry else None,
            "price": detail.last_price,
            "change": detail.change,
            "change_rate": detail.change_rate,
            "volume": detail.volume,
            "open": detail.open,
            "high": detail.high,
            "low": detail.low,
            "prev_close": detail.prev_close,
            "upper_limit": detail.upper_limit,
            "lower_limit": detail.lower_limit,
            "multiplier": detail.multiplier,
            "remaining_days": detail.remaining_days,
            "market_session": market_session(detail.name, self._now()),
        }

    def candles(self, code: str, interval: str, quantity: int) -> list[dict[str, Any]]:
        def make() -> list[Candle]:
            if interval == "day":
                return fetch_daily_bars(self._nh(), code, quantity=quantity)
            return fetch_recent_bars(self._nh(), code, minutes=int(interval), quantity=quantity)

        candles: list[Candle] = self._cache.get(("candles", code, interval, quantity), self.CANDLE_TTL, make)
        return [
            {
                "time": c.time.date().isoformat() if interval == "day" else c.time.isoformat(),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in candles
        ]

    def orderbook(self, code: str) -> dict[str, Any]:
        book, price, rate = self._cache.get(("book", code), self.BOOK_TTL, lambda: fetch_book(self._nh(), code))
        return {
            "code": book.code,
            "time": book.time,
            "price": price,
            "change_rate": rate,
            "total_ask_quantity": book.total_ask_quantity,
            "total_bid_quantity": book.total_bid_quantity,
            "levels": [
                {
                    "ask_price": level.ask_price,
                    "ask_quantity": level.ask_quantity,
                    "bid_price": level.bid_price,
                    "bid_quantity": level.bid_quantity,
                }
                for level in book.levels
            ],
        }
