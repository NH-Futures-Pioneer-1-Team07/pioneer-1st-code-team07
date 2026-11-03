import json
from datetime import date, datetime

import httpx
import pytest

from app.config import Settings
from app.nh.client import NHClient
from app.nh.domestic.account import OrderStatus
from app.nh.domestic.orders import OrderBlocked
from app.nh.errors import NHConfigError
from app.nh.overseas import account, orders, quotes
from strategy_base.models import OrderType, Side
from tests.test_nh_client import FakeLimiter, Server


def make(*responses, env="mock"):
    server = Server(*responses)
    settings = Settings(trading_env=env, nh_overseas_app_key="ok", nh_overseas_app_secret="os")
    http = httpx.Client(transport=httpx.MockTransport(server))
    client = NHClient(settings, market="overseas", http_client=http, limiter=FakeLimiter())
    return client, server


def body_of(request):
    return json.loads(request.content)


def minute_row(day, clock, high, low, close, volume, open_="0"):
    return {
        "occurs1_ref_dt": day,
        "occurs1_exch_tm": clock,
        "occurs1_open_pric": open_,
        "occurs1_high_pric": str(high),
        "occurs1_low_pric": str(low),
        "occurs1_close_pric": str(close),
        "occurs1_cum_trd_qty": str(volume),
    }


# ---- 시세 ----


def test_해외_분봉을_Bar로_바꾸고_오래된_순서로_정렬한다():
    client, server = make(
        {
            "Occurs1": [
                minute_row("20261102", "000500", 111.5, 111.25, 111.4, 80),
                minute_row("20261102", "000000", 111.3, 111.1, 111.2, 120, open_="111.15"),
            ]
        }
    )

    bars = quotes.fetch_minute_bars(client, "FCME", "ZNZ26", minutes=5, start=date(2026, 11, 2), end=date(2026, 11, 2))

    assert [(b.time, b.open, b.high, b.low, b.close, b.volume) for b in bars] == [
        (datetime(2026, 11, 2, 0, 0), 111.15, 111.3, 111.1, 111.2, 120),
        (datetime(2026, 11, 2, 0, 5), 0.0, 111.5, 111.25, 111.4, 80),
    ]
    request = server.api_requests()[0]
    assert request.url.path == "/trade/v1/overseas/chart-minute"
    assert body_of(request)["exch_cd"] == "FCME"
    assert body_of(request)["sym"] == "ZNZ26"
    assert body_of(request)["dcnt"] == "5"
    assert body_of(request)["inq_strt_dt"] == "20261102"


def test_분봉은_다음_데이터_키로_과거_쪽을_이어받고_기간_밖의_봉은_거른다():
    client, server = make(
        {"nxt_key": "K1", "Occurs1": [minute_row("20261105", "000500", 3, 2, 2.6, 20), minute_row("20261105", "000000", 3, 2, 2.5, 20)]},
        {"nxt_key": "K2", "Occurs1": [minute_row("20261103", "235500", 2, 1, 1.5, 10), minute_row("20261102", "235500", 2, 1, 1.4, 10)]},
        {"nxt_key": "K3", "Occurs1": [minute_row("20261101", "235500", 2, 1, 1.3, 10)]},
    )

    bars = quotes.fetch_minute_bars(client, "FCME", "ZNZ26", minutes=5, start=date(2026, 11, 2), end=date(2026, 11, 4))

    assert [b.time for b in bars] == [datetime(2026, 11, 2, 23, 55), datetime(2026, 11, 3, 23, 55)]  # 5일 봉과 1일 봉은 기간 밖
    assert [body_of(r)["nxt_key"] for r in server.api_requests()] == ["99999999", "K1", "K2"]  # 시작일보다 오래된 봉이 나오면 멈춘다


def test_데이터_끝에서_키가_최신_쪽으로_되돌아가면_멈춘다():
    client, server = make(
        {"nxt_key": "K1", "Occurs1": [minute_row("20261103", "000500", 2, 1, 1.5, 10), minute_row("20261103", "000000", 2, 1, 1.4, 10)]},
        {"nxt_key": "K2", "Occurs1": [minute_row("20261102", "000000", 2, 1, 1.3, 10)]},
        {"nxt_key": "K3", "Occurs1": [minute_row("20261103", "000500", 2, 1, 1.5, 10)]},  # 되돌아온 쪽
    )

    bars = quotes.fetch_minute_bars(client, "FCME", "ZNZ26", minutes=5)

    assert [b.time.day for b in bars] == [2, 3, 3]
    assert len(server.api_requests()) == 3


