"""접근토큰 발급과 보관. 토큰은 메모리에만 두고 로그·예외 메시지에 남기지 않는다."""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.nh.errors import NHConfigError, NHError, TransportError

TOKEN_PATH = "/auth-service/v1/token"
KST = timezone(timedelta(hours=9))
REFRESH_MARGIN = timedelta(minutes=5)
FALLBACK_LIFETIME = timedelta(minutes=10)


class AuthError(NHError):
    pass


@dataclass(frozen=True)
class Token:
    access_token: str
    token_type: str
    expires_at: datetime

    @property
    def authorization(self) -> str:
        return f"{self.token_type} {self.access_token}"

    def __repr__(self) -> str:
        return f"Token(expires_at={self.expires_at.isoformat()})"


def now_kst() -> datetime:
    return datetime.now(KST)


def parse_expires_at(body: dict[str, Any], now: datetime) -> datetime:
    """응답의 만료 시각. `expires_at`(한국 시간)을 먼저 보고, 없으면 `expires_in`(초)으로 계산한다."""
    raw = str(body.get("expires_at") or "").strip()
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
        except ValueError:
            pass
    seconds = str(body.get("expires_in") or "").strip()
    if seconds:
        try:
            return now + timedelta(seconds=int(float(seconds)))
        except ValueError:
            pass
    return now + FALLBACK_LIFETIME


class TokenManager:
    def __init__(
        self,
        *,
        base_url: str,
        app_key: str | None,
        app_secret: str | None,
        client: httpx.Client,
        clock: Callable[[], datetime] = now_kst,
    ):
        self._base_url = base_url
        self._app_key = app_key
        self._app_secret = app_secret
        self._client = client
        self._clock = clock
        self._lock = threading.Lock()
        self._token: Token | None = None

    def token(self) -> Token:
        """유효한 토큰을 돌려준다. 없거나 만료가 가까우면 새로 발급받는다."""
        with self._lock:
            if self._token is None or self._clock() + REFRESH_MARGIN >= self._token.expires_at:
                self._token = self._issue()
            return self._token

    def forget(self) -> None:
        """서버가 받아 주지 않는 토큰을 버린다. 다음 호출에서 다시 발급받는다."""
        with self._lock:
            self._token = None

    def _issue(self) -> Token:
        if not self._app_key or not self._app_secret:
            raise NHConfigError("NH_APP_KEY, NH_APP_SECRET 환경변수를 설정하세요")
        # 토큰 발급만 form 형식을 받는다. JSON으로 보내면 본문을 읽지 못한다.
        form = {"grant_type": "client_credentials", "appkey": self._app_key, "appsecret": self._app_secret}
        try:
            response = self._client.post(f"{self._base_url}{TOKEN_PATH}", data=form)
        except httpx.HTTPError as error:
            raise TransportError(f"접근토큰 발급 요청에 실패했습니다: {type(error).__name__}") from None
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.status_code >= 400 or not isinstance(body, dict):
            raise AuthError(f"접근토큰 발급이 거부되었습니다. (HTTP {response.status_code})")
        access_token = str(body.get("access_token") or "").strip()
        if not access_token:
            raise AuthError("접근토큰 발급 응답에 access_token이 없습니다")
        return Token(
            access_token=access_token,
            token_type=str(body.get("token_type") or "Bearer").strip(),
            expires_at=parse_expires_at(body, self._clock()),
        )
