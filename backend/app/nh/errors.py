"""NH선물 API 호출이 실패했을 때 쓰는 예외.

- `NHConfigError`: 인증 정보가 설정돼 있지 않음
- `TransportError`: 응답을 받지 못함(연결 실패, 시간 초과)
- `HttpError`: HTTP 오류 응답
- `BusinessError`: 업무 처리가 거부됨(상태 코드와 무관)
- `GatewayError`: 게이트웨이 쪽이 거절함(`EG`·`EST` 코드)

HTTP 200은 성공이 아니다. 본문에 `errorCode`나 `msg_cd`가 담겨 오면 실패로 본다.
"""

from typing import Any


class NHError(Exception):
    pass


class NHConfigError(NHError):
    pass


class TransportError(NHError):
    """응답을 받지 못했다. 시간 초과는 처리 여부를 알 수 없으므로 다시 보내지 않는다."""


class HttpError(NHError):
    def __init__(self, path: str, status: int, body: Any):
        detail = str(body.get("errorMessage") or "").strip() if isinstance(body, dict) else ""
        super().__init__(f"{path} 호출이 거부되었습니다. (HTTP {status}) {detail}".strip())
        self.path = path
        self.status = status
        self.body = body


class BusinessError(NHError):
    def __init__(self, path: str, code: str, detail: str, body: Any):
        super().__init__(f"{path} 처리가 거부되었습니다. ({code}) {detail}".strip())
        self.path = path
        self.code = code
        self.detail = detail
        self.body = body


class GatewayError(NHError):
    """요청이 처리됐는지 알 수 없는 거절이다. 주문에서는 '거절'로 단정하지 않는다."""

    def __init__(self, path: str, code: str, detail: str, body: Any):
        super().__init__(f"{path} 요청이 거절되었습니다. ({code}) {detail}".strip())
        self.path = path
        self.code = code
        self.detail = detail
        self.body = body