def test_끝_날짜가_시작보다_빠르면_거부한다():
    client, _ = make()

    with pytest.raises(ValueError):
        quotes.fetch_minute_bars(client, "FCME", "ZNZ26", minutes=5, start=date(2026, 11, 3), end=date(2026, 11, 2))


def test_일봉은_최근_개수만_오래된_순서로_돌려준다():
    rows = [
        {**minute_row(day, "", 111, 110, 110.5, 1000), "occurs1_exch_tm": ""}
        for day in ("20261104", "20261102", "20261103")
    ]
    client, server = make({"Occurs1": rows})

    bars = quotes.fetch_daily_bars(client, "FCME", "ZNZ26", quantity=2)

    assert [b.time for b in bars] == [datetime(2026, 11, 3), datetime(2026, 11, 4)]
    assert body_of(server.api_requests()[0])["req_qty"] == "2"
    assert server.api_requests()[0].url.path == "/trade/v1/overseas/chart-daily"


def test_현재가는_중첩_입력으로_요청하고_종가를_읽는다():
    client, server = make({"nrec": "1", "Occurs1": [{"occurs1_last_pric": "111.25"}]})

    quote = quotes.fetch_quote(client, "FCME", "ZNZ26")

    assert quote.last_price == 111.25
    assert quote.last_trading_day is None
    assert body_of(server.api_requests()[0]) == {"Iccurs1": {"iccurs1_exch_cd": "FCME", "iccurs1_sym": "ZNZ26"}}


def test_해외_키가_없으면_해외_호출이_설정_오류다():
    settings = Settings(_env_file=None, trading_env="mock", nh_app_key="k", nh_app_secret="s")
    http = httpx.Client(transport=httpx.MockTransport(Server({})))
    client = NHClient(settings, market="overseas", http_client=http, limiter=FakeLimiter())

    with pytest.raises(NHConfigError, match="NH_OVERSEAS_APP_KEY"):
        quotes.fetch_quote(client, "FCME", "ZNZ26")


# ---- 주문 ----


def test_해외_시장가_매수_주문이_명세대로_나간다():
    client, server = make({"ord_no": "0000000042", "err_cd": "", "err_msg": ""})

    order_no = orders.place_order(client, "ZNZ26", Side.BUY, 3)

    assert order_no == "0000000042"
    request = server.api_requests()[0]
    assert request.url.path == "/trade/v1/overseas/order"
    assert body_of(request) == {
        "qt_div_cd": "1",
        "sym": "ZNZ26",
        "trd_div_cd": "1",
        "glb_ord_tp_cd": "1",
        "ord_qty": "3",
        "ord_pric": "0",
        "org_ord_no": "0",
    }


def test_해외_지정가_매도_주문은_가격을_보낸다():
    client, server = make({"ord_no": "1"})

    orders.place_order(client, "ZNZ26", Side.SELL, 1, order_type=OrderType.LIMIT, price=111.5)

    body = body_of(server.api_requests()[0])
    assert (body["trd_div_cd"], body["glb_ord_tp_cd"], body["ord_pric"]) == ("2", "2", "111.5")


def test_해외_지정가는_가격이_없으면_보내지_않는다():
    client, server = make()

    with pytest.raises(ValueError):
        orders.place_order(client, "ZNZ26", Side.BUY, 1, order_type=OrderType.LIMIT)

    assert server.api_requests() == []


def test_해외_취소는_원주문번호와_취소구분을_보낸다():
    client, server = make({"ord_no": "0000000043"})

    assert orders.cancel_order(client, "ZNZ26", Side.BUY, 2, "0000000042") == "0000000043"

    body = body_of(server.api_requests()[0])
    assert (body["qt_div_cd"], body["org_ord_no"], body["ord_qty"]) == ("3", "0000000042", "2")


def test_실전_환경에서는_해외_주문과_취소를_보내지_않는다():
    client, server = make(env="real")

    with pytest.raises(OrderBlocked):
        orders.place_order(client, "ZNZ26", Side.BUY, 1)
    with pytest.raises(OrderBlocked):
        orders.cancel_order(client, "ZNZ26", Side.BUY, 1, "1")

    assert server.api_requests() == []


