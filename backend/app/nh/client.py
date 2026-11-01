"""NH선물 API를 부르는 공통 자리.

- 접근토큰을 붙이고 호출 제한 간격을 지킨다.
- 성공 여부를 본문까지 보고 판단한다. HTTP 200은 성공이 아니다.
- 실패해도 다시 보내지 않는다. 주문이 시간 초과로 실패했을 때 다시 보내면 같은 주문이
  두 번 접수될 수 있다. 예외는 토큰이 거부된 경우의 한 번과, 조회가 호출 속도 제한(`EGW036`)으로
  거절된 경우의 몇 번뿐이다. 그 요청은 처리되지 않았다.
"""

import time
from collections.abc import Callable
from typing import Any, Literal

import httpx

from app.config import Settings
from app.nh.auth import TokenManager
from app.nh.errors import BusinessError, GatewayError, HttpError, TransportError
from app.nh.rate_limit import SHARED_LIMITER, Limit, RateLimiter

Market = Literal["domestic", "overseas"]

BASE_URLS = {"mock": "https://apidemo.futures.co.kr", "real": "https://api.futures.co.kr"}
TIMEOUT = httpx.Timeout(10.0)

UNAUTHORIZED = 401
WEBSOCKET_KEY_PATH = "/permission/v1/web-socket-key"
# 접근토큰을 다시 받으면 풀리는 코드
REISSUE_CODES = {"EG041", "EG042", "EG043", "EG044", "EG045", "EG047", "EG049", "EGW052"}
GATEWAY_PREFIXES = ("EG", "EST")
RATE_LIMITED = "EGW036"
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF = 1.0
ERROR_MESSAGE_FIELDS = ("errorMessage", "errorMsg", "message", "msg")


class NHClient:
    def __init__(
        self,
        settings: Settings,
        *,
        market: Market = "domestic",
        http_client: httpx.Client | None = None,
        limiter: RateLimiter | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.environment = settings.trading_env
        self.market = market
        key, secret = (
            (settings.nh_overseas_app_key, settings.nh_overseas_app_secret)
            if market == "overseas"
            else (settings.nh_app_key, settings.nh_app_secret)
        )
        self.base_url = BASE_URLS[self.environment]
        self._http = http_client or httpx.Client(timeout=TIMEOUT)
        # 클라이언트가 여러 개여도 같은 계정의 호출 한도를 함께 지키도록 기본은 하나를 공유한다.
        self._limiter = limiter or SHARED_LIMITER
        self._sleep = sleep
        self._tokens = TokenManager(
            base_url=self.base_url,
            app_key=key.get_secret_value() if key else None,
            app_secret=secret.get_secret_value() if secret else None,
            key_names="NH_OVERSEAS_APP_KEY, NH_OVERSEAS_APP_SECRET" if market == "overseas" else "NH_APP_KEY, NH_APP_SECRET",
            client=self._http,
        )

    def call(self, path: str, payload: dict[str, Any], limit: Limit) -> dict[str, Any]:
        """API를 부르고 응답 본문을 돌려준다. 실패하면 예외를 낸다.

        주문이 아닌 조회가 호출 속도 제한으로 거절되면 간격을 늘려 몇 번 다시 보낸다.
        """
        retries = 0
        while True:
            try:
                return self._call_once(path, payload, limit)
            except GatewayError as error:
                if error.code != RATE_LIMITED or limit is Limit.ORDER or retries >= RATE_LIMIT_RETRIES:
                    raise
                retries += 1
                self._sleep(RATE_LIMIT_BACKOFF * retries)

    def _call_once(self, path: str, payload: dict[str, Any], limit: Limit) -> dict[str, Any]:
        self._limiter.wait(self.environment, limit)
        response, body = self._send(path, payload)
        if response.status_code == UNAUTHORIZED or _error_code(body) in REISSUE_CODES:
            self._tokens.forget()
            self._limiter.wait(self.environment, limit)
            response, body = self._send(path, payload)

        return self._checked(path, response, body)

    def issue_websocket_key(self) -> str:
        """실시간 연결에 쓰는 접속키를 발급받는다. 연결할 때마다 한 번 쓰고 보관하지 않는다."""
        headers = {"Authorization": self._tokens.token().authorization}
        try:
            response = self._http.get(f"{self.base_url}{WEBSOCKET_KEY_PATH}", headers=headers)
        except httpx.HTTPError as error:
            raise TransportError(f"웹소켓 접속키 발급 요청에 실패했습니다: {type(error).__name__}") from None
        try:
            body = response.json()
        except ValueError:
            body = response.text.strip()
        key = str(self._checked(WEBSOCKET_KEY_PATH, response, body).get("access_key") or "").strip()
        if not key:
            raise HttpError(WEBSOCKET_KEY_PATH, response.status_code, {"errorMessage": "access_key가 없습니다"})
        return key

    def session_token(self) -> str:
        """실시간 세션 초기화에 쓰는 접근토큰 값."""
        return self._tokens.token().access_token

    def _checked(self, path: str, response: httpx.Response, body: Any) -> dict[str, Any]:
        """응답이 실패인지 본문까지 보고 판단한다. 성공이면 본문을 돌려준다."""
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
