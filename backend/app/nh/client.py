"""NH선물 API를 부르는 공통 자리.

- 접근토큰을 붙이고 호출 제한 간격을 지킨다.
- 성공 여부를 본문까지 보고 판단한다. HTTP 200은 성공이 아니다.
- 실패해도 다시 보내지 않는다. 주문이 시간 초과로 실패했을 때 다시 보내면 같은 주문이
  두 번 접수될 수 있다. 예외는 토큰이 거부된 경우의 한 번뿐이다. 그 요청은 처리되지 않았다.
"""

from typing import Any

import httpx

from app.config import Settings
from app.nh.auth import TokenManager
from app.nh.errors import BusinessError, GatewayError, HttpError, TransportError
from app.nh.rate_limit import Limit, RateLimiter

BASE_URLS = {"mock": "https://apidemo.futures.co.kr", "real": "https://api.futures.co.kr"}
TIMEOUT = httpx.Timeout(10.0)

UNAUTHORIZED = 401
# 접근토큰을 다시 받으면 풀리는 코드
REISSUE_CODES = {"EG041", "EG042", "EG043", "EG044", "EG045", "EG047", "EG049", "EGW052"}
GATEWAY_PREFIXES = ("EG", "EST")
ERROR_MESSAGE_FIELDS = ("errorMessage", "errorMsg", "message", "msg")


class NHClient:
    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.Client | None = None,
        limiter: RateLimiter | None = None,
    ):
        self.environment = settings.trading_env
        self.base_url = BASE_URLS[self.environment]
        self._http = http_client or httpx.Client(timeout=TIMEOUT)
        self._limiter = limiter or RateLimiter()
        self._tokens = TokenManager(
            base_url=self.base_url,
            app_key=settings.nh_app_key.get_secret_value() if settings.nh_app_key else None,
            app_secret=settings.nh_app_secret.get_secret_value() if settings.nh_app_secret else None,
            client=self._http,
        )

    def call(self, path: str, payload: dict[str, Any], limit: Limit) -> dict[str, Any]:
        """API를 한 번 부르고 응답 본문을 돌려준다. 실패하면 예외를 낸다."""
        self._limiter.wait(self.environment, limit)
        response, body = self._send(path, payload)
        if response.status_code == UNAUTHORIZED or _error_code(body) in REISSUE_CODES:
            self._tokens.forget()
            self._limiter.wait(self.environment, limit)
            response, body = self._send(path, payload)

        code = _error_code(body)
        if code:
            detail = _error_message(body)
            if code.upper().startswith(GATEWAY_PREFIXES):
                raise GatewayError(path, code, detail, body)
            raise BusinessError(path, code, detail, body)
        if response.status_code >= 400:
            raise HttpError(path, response.status_code, body)
        message_code = str(body.get("msg_cd") or "").strip() if isinstance(body, dict) else ""
        if message_code:
            raise BusinessError(path, message_code, str(body.get("msg_cntn") or "").strip(), body)
        if not isinstance(body, dict):
            raise HttpError(path, response.status_code, body)
        return body

    def _send(self, path: str, payload: dict[str, Any]) -> tuple[httpx.Response, Any]:
        headers = {"Authorization": self._tokens.token().authorization}
        try:
            response = self._http.post(f"{self.base_url}{path}", headers=headers, json=payload)
        except httpx.TimeoutException:
            raise TransportError(
                f"{path} 요청이 시간 안에 끝나지 않았습니다. 처리 여부를 알 수 없으므로 "
                "다시 보내기 전에 주문 내역으로 확인하세요."
            ) from None
        except httpx.HTTPError as error:
            raise TransportError(f"{path} 요청에 실패했습니다: {type(error).__name__}") from None
        try:
            body = response.json()
        except ValueError:
            body = response.text.strip()
        return response, body


def _error_code(body: Any) -> str:
    return str(body.get("errorCode") or "").strip() if isinstance(body, dict) else ""


def _error_message(body: Any) -> str:
    for name in ERROR_MESSAGE_FIELDS:
        text = str(body.get(name) or "").strip() if isinstance(body, dict) else ""
        if text:
            return text
    return ""