# ---- 계좌 ----


def test_예탁금을_통화와_환산구분으로_조회한다():
    client, server = make(
        {"dps_csh_amt": "10,000.50", "dps_aset_amt": "10100", "ord_psb_amt": "9000", "init_mrgn": "1000", "mtn_mrgn": "900", "pl_amt": "100"}
    )

    deposit = account.fetch_deposit(client, "USD", date(2026, 11, 2))

    assert (deposit.cash, deposit.total_assets, deposit.order_available_total, deposit.initial_margin) == (10000.5, 10100, 9000, 1000)
    assert deposit.maintenance_margin == 900 and deposit.total_pnl == 100
    assert body_of(server.api_requests()[0]) == {"biz_dt": "20261102", "cur_cd": "USD", "cvs_div": "1"}


def test_보유_포지션을_읽는다():
    client, _ = make(
        {
            "Occurs1": [
                {"occurs1_sym": "ZNZ26", "occurs1_trd_tp": "2", "occurs1_opint_qty": "4", "occurs1_cls_psb_qty": "4", "occurs1_avg_pric": "111.5", "occurs1_pl_amt": "-62.5", "occurs1_last_pric": "111.52"}
            ]
        }
    )

    [position] = account.fetch_positions(client)

    assert (position.code, position.side, position.quantity, position.avg_price, position.pnl) == ("ZNZ26", Side.SELL, 4, 111.5, -62.5)


def test_주문_내역을_읽고_미체결만_조회할_수_있다():
    row = {
        "occurs1_ord_no": "7", "occurs1_org_ord_no": "0", "occurs1_sym": "ZNZ26", "occurs1_ord_sts": "4", "occurs1_trd_tp": "1",
        "occurs1_qt_tp": "1", "occurs1_ord_qty": "3", "occurs1_exec_qty": "1", "occurs1_ord_rem_qty": "2", "occurs1_ord_pric": "0",
        "occurs1_exec_pric": "111.5", "occurs1_ord_rcv_tm": "20261102103015", "occurs1_rejt_rsn": "",
    }
    client, server = make({"Occurs1": [row]})

    [record] = account.fetch_orders(client, open_only=True)

    assert body_of(server.api_requests()[0])["inq_div"] == "3"
    assert (record.order_no, record.status, record.side, record.remaining_quantity) == ("7", OrderStatus.PARTIAL, Side.BUY, 2)
    assert record.is_open and record.received_time == "103015"


def test_주문가능수량은_방향에_맞는_필드를_읽는다():
    body = {"new_buy_ord_psb_qty": "10", "buy_cls_psb_qty": "0", "buy_ord_psb_qty": "10", "new_sel_ord_psb_qty": "8", "sel_cls_psb_qty": "2", "sel_ord_psb_qty": "10", "ord_psb_amt": "5000"}
    client, server = make(body, body)

    sell = account.fetch_orderable_quantity(client, "ZNZ26", Side.SELL, 0)
    buy = account.fetch_orderable_quantity(client, "ZNZ26", Side.BUY, 111.5)

    assert (sell.order_quantity, sell.closable_quantity, sell.total_quantity) == (8, 2, 10)
    assert buy.order_quantity == 10
    assert body_of(server.api_requests()[0])["glb_ord_tp_cd"] == "1"
    assert body_of(server.api_requests()[1])["glb_ord_tp_cd"] == "2"


def test_상품_정보에서_틱_크기와_틱값을_읽는다():
    client, server = make(
        {"Occurs1": [{"occurs1_prd_cd": "ZB", "occurs1_tick_unt": "0.03125"}, {"occurs1_prd_cd": "ZN", "occurs1_ko_prd_nm": "미국 10년 국채", "occurs1_exch_cd": "CME", "occurs1_cur_cd": "USD", "occurs1_tick_unt": "0.015625", "occurs1_tick_val": "15.625"}]}
    )

    product = account.fetch_product(client, "ZN", "CME")

    assert (product.code, product.exchange, product.currency, product.tick_size, product.tick_value) == ("ZN", "CME", "USD", 0.015625, 15.625)
    assert account.fetch_product(make({"Occurs1": []})[0], "ZN") is None
