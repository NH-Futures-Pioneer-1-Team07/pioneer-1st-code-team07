import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import httpx
import pytest

from app.config import Settings
from app.nh.auth import KST, REFRESH_MARGIN, AuthError, Token, TokenManager, parse_expires_at
from app.nh.client import RATE_LIMIT_RETRIES, NHClient
from app.nh.errors import BusinessError, GatewayError, HttpError, NHConfigError, TransportError
from app.nh.rate_limit import PER_SECOND, SHARED_LIMITER, Limit, RateLimiter

KEY, SECRET, TOKEN = "APPKEY-123", "APPSECRET-456", "ACCESS-TOKEN-789"
TOKEN_BODY = {"access_token": TOKEN, "token_type": "Bearer", "expires_in": "86400", "expires_at": "2099-01-01 00:00:00"}


class Server:
    """NH 서버를 흉내 낸다. 요청을 모두 기록한다."""

    def __init__(self, *responses):
        self.requests: list[httpx.Request] = []
        self.responses = list(responses)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/auth-service/v1/token":
            return httpx.Response(200, json=TOKEN_BODY)
        item = self.responses.pop(0) if self.responses else {}
        if isinstance(item, Exception):
            raise item
        if isinstance(item, httpx.Response):
            return item
        return httpx.Response(200, json=item)

    def api_requests(self):
        return [r for r in self.requests if r.url.path != "/auth-service/v1/token"]

    def token_requests(self):
        return [r for r in self.requests if r.url.path == "/auth-service/v1/token"]


class FakeLimiter:
    def __init__(self):
        self.calls = []

    def wait(self, environment, limit):
        self.calls.append((environment, limit))
        return 0.0


def make_client(*responses, env="mock", key=KEY, secret=SECRET, limiter=None, sleep=lambda seconds: None):
    server = Server(*responses)
    settings = Settings(trading_env=env, nh_app_key=key, nh_app_secret=secret)
    http = httpx.Client(transport=httpx.MockTransport(server))
    return NHClient(settings, http_client=http, limiter=limiter or FakeLimiter(), sleep=sleep), server


# ---- 환경과 설정 ----


def test_모의_환경은_모의_도메인으로_부른다():
    client, server = make_client({"ok": "1"})

    client.call("/trade/v1/domestic/price", {"sym": "A"}, Limit.QUOTE)

    assert {r.url.host for r in server.requests} == {"apidemo.futures.co.kr"}


def test_실전_환경은_실전_도메인으로_부른다():
    client, server = make_client({"ok": "1"}, env="real")

    client.call("/trade/v1/domestic/price", {"sym": "A"}, Limit.QUOTE)

    assert {r.url.host for r in server.requests} == {"api.futures.co.kr"}


def test_인증_정보가_없으면_필요한_변수_이름을_알려_준다():
    client, server = make_client(key=None, secret=None)

    with pytest.raises(NHConfigError, match="NH_APP_KEY"):
        client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)
    assert server.requests == []


def test_해외_클라이언트는_해외_키로_토큰을_발급받는다():
    server = Server({})
    settings = Settings(
        trading_env="mock",
        nh_app_key=KEY,
        nh_app_secret=SECRET,
        nh_overseas_app_key="OVERSEAS-KEY",
        nh_overseas_app_secret="OVERSEAS-SECRET",
    )
    http = httpx.Client(transport=httpx.MockTransport(server))
    client = NHClient(settings, market="overseas", http_client=http, limiter=FakeLimiter())

    client.call("/trade/v1/overseas/price", {}, Limit.QUOTE)

    form = parse_qs(server.token_requests()[0].content.decode())
    assert form["appkey"] == ["OVERSEAS-KEY"] and form["appsecret"] == ["OVERSEAS-SECRET"]


