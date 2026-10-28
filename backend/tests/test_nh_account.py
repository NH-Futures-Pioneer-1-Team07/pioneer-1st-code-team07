import json
from datetime import date

import httpx
import pytest

from app.config import Settings
from app.nh.account import (
    OrderStatus,
    fetch_deposit,
    fetch_orderable_quantity,
    fetch_orders,
    fetch_positions,
)
from app.nh.client import NHClient
from app.nh.errors import NHError
from strategy_base.models import Side
from tests.test_nh_client import FakeLimiter, Server


def make(*responses):
    server = Server(*responses)
    settings = Settings(trading_env="mock", nh_app_key="k", nh_app_secret="s")
    http = httpx.Client(transport=httpx.MockTransport(server))
    return NHClient(settings, http_client=http, limiter=FakeLimiter()), server


def body_of(request):
    return json.loads(request.content)


def position_row(code="A116B000", side="1", quantity="5", **extra):
    return {
        "occurs1_ac_no": "123-45-678901",
        "occurs1_ac_nm": "홍길동",
        "occurs1_sym": code,
        "occurs1_ko_sym_nm": "삼성전자 F 202611",
        "occurs1_trd_div": side,
        "occurs1_opint_qty": quantity,
        "occurs1_cls_psb_qty": quantity,
        "occurs1_avg_pric": "70,500",
        "occurs1_close_pric": "70600",
        "occurs1_pl_amt": "5000",
        "occurs1_pl_rt": "0.14",
        **extra,
    }


def order_row(order_no, status="1", **extra):
    return {
        "occurs1_ac_no": "123-45-678901",
        "occurs1_ord_no": order_no,
        "occurs1_org_ord_no": "",
        "occurs1_sym": "A116B000",
        "occurs1_trd_div": "2",
        "occurs1_ord_sts": status,
        "occurs1_ord_div_cd": "1",
        "occurs1_ord_qty": "5",
        "occurs1_ord_pric": "0",
        "occurs1_exec_qty": "2",
        "occurs1_exec_pric": "70500",
        "occurs1_rem_ord_qty": "3",
        "occurs1_exch_rcv_tm": "093012",
        "occurs1_ord_rejt_rsn": "",
        **extra,
    }


def test_예탁금을_변환하고_영업일자를_보낸다():
    client, server = make(
        {
            "dps_csh_amt": "100000000",
            "dps_aset_tot_amt": "100500000",
            "ord_psb_tot_amt": "90000000",
            "ord_psb_csh_amt": "80000000",
            "init_mrgn_tot_amt": "10000000",
            "mtn_mrgn_tam_amt": "7000000",
            "fut_rez_pl_amt": "500000",
            "pl_tot_pric": "500000",
        }
    )

    deposit = fetch_deposit(client, date(2026, 10, 28))

    assert deposit.cash == 100000000
    assert deposit.total_assets == 100500000
    assert (deposit.order_available_total, deposit.initial_margin) == (90000000, 10000000)
    assert deposit.futures_realized_pnl == 500000
    request = server.api_requests()[0]
    assert request.url.path == "/trade/v1/domestic/deposit"
    assert body_of(request) == {"biz_dt": "20261028"}


def test_예탁금_항목이_비어_있으면_값이_없다():
    client, _ = make({"dps_csh_amt": ""})

    assert fetch_deposit(client, date(2026, 10, 28)).cash is None


def test_보유_포지션을_변환한다():
    client, _ = make({"Occurs1": [position_row(side="2", quantity="3")]})

    [position] = fetch_positions(client)

    assert (position.code, position.side, position.quantity, position.closable_quantity) == (
        "A116B000",
        Side.SELL,
        3,
        3,
    )
    assert (position.avg_price, position.last_price, position.pnl) == (70500, 70600, 5000)


