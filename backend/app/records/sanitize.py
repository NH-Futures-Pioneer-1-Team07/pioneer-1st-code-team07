"""기록에 비밀정보가 남지 않도록 필드를 제거한다."""

import re
from typing import Any

# 키 이름을 소문자로 바꾸고 영문·숫자·한글 외 문자를 뺀 뒤, 아래 낱말을 포함하면 제거한다.
SECRET_WORDS = (
    "appkey",
    "secret",
    "token",
    "password",
    "passwd",
    "authorization",
    "accountno",
    "accountnumber",
    "acntno",
    "acctno",
    "acntnum",
    "계좌",
)


def is_secret_key(key: str) -> bool:
    normalized = re.sub(r"[^0-9a-z가-힣]", "", key.lower())
    return any(word in normalized for word in SECRET_WORDS)


def sanitize(value: Any) -> Any:
    """딕셔너리와 리스트를 안쪽까지 훑어 비밀정보 필드를 뺀 사본을 돌려준다."""
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items() if not is_secret_key(str(key))}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return value
