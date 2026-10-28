"""NH 응답의 문자열 값을 숫자·날짜로 바꾼다. 읽을 수 없으면 `None`이다."""

from datetime import date, datetime
from typing import Any


def number(value: Any) -> float | None:
    text = str(value if value is not None else "").replace(",", "").replace("+", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def count(value: Any) -> int | None:
    parsed = number(value)
    return None if parsed is None else int(parsed)


def day(value: Any) -> date | None:
    try:
        return datetime.strptime(str(value or "").strip(), "%Y%m%d").date()
    except ValueError:
        return None


def text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def price_text(price: float | int) -> str:
    """요청에 넣을 가격 문자열. 정수로 떨어지면 소수점을 뺀다."""
    return str(int(price)) if float(price) == int(price) else str(price)
