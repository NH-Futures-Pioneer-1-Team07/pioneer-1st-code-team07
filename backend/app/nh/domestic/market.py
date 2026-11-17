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
    HOURS_TTL = 3600.0

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
        self._overseas_client: NHClient | None = None
        self._cache = TtlCache(clock)
        # 합성 일봉은 만드는 동안 `self.candles`(위 캐시)를 부르므로 캐시를 따로 둔다. 같은 캐시를 쓰면 잠금이 겹쳐 교착한다.
        self._spread_cache = TtlCache(clock)

    def _nh(self, market: str = "domestic") -> NHClient:
        if market == "overseas":
            if self._overseas_client is None:
                self._overseas_client = NHClient(self._settings, market="overseas")
            return self._overseas_client
        if self._client is None:
            self._client = NHClient(self._settings)
        return self._client

    def has_credentials(self, market: str = "domestic") -> bool:
        if market == "overseas":
            return bool(self._settings.nh_overseas_app_key and self._settings.nh_overseas_app_secret)
        return bool(self._settings.nh_app_key and self._settings.nh_app_secret)

    def quote(self, code: str, market: str = "domestic", exchange: str | None = None) -> dict[str, Any]:
        def make() -> QuoteDetail:
            if market == "overseas":
                from app.nh.overseas.quotes import fetch_quote_detail as fetch_overseas

                return fetch_overseas(self._nh(market), exchange or "", code)
            return fetch_quote_detail(self._nh(), code)

        detail: QuoteDetail = self._cache.get(("quote", market, exchange, code), self.QUOTE_TTL, make)
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
            "market_session": self._session(detail, market, exchange),
        }

    def _session(self, detail: QuoteDetail, market: str, exchange: str | None) -> str:
        if market == "domestic":
            return market_session(detail.name, self._now())
        from app.nh.overseas.market_hours import fetch_window, session

        try:
            window = self._cache.get(
                ("hours", exchange, detail.code),
                self.HOURS_TTL,
                lambda: fetch_window(self._nh(market), exchange or "", detail.code),
            )
        except NHError:
            return "unknown"  # 장 종류를 못 구해도 시세는 돌려준다
        return session(window, self._now()) if window else "unknown"

    def candles(
        self, code: str, interval: str, quantity: int, market: str = "domestic", exchange: str | None = None
    ) -> list[dict[str, Any]]:
        def make() -> list[Candle]:
            if market == "overseas":
                from app.nh.overseas import quotes as overseas

                client = self._nh(market)
                if interval == "day":
                    bars = overseas.fetch_daily_bars(client, exchange or "", code, quantity=quantity)
                else:
                    bars = overseas.fetch_minute_bars(
                        client, exchange or "", code, minutes=int(interval), max_bars=quantity
                    )[-quantity:]
                return [Candle(b.time, b.open, b.high, b.low, b.close, b.volume) for b in bars]
            if interval == "day":
                return fetch_daily_bars(self._nh(), code, quantity=quantity)
            return fetch_recent_bars(self._nh(), code, minutes=int(interval), quantity=quantity)

        candles: list[Candle] = self._cache.get(
            ("candles", market, exchange, code, interval, quantity), self.CANDLE_TTL, make
        )
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

    def orderbook(self, code: str, market: str = "domestic", exchange: str | None = None) -> dict[str, Any]:
        def make() -> tuple[OrderBook, float | None, float | None]:
            if market == "overseas":
                from app.nh.overseas.quotes import fetch_book as fetch_overseas

                return fetch_overseas(self._nh(market), exchange or "", code)
            return fetch_book(self._nh(), code)

        book, price, rate = self._cache.get(("book", market, exchange, code), self.BOOK_TTL, make)
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

    # ---- 스프레드 종목 ----

    def spread_quote(self, code: str, legs: list[tuple[str, float]], exchange: str | None) -> dict[str, Any]:
        """두 종목 현재가를 가중치대로 합친 스프레드 현재가. 월물·만기·가격 제한·거래승수는 `null`이다."""
        quotes = [self.quote(leg_code, "overseas", exchange) for leg_code, _ in legs]

        def combine(key: str) -> float | None:
            values = [quote[key] for quote in quotes]
            return None if None in values else sum(ratio * value for (_, ratio), value in zip(legs, values))

        price, prev = combine("price"), combine("prev_close")
        change = None if price is None or prev is None else price - prev
        volumes = [quote["volume"] for quote in quotes if quote["volume"] is not None]
        return {
            "code": code,
            "name": code,
            "contract": None,
            "expiry": None,
            "price": price,
            "change": change,
            "change_rate": None if change is None or not prev else change / abs(prev) * 100,
            "volume": min(volumes) if volumes else None,
            "open": combine("open"),
            "high": None,
            "low": None,
            "prev_close": prev,
            "upper_limit": None,
            "lower_limit": None,
            "multiplier": None,
            "remaining_days": None,
            # 한 종목의 장 정보를 모를 수 있어(예: 3년물) 알 수 있는 값을 쓴다.
            "market_session": next((q["market_session"] for q in quotes if q["market_session"] != "unknown"), "unknown"),
        }

    # 스프레드 봉은 종목마다 최근 봉을 받아 같은 시각끼리 짝짓는다. 한 종목의 봉이 오래전에 끊기면 겹치지 않으므로 넉넉히 받는다.
    SPREAD_FETCH_FACTOR = 4
    SPREAD_MAX_BARS = 4000
    SPREAD_DAILY_SYNTH_BARS = 20000
    SPREAD_DAILY_TTL = 300.0

    def spread_candles(
        self, legs: list[tuple[str, float]], interval: str, quantity: int, exchange: str | None
    ) -> list[dict[str, Any]]:
        """두 종목 봉을 같은 시각끼리 짝지은 스프레드 봉. 고가·저가는 알 수 없어 시가·종가의 최댓값·최솟값으로 둔다.

        일봉은 한 종목이라도 NH 일봉이 비어 있으면 5분봉 스프레드를 영업일별로 합성해 돌려준다.
        """
        if interval == "day":
            rows = self._spread_pairs(legs, "day", quantity, exchange)
            if rows:
                return rows[-quantity:]
            # 5분봉을 많이 받아 합성하므로 무거워 일봉 차트의 짧은 갱신 주기마다 다시 만들지 않는다.
            return self._spread_cache.get(
                ("spread-daily", tuple(legs), exchange, quantity),
                self.SPREAD_DAILY_TTL,
                lambda: self._spread_daily_from_minutes(legs, quantity, exchange),
            )
        return self._spread_pairs(legs, interval, min(quantity * self.SPREAD_FETCH_FACTOR, self.SPREAD_MAX_BARS), exchange)[-quantity:]

    def _spread_daily_from_minutes(self, legs: list[tuple[str, float]], quantity: int, exchange: str | None) -> list[dict[str, Any]]:
        from datetime import datetime

        from app.runners.series import daily_from_minutes
        from strategy_base.models import Bar

        rows = self._spread_pairs(legs, "5", self.SPREAD_DAILY_SYNTH_BARS, exchange)
        bars = [Bar(datetime.fromisoformat(r["time"]), r["high"], r["low"], r["close"], r["volume"], r["open"]) for r in rows]
        return [
            {"time": b.time.date().isoformat(), "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume}
            for b in daily_from_minutes(bars)
        ][-quantity:]

    def _spread_pairs(self, legs: list[tuple[str, float]], interval: str, quantity: int, exchange: str | None) -> list[dict[str, Any]]:
        first, second = (self.candles(leg_code, interval, quantity, "overseas", exchange) for leg_code, _ in legs)
        others = {row["time"]: row for row in second}
        (_, one), (_, two) = legs
        result = []
        for row in first:
            other = others.get(row["time"])
            if other is None or not (row["close"] and other["close"] and row["volume"] and other["volume"]):
                continue
            close = one * row["close"] + two * other["close"]
            open_ = one * row["open"] + two * other["open"] if row["open"] is not None and other["open"] is not None else close
            result.append(
                {
                    "time": row["time"],
                    "open": open_,
                    "high": max(open_, close),
                    "low": min(open_, close),
                    "close": close,
                    "volume": min(row["volume"], other["volume"]),
                }
            )
        return result

    @staticmethod
    def spread_orderbook(code: str) -> dict[str, Any]:
        """스프레드에는 호가가 없다."""
        return {
            "code": code,
            "time": "",
            "price": None,
            "change_rate": None,
            "total_ask_quantity": None,
            "total_bid_quantity": None,
            "levels": [],
        }