def test_해외_키가_없으면_해외_변수_이름을_알려_준다():
    server = Server()
    settings = Settings(trading_env="mock", nh_app_key=KEY, nh_app_secret=SECRET)
    http = httpx.Client(transport=httpx.MockTransport(server))
    client = NHClient(settings, market="overseas", http_client=http, limiter=FakeLimiter())

    with pytest.raises(NHConfigError, match="NH_OVERSEAS_APP_KEY, NH_OVERSEAS_APP_SECRET"):
        client.call("/trade/v1/overseas/price", {}, Limit.QUOTE)
    assert server.requests == []


def test_인증_정보_설정은_값을_출력하지_않는다():
    settings = Settings(trading_env="mock", nh_app_key=KEY, nh_app_secret=SECRET)

    assert KEY not in repr(settings) and SECRET not in repr(settings)


# ---- 토큰 ----


def test_토큰_발급은_form_형식으로_명세대로_보낸다():
    client, server = make_client({"ok": "1"})

    client.call("/trade/v1/domestic/price", {"sym": "A"}, Limit.QUOTE)

    [issue] = server.token_requests()
    assert issue.headers["content-type"] == "application/x-www-form-urlencoded"
    assert parse_qs(issue.content.decode()) == {
        "grant_type": ["client_credentials"],
        "appkey": [KEY],
        "appsecret": [SECRET],
    }


def test_요청에_토큰을_붙이고_유효한_토큰은_재사용한다():
    client, server = make_client({"a": "1"}, {"b": "2"})

    client.call("/trade/v1/domestic/price", {"sym": "A"}, Limit.QUOTE)
    client.call("/trade/v1/domestic/price", {"sym": "B"}, Limit.QUOTE)

    assert len(server.token_requests()) == 1
    for request in server.api_requests():
        assert request.headers["authorization"] == f"Bearer {TOKEN}"
        assert request.headers["content-type"] == "application/json"
    assert json.loads(server.api_requests()[1].content) == {"sym": "B"}


def test_만료가_가까우면_토큰을_다시_발급받는다():
    now = datetime(2026, 10, 28, 9, 0, tzinfo=KST)
    clock = {"now": now}
    body = {**TOKEN_BODY, "expires_at": (now + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")}
    issued = []

    def handler(request):
        issued.append(request)
        return httpx.Response(200, json=body)

    manager = TokenManager(
        base_url="https://x",
        app_key=KEY,
        app_secret=SECRET,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        clock=lambda: clock["now"],
    )

    manager.token()
    clock["now"] = now + timedelta(hours=23, minutes=50)
    manager.token()
    assert len(issued) == 1

    clock["now"] = now + timedelta(hours=24) - REFRESH_MARGIN
    manager.token()
    assert len(issued) == 2


def test_만료_시각은_expires_at을_먼저_보고_없으면_expires_in으로_계산한다():
    now = datetime(2026, 10, 28, 9, 0, tzinfo=KST)

    assert parse_expires_at({"expires_at": "2026-10-29 09:00:00"}, now) == now + timedelta(days=1)
    assert parse_expires_at({"expires_in": "3600"}, now) == now + timedelta(hours=1)
    assert parse_expires_at({}, now) < now + timedelta(hours=1)


def test_토큰_발급이_거부되면_인증_오류를_내고_키를_드러내지_않는다():
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401, json={"x": 1})))
    manager = TokenManager(base_url="https://x", app_key=KEY, app_secret=SECRET, client=http)

    with pytest.raises(AuthError) as error:
        manager.token()

    assert KEY not in str(error.value) and SECRET not in str(error.value)


def test_토큰_표시에는_토큰_값이_없다():
    token = Token("SECRET-VALUE", "Bearer", datetime(2026, 10, 28, tzinfo=KST))

    assert "SECRET-VALUE" not in repr(token)


# ---- 오류 판단 ----