def test_계좌번호와_계좌명은_결과와_요청에_남지_않는다():
    client, server = make({"Occurs1": [position_row()]})

    positions = fetch_positions(client)

    assert "123-45-678901" not in repr(positions) and "홍길동" not in repr(positions)
    assert "123-45-678901" not in server.api_requests()[0].content.decode()


def test_보유_포지션이_여러_쪽이면_이어받아_합친다():
    client, server = make(
        {"nxt_key": "PAGE2", "Occurs1": [position_row("A1")]},
        {"nxt_key": "", "Occurs1": [position_row("A2")]},
    )

    positions = fetch_positions(client)

    assert [p.code for p in positions] == ["A1", "A2"]
    assert [body_of(r)["nxt_key"] for r in server.api_requests()] == ["", "PAGE2"]


def test_이어받기_키가_반복되면_무한히_부르지_않고_멈춘다():
    client, server = make(
        {"nxt_key": "SAME", "Occurs1": [position_row("A1")]},
        {"nxt_key": "SAME", "Occurs1": [position_row("A2")]},
        {"nxt_key": "SAME", "Occurs1": [position_row("A3")]},
    )

    positions = fetch_positions(client)

    assert len(positions) == 2
    assert len(server.api_requests()) == 2


def test_Occurs1_형식이_이상하면_오류다():
    client, _ = make({"Occurs1": "x"})

    with pytest.raises(NHError):
        fetch_positions(client)


def test_주문_내역을_변환한다():
    client, server = make({"Occurs1": [order_row("0000012345", status="4")]})

    [order] = fetch_orders(client)

    assert order.order_no == "0000012345"
    assert (order.side, order.status, order.kind) == (Side.SELL, OrderStatus.PARTIAL, "new")
    assert (order.quantity, order.filled_quantity, order.remaining_quantity) == (5, 2, 3)
    assert order.filled_price == 70500
    assert order.is_open
    assert body_of(server.api_requests()[0]) == {
        "trd_div": "0",
        "exec_div": "0",
        "trd_tm_div_cd": "0",
        "ord_div_cd": "0",
        "nxt_key": "",
    }


def test_미체결_주문만_조회한다():
    client, server = make({"Occurs1": []})

    fetch_orders(client, open_only=True)

    assert body_of(server.api_requests()[0])["exec_div"] == "2"


def test_주문_상태별로_미체결_여부를_가른다():
    statuses = {"1": True, "3": True, "4": True, "6": False, "8": False, "9": False, "7": False}
    client, _ = make({"Occurs1": [order_row(f"N{code}", status=code) for code in statuses]})

    orders = fetch_orders(client)

    assert {o.order_no[1:]: o.is_open for o in orders} == statuses
    assert orders[-1].status == OrderStatus.UNKNOWN


def test_거부된_주문은_사유를_담는다():
    client, _ = make({"Occurs1": [order_row("N1", status="9", occurs1_ord_rejt_rsn="증거금 부족")]})

    [order] = fetch_orders(client)

    assert (order.status, order.reject_reason, order.is_open) == (OrderStatus.REJECTED, "증거금 부족", False)


def test_정정과_취소_주문은_구분해서_원주문번호를_담는다():
    client, _ = make(
        {"Occurs1": [order_row("C1", occurs1_ord_div_cd="3", occurs1_org_ord_no="N1")]}
    )

    [order] = fetch_orders(client)

    assert (order.kind, order.original_order_no) == ("cancel", "N1")


def test_주문가능수량을_변환하고_요청에_주간_일반을_보낸다():
    client, server = make({"ord_psb_qty": "20", "cls_psb_qty": "5", "tot_psb_qty": "25", "ord_psb_amt": "9000000"})

    result = fetch_orderable_quantity(client, "A116B000", Side.BUY, 70500.0)

    assert (result.order_quantity, result.closable_quantity, result.total_quantity) == (20, 5, 25)
    assert result.order_amount == 9000000
    assert body_of(server.api_requests()[0]) == {
        "ord_sts": "1",
        "sym": "A116B000",
        "trd_div": "1",
        "ord_pric": "70500",
    }
