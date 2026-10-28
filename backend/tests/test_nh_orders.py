import json

import httpx
import pytest

from app.config import Settings
from app.nh.client import NHClient
from app.nh.errors import BusinessError, NHError, TransportError
from app.nh.orders import OrderBlocked, cancel_order, place_order
from strategy_base.models import OrderType, Side
from tests.test_nh_client import FakeLimiter, Server


def make(*responses, env="mock", limiter=None):
    server = Server(*responses)
    settings = Settings(trading_env=env, nh_app_key="k", nh_app_secret="s")
    http = httpx.Client(transport=httpx.MockTransport(server))
    return NHClient(settings, http_client=http, limiter=limiter or FakeLimiter()), server


def body_of(request):
    return json.loads(request.content)


def test_시장가_매수_주문이_명세대로_나가고_주문번호를_돌려준다():
    client, server = make({"ord_no": "0000012345", "msg_cd": "", "msg_cntn": ""})

    order_no = place_order(client, "A116B000", Side.BUY, 5)

    assert order_no == "0000012345"
    request = server.api_requests()[0]
    assert request.url.path == "/trade/v1/domestic/order"
    assert body_of(request) == {
        "sym": "A116B000",
        "trd_div": "1",
        "ord_tp_cd": "2",
        "ord_qty": "5",
        "ord_pric": "0",
        "exec_cnd_cd": "1",
    }


def test_지정가_매도_주문은_가격을_보낸다():
    client, server = make({"ord_no": "1", "msg_cd": ""})

    place_order(client, "A116B000", Side.SELL, 2, order_type=OrderType.LIMIT, price=70500.0)

    assert body_of(server.api_requests()[0]) == {
        "sym": "A116B000",
        "trd_div": "2",
        "ord_tp_cd": "1",
        "ord_qty": "2",
        "ord_pric": "70500",
        "exec_cnd_cd": "1",
    }


def test_주문_인자가_잘못되면_보내지_않는다():
    client, server = make()

    with pytest.raises(ValueError):
        place_order(client, "A", Side.BUY, 0)
    with pytest.raises(ValueError):
        place_order(client, "A", Side.BUY, 1, order_type=OrderType.LIMIT)
    with pytest.raises(ValueError):
        place_order(client, "A", Side.BUY, 1, order_type=OrderType.LIMIT, price=0)

    assert server.requests == []


def test_취소_주문이_명세대로_나가고_취소_주문번호를_돌려준다():
    client, server = make({"ord_no": "0000012346", "msg_cd": "", "msg_cntn": ""})

    order_no = cancel_order(client, "A116B000", Side.BUY, 3, "0000012345")

    assert order_no == "0000012346"
    request = server.api_requests()[0]
    assert request.url.path == "/trade/v1/domestic/cancel"
    assert body_of(request) == {"sym": "A116B000", "trd_div": "1", "ord_qty": "3", "org_ord_no": "0000012345"}


def test_취소_인자가_잘못되면_보내지_않는다():
    client, server = make()

    with pytest.raises(ValueError):
        cancel_order(client, "A", Side.BUY, 0, "1")
    with pytest.raises(ValueError):
        cancel_order(client, "A", Side.BUY, 1, " ")

    assert server.requests == []


def test_실전_환경에서는_주문과_취소를_요청_없이_거부한다():
    client, server = make(env="real")

    with pytest.raises(OrderBlocked):
        place_order(client, "A", Side.BUY, 1)
    with pytest.raises(OrderBlocked):
        cancel_order(client, "A", Side.BUY, 1, "1")

    assert server.requests == []


def test_주문_거부_응답은_코드와_사유를_담은_예외가_된다():
    client, _ = make({"ord_no": "", "msg_cd": "40123", "msg_cntn": "증거금이 부족합니다"})

    with pytest.raises(BusinessError) as error:
        place_order(client, "A116B000", Side.BUY, 5)

    assert error.value.code == "40123"
    assert "증거금이 부족합니다" in str(error.value)


def test_주문번호가_없는_정상_응답은_오류다():
    client, _ = make({"ord_no": "", "msg_cd": ""})

    with pytest.raises(NHError, match="주문번호"):
        place_order(client, "A", Side.BUY, 1)


def test_시간_초과된_주문은_다시_보내지_않는다():
    client, server = make(httpx.ReadTimeout("느림"))

    with pytest.raises(TransportError, match="주문 내역"):
        place_order(client, "A", Side.BUY, 1)

    assert len(server.api_requests()) == 1


def test_주문은_주문_등급으로_제한기를_거친다():
    from app.nh.rate_limit import Limit

    limiter = FakeLimiter()
    client, _ = make({"ord_no": "1", "msg_cd": ""}, {"ord_no": "2", "msg_cd": ""}, limiter=limiter)

    place_order(client, "A", Side.BUY, 1)
    cancel_order(client, "A", Side.BUY, 1, "1")

    assert limiter.calls == [("mock", Limit.ORDER), ("mock", Limit.ORDER)]