def test_본문의_msg_cd는_상태가_200이어도_업무_거부다():
    client, _ = make_client({"msg_cd": "40001", "msg_cntn": "주문 거부"})

    with pytest.raises(BusinessError) as error:
        client.call("/trade/v1/domestic/order", {}, Limit.ORDER)

    assert error.value.code == "40001"
    assert "주문 거부" in str(error.value)


def test_본문의_errorCode는_상태가_200이어도_실패다():
    client, _ = make_client({"errorCode": "5039", "errorMessage": "처리불가"})

    with pytest.raises(BusinessError) as error:
        client.call("/trade/v1/domestic/order", {}, Limit.ORDER)

    assert error.value.code == "5039"


def test_EG로_시작하는_코드는_게이트웨이_거절이다():
    client, _ = make_client({"errorCode": "EGW053", "errorMessage": "모의에서 호출 불가"})

    with pytest.raises(GatewayError) as error:
        client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)

    assert error.value.code == "EGW053"


def test_HTTP_오류는_상태와_함께_예외로_바뀐다():
    client, _ = make_client(httpx.Response(500, json={"errorMessage": "서버 오류"}))

    with pytest.raises(HttpError) as error:
        client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)

    assert error.value.status == 500
    assert "서버 오류" in str(error.value)


def test_토큰을_다시_받으라는_코드는_토큰을_새로_받아_한_번만_다시_보낸다():
    client, server = make_client({"errorCode": "EGW052", "errorMessage": "재발급 필요"}, {"ok": "1"})

    body = client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)

    assert body == {"ok": "1"}
    assert len(server.api_requests()) == 2
    assert len(server.token_requests()) == 2


def test_401이_두_번_오면_다시_보내지_않고_실패한다():
    client, server = make_client(httpx.Response(401, json={}), httpx.Response(401, json={}))

    with pytest.raises(HttpError):
        client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)

    assert len(server.api_requests()) == 2


def test_시간_초과는_다시_보내지_않고_처리_여부를_알_수_없다고_알린다():
    client, server = make_client(httpx.ReadTimeout("느림"))

    with pytest.raises(TransportError, match="처리 여부"):
        client.call("/trade/v1/domestic/order", {"x": 1}, Limit.ORDER)

    assert len(server.api_requests()) == 1


def test_오류_메시지에는_키와_토큰이_나오지_않는다():
    client, _ = make_client({"errorCode": "EG999", "errorMessage": "거절"})

    with pytest.raises(GatewayError) as error:
        client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)

    text = str(error.value) + repr(error.value)
    assert not any(secret in text for secret in (KEY, SECRET, TOKEN))


def test_호출_전에_등급별_호출_제한기를_거친다():
    limiter = FakeLimiter()
    client, _ = make_client({"a": 1}, {"b": 2}, limiter=limiter)

    client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)
    client.call("/trade/v1/domestic/order", {}, Limit.ORDER)

    assert limiter.calls == [("mock", Limit.QUOTE), ("mock", Limit.ORDER)]


# ---- 호출 제한기 ----


def test_초당_건수만큼_간격을_벌린다():
    clock = {"now": 100.0}
    slept = []

    def sleep(seconds):
        slept.append(round(seconds, 6))
        clock["now"] += seconds

    limiter = RateLimiter(monotonic=lambda: clock["now"], sleep=sleep)

    delays = [limiter.wait("mock", Limit.ORDER) for _ in range(3)]

    assert delays == [0.0, pytest.approx(0.2), pytest.approx(0.2)]
    assert PER_SECOND[Limit.ORDER] == 5 and PER_SECOND[Limit.QUOTE] == 10 and PER_SECOND[Limit.ACCOUNT] == 10


def test_간격이_이미_지났으면_기다리지_않는다():
    clock = {"now": 0.0}
    limiter = RateLimiter(monotonic=lambda: clock["now"], sleep=lambda s: pytest.fail("기다리면 안 됨"))

    limiter.wait("mock", Limit.QUOTE)
    clock["now"] = 5.0

    assert limiter.wait("mock", Limit.QUOTE) == 0.0


def test_환경과_등급이_다르면_서로_기다리지_않는다():
    limiter = RateLimiter(monotonic=lambda: 0.0, sleep=lambda s: None)

    assert limiter.wait("mock", Limit.QUOTE) == 0.0
    assert limiter.wait("real", Limit.QUOTE) == 0.0
    assert limiter.wait("mock", Limit.ORDER) == 0.0


# ---- 웹소켓 접속키 ----


def test_웹소켓_접속키를_토큰과_함께_GET으로_발급받는다():
    client, server = make_client({"access_key": "WS-KEY"})

    key = client.issue_websocket_key()

    assert key == "WS-KEY"
    [request] = server.api_requests()
    assert (request.method, request.url.path) == ("GET", "/permission/v1/web-socket-key")
    assert request.headers["authorization"] == f"Bearer {TOKEN}"


def test_접속키는_발급할_때마다_새로_요청한다():
    client, server = make_client({"access_key": "A"}, {"access_key": "B"})

    assert [client.issue_websocket_key(), client.issue_websocket_key()] == ["A", "B"]
    assert len(server.api_requests()) == 2


def test_접속키_응답에_키가_없으면_오류다():
    client, _ = make_client({"access_key": ""})

    with pytest.raises(HttpError):
        client.issue_websocket_key()


def test_접속키_발급이_거절되면_예외가_된다():
    client, _ = make_client({"errorCode": "EGW051", "errorMessage": "인증 정보 확인 불가"})

    with pytest.raises(GatewayError):
        client.issue_websocket_key()


def test_세션_초기화용_토큰_값을_돌려준다():
    client, _ = make_client()

    assert client.session_token() == TOKEN


RATE_LIMITED_BODY = {"errorCode": "EGW036", "errorMessage": "허용된 요청 속도를 초과했습니다."}


def test_클라이언트를_여러_개_만들어도_기본_호출_제한기는_하나를_함께_쓴다():
    settings = Settings(trading_env="mock", nh_app_key=KEY, nh_app_secret=SECRET)

    first, second = NHClient(settings), NHClient(settings)

    assert first._limiter is second._limiter is SHARED_LIMITER


def test_조회가_호출_속도_제한으로_거절되면_기다렸다가_다시_보낸다():
    waits = []
    client, server = make_client(RATE_LIMITED_BODY, RATE_LIMITED_BODY, {"ok": 1}, sleep=waits.append)

    body = client.call("/trade/v1/domestic/chart-minute", {}, Limit.QUOTE)

    assert body == {"ok": 1}
    assert len(server.api_requests()) == 3
    assert waits == [1.0, 2.0]


def test_호출_속도_제한이_계속되면_재시도_횟수만큼만_보내고_예외를_낸다():
    client, server = make_client(*[RATE_LIMITED_BODY] * (RATE_LIMIT_RETRIES + 2))

    with pytest.raises(GatewayError) as error:
        client.call("/trade/v1/domestic/chart-minute", {}, Limit.QUOTE)

    assert error.value.code == "EGW036"
    assert len(server.api_requests()) == RATE_LIMIT_RETRIES + 1


def test_주문은_호출_속도_제한으로_거절돼도_다시_보내지_않는다():
    client, server = make_client(RATE_LIMITED_BODY, {"ord_no": "1", "msg_cd": ""})

    with pytest.raises(GatewayError):
        client.call("/trade/v1/domestic/order", {}, Limit.ORDER)

    assert len(server.api_requests()) == 1


def test_다른_게이트웨이_거절은_다시_보내지_않는다():
    client, server = make_client({"errorCode": "EG999", "errorMessage": "거절"}, {"ok": 1})

    with pytest.raises(GatewayError):
        client.call("/trade/v1/domestic/price", {}, Limit.QUOTE)

    assert len(server.api_requests()) == 1
