# 국내_시세호가

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | KB |
| API 통신 방식 | WEBSOCKET |
| API 명 | 국내_시세호가 |
| HTTP Method | WEBSOCKET |
| Content-Type |  |
| 실전 Domain | wss://api.futures.co.kr |
| 모의 Domain | wss://apidemo.futures.co.kr |
| URL 명 | /trade/ws-stream?access_key={{WEBSOCKET_KEY}} |
| API 요청 제한 | 전체 실시간 구독 제한은 20개입니다. |

## 설명

```text
실시간 처리 안내

1. 실시간 구독/해제 요청에 대한 응답
실시간 데이터 구독 또는 해제를 요청하면, 아래와 같이 결과가 응답됩니다.
 - 성공 시: RT_INIT
 - 실패 시: RT_FAIL

2. 실시간 데이터 처리 방식
수신된 데이터는 JSON으로 변환한 후, header 객체의 포함 여부에 따라 다음과 같이 구분하여 처리합니다.
 - header 객체가 있는 경우: 실시간 데이터로 처리
 - header 객체가 없는 경우: 요청에 대한 응답으로 처리

=============================================================================
실시간 처리 샘플 (Pythone)
import json

def on_message(ws, message):
    response = json.loads(message)

    if response.get("header"):
        # 실시간 데이터 처리
        handle_realtime_data(response)
    else:
        # 요청에 대한 응답 처리
        handle_request_response(response)

def handle_request_response(response):
    rt_cd = response.get("rt_cd")

    if rt_cd == "RT_INIT":
        # 구독/해제 요청 성공
        print("실시간 등록 성공:", response)
    elif rt_cd == "RT_FAIL":
        # 구독/해제 요청 실패
        print("실시간 등록 실패:", response)
    else:
        # 기타 요청에 대한 응답 처리
        print("요청 응답 수신:", response)

# 실시간 데이터(호가/체결/주문체결 등) 처리 로직
def handle_realtime_data(response):
    header = response.get("header")
    body = response.get("body")
=============================================================================

3. 동시 구독 가능 건수
실시간 동시 구독은 호가, 체결(주간·야간 포함), 주문체결을 모두 합산하여 최대 20건까지 가능합니다.
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `header` | 공통헤더 | `struct` | 0 | Object | 0 |  |  | N |  |
| header | `api_ver` | api 버전 | `char` | 1 | 일반 | 1 | 1 |  | Y |  |
| header | `action` | 구독 / 구독 해제 | `char` | 1 | 일반 | 1 |  | A:구독, D:해제 | N |  |
|  | `body` | 웹소켓 바디 | `struct` | 0 | Object | 1 |  |  | N |  |
| body | `action_code` | 실시간 구분 | `char` | 12 | 일반 | 1 | KB | 실시간 구분 | N |  |
| body | `action_sym` | 실시간 구독/해제 종목코드 | `char` | 12 | 일반 | 1 | A0169000 | 구독/해제 종목코드 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nght_tp` | 실시간 시세 유형(KB) | `char` | 2 | 일반 | 0 |  |  | 없음 |
|  | `sym` | 종목코드 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `seq_no` | 일련번호 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `exch_tm` | 거래소시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `ask_qty` | 총매도잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt` | 총매도건수 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `pre_ask_qty_clr` | 총매도잔량직전대비색상 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `pre_ask_qty` | 총매도잔량직전대비 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty` | 총매수잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt` | 총매수건수 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `pre_bid_qty_clr` | 총매수잔량직전대비색상 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `pre_bid_qty` | 총매수잔량직전대비 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_1` | 매도호가색상1 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_1` | 매도호가1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_1` | 매도수량1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_1` | 매도건수1 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_1` | 매도직전대비색상1 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_1` | 매도직전대비1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_1` | 매도등락률색상1 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_1` | 매도등락률1 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_1` | 매수호가색상1 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_1` | 매수호가1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_1` | 매수잔량1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_1` | 매수건수1 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_1` | 매수직전대비색상1 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_1` | 매수직전대비1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_1` | 매수등락률색상1 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_1` | 매수등락률1 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_2` | 매도호가색상2 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_2` | 매도호가2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_2` | 매도수량2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_2` | 매도건수2 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_2` | 매도직전대비색상2 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_2` | 매도직전대비2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_2` | 매도등락률색상2 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_2` | 매도등락률2 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_2` | 매수호가색상2 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_2` | 매수호가2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_2` | 매수잔량2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_2` | 매수건수2 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_2` | 매수직전대비색상2 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_2` | 매수직전대비2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_2` | 매수등락률색상2 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_2` | 매수등락률2 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_3` | 매도호가색상3 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_3` | 매도호가3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_3` | 매도수량3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_3` | 매도건수3 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_3` | 매도직전대비색상3 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_3` | 매도직전대비3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_3` | 매도등락률색상3 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_3` | 매도등락률3 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_3` | 매수호가색상3 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_3` | 매수호가3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_3` | 매수잔량3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_3` | 매수건수3 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_3` | 매수직전대비색상3 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_3` | 매수직전대비3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_3` | 매수등락률색상3 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_3` | 매수등락률3 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_4` | 매도호가색상4 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_4` | 매도호가4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_4` | 매도수량4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_4` | 매도건수4 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_4` | 매도직전대비색상4 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_4` | 매도직전대비4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_4` | 매도등락률색상4 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_4` | 매도등락률4 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_4` | 매수호가색상4 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_4` | 매수호가4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_4` | 매수잔량4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_4` | 매수건수4 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_4` | 매수직전대비색상4 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_4` | 매수직전대비4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_4` | 매수등락률색상4 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_4` | 매수등락률4 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_5` | 매도호가색상5 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_5` | 매도호가5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_5` | 매도수량5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_5` | 매도건수5 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_5` | 매도직전대비색상5 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_5` | 매도직전대비5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_5` | 매도등락률색상5 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_5` | 매도등락률5 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_5` | 매수호가색상5 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_5` | 매수호가5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_5` | 매수잔량5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_5` | 매수건수5 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_5` | 매수직전대비색상5 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_5` | 매수직전대비5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_5` | 매수등락률색상5 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_5` | 매수등락률5 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_6` | 매도호가색상6 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_6` | 매도호가6 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_6` | 매도수량6 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_6` | 매도건수6 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_6` | 매도직전대비색상6 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_6` | 매도직전대비6 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_6` | 매도등락률색상6 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_6` | 매도등락률6 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_6` | 매수호가색상6 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_6` | 매수호가6 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_6` | 매수잔량6 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_6` | 매수건수6 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_6` | 매수직전대비색상6 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_6` | 매수직전대비6 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_6` | 매수등락률색상6 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_6` | 매수등락률6 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_7` | 매도호가색상7 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_7` | 매도호가7 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_7` | 매도수량7 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_7` | 매도건수7 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_7` | 매도직전대비색상7 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_7` | 매도직전대비7 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_7` | 매도등락률색상7 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_7` | 매도등락률7 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_7` | 매수호가색상7 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_7` | 매수호가7 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_7` | 매수잔량7 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_7` | 매수건수7 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_7` | 매수직전대비색상7 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_7` | 매수직전대비7 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_7` | 매수등락률색상7 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_7` | 매수등락률7 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_8` | 매도호가색상8 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_8` | 매도호가8 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_8` | 매도수량8 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_8` | 매도건수8 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_8` | 매도직전대비색상8 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_8` | 매도직전대비8 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_8` | 매도등락률색상8 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_8` | 매도등락률8 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_8` | 매수호가색상8 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_8` | 매수호가8 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_8` | 매수잔량8 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_8` | 매수건수8 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_8` | 매수직전대비색상8 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_8` | 매수직전대비8 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_8` | 매수등락률색상8 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_8` | 매수등락률8 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_9` | 매도호가색상9 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_9` | 매도호가9 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_9` | 매도수량9 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_9` | 매도건수9 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_9` | 매도직전대비색상9 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_9` | 매도직전대비9 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_9` | 매도등락률색상9 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_9` | 매도등락률9 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_9` | 매수호가색상9 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_9` | 매수호가9 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_9` | 매수잔량9 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_9` | 매수건수9 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_9` | 매수직전대비색상9 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_9` | 매수직전대비9 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_9` | 매수등락률색상9 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_9` | 매수등락률9 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_clr_10` | 매도호가색상10 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_10` | 매도호가10 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_10` | 매도수량10 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_10` | 매도건수10 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_clr_10` | 매도직전대비색상10 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_10` | 매도직전대비10 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_clr_10` | 매도등락률색상10 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_rt_10` | 매도등락률10 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_clr_10` | 매수호가색상10 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_10` | 매수호가10 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_10` | 매수잔량10 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_10` | 매수건수10 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_clr_10` | 매수직전대비색상10 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_10` | 매수직전대비10 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_clr_10` | 매수등락률색상10 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `bid_rt_10` | 매수등락률10 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `est_exec_pric_clr` | 예상체결가색상 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `est_exec_pric` | 예상체결가 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `net_bid_ask_clr` | 총매수매도잔량차이색상 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `net_bid_ask` | 총매수매도잔량차이 | `char` | 9 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "api_ver": "1",
  "action_code": "KB",
  "action_sym": "A0169000",
  "header": null,
  "action": null,
  "body": null
}
```

## Response JSON (Output)

```json
{
  "ask_rt_clr_9": "",
  "ask_rt_clr_7": "",
  "ask_rt_clr_8": "",
  "ask_rt_clr_5": "",
  "ask_rt_clr_6": "",
  "ask_rt_clr_3": "",
  "ask_rt_clr_4": "",
  "ask_rt_clr_1": "",
  "ask_rt_clr_2": "",
  "ask_rt_10": "",
  "ask_rt_clr_10": "",
  "bid_qty_3": "",
  "bid_pre_7": "",
  "bid_qty_4": "",
  "bid_pre_6": "",
  "bid_qty_5": "",
  "bid_pre_9": "",
  "bid_qty_6": "",
  "bid_pre_8": "",
  "bid_qty_7": "",
  "bid_qty_8": "",
  "bid_qty_9": "",
  "bid_pre_clr_6": "",
  "ask_cnt": "",
  "pre_ask_qty_clr": "",
  "bid_pre_clr_7": "",
  "bid_pre_1": "",
  "bid_pre_clr_4": "",
  "bid_pre_clr_5": "",
  "bid_pre_3": "",
  "bid_pre_2": "",
  "bid_qty_1": "",
  "bid_pre_5": "",
  "bid_pre_clr_8": "",
  "bid_qty_2": "",
  "bid_pre_4": "",
  "bid_pre_clr_9": "",
  "est_exec_pric": "",
  "ask_qty_10": "",
  "ask_clr_2": "",
  "ask_rt_8": "",
  "ask_clr_3": "",
  "ask_rt_7": "",
  "ask_clr_1": "",
  "ask_rt_9": "",
  "ask_clr_6": "",
  "ask_clr_7": "",
  "ask_clr_4": "",
  "ask_clr_5": "",
  "ask_clr_10": "",
  "ask_clr_8": "",
  "ask_clr_9": "",
  "bid_pric_10": "",
  "bid_pre_clr_2": "",
  "bid_pre_clr_3": "",
  "bid_pre_clr_1": "",
  "bid_rt_clr_9": "",
  "bid_rt_clr_8": "",
  "net_bid_ask": "",
  "bid_cnt_1": "",
  "bid_rt_clr_7": "",
  "bid_cnt_2": "",
  "bid_rt_clr_6": "",
  "bid_cnt_3": "",
  "bid_rt_clr_5": "",
  "bid_cnt_4": "",
  "bid_rt_clr_4": "",
  "bid_rt_clr_3": "",
  "bid_cnt_5": "",
  "bid_rt_clr_2": "",
  "bid_cnt_6": "",
  "bid_rt_clr_1": "",
  "bid_cnt_7": "",
  "ask_pric_2": "",
  "bid_cnt_8": "",
  "ask_pric_1": "",
  "bid_cnt_9": "",
  "ask_pric_4": "",
  "ask_pric_3": "",
  "ask_cnt_10": "",
  "ask_pric_9": "",
  "ask_pre_clr_10": "",
  "ask_pric_6": "",
  "bid_rt_10": "",
  "ask_pric_5": "",
  "ask_pric_8": "",
  "ask_pric_7": "",
  "ask_qty_9": "",
  "ask_qty_8": "",
  "ask_qty_7": "",
  "bid_pre_clr_10": "",
  "bid_rt_clr_10": "",
  "ask_pre_10": "",
  "ask_qty_2": "",
  "ask_qty_1": "",
  "ask_qty": "",
  "ask_qty_6": "",
  "ask_qty_5": "",
  "ask_qty_4": "",
  "ask_qty_3": "",
  "ask_pre_1": "",
  "ask_cnt_3": "",
  "ask_cnt_2": "",
  "ask_cnt_1": "",
  "pre_ask_qty": "",
  "ask_cnt_7": "",
  "bid_qty": "",
  "ask_cnt_6": "",
  "ask_cnt_5": "",
  "ask_cnt_4": "",
  "ask_cnt_9": "",
  "ask_cnt_8": "",
  "bid_pre_10": "",
  "pre_bid_qty": "",
  "ask_pre_6": "",
  "ask_pre_7": "",
  "ask_pre_8": "",
  "ask_pre_9": "",
  "ask_pre_2": "",
  "ask_pre_3": "",
  "ask_pre_4": "",
  "ask_pre_5": "",
  "seq_no": "",
  "ask_pre_clr_1": "",
  "ask_pre_clr_2": "",
  "ask_pre_clr_3": "",
  "ask_pre_clr_4": "",
  "ask_pre_clr_5": "",
  "ask_pre_clr_6": "",
  "ask_pre_clr_7": "",
  "ask_rt_4": "",
  "ask_rt_3": "",
  "ask_rt_6": "",
  "ask_rt_5": "",
  "ask_rt_2": "",
  "ask_rt_1": "",
  "bid_rt_1": "",
  "bid_rt_2": "",
  "sym": "",
  "bid_rt_9": "",
  "bid_qty_10": "",
  "bid_rt_7": "",
  "bid_rt_8": "",
  "bid_rt_5": "",
  "bid_rt_6": "",
  "bid_rt_3": "",
  "bid_rt_4": "",
  "ask_pric_10": "",
  "nght_tp": "",
  "ask_pre_clr_8": "",
  "ask_pre_clr_9": "",
  "bid_cnt": "",
  "bid_clr_10": "",
  "bid_clr_9": "",
  "bid_clr_8": "",
  "bid_clr_7": "",
  "bid_clr_6": "",
  "bid_clr_5": "",
  "est_exec_pric_clr": "",
  "bid_clr_4": "",
  "bid_clr_3": "",
  "bid_clr_2": "",
  "bid_clr_1": "",
  "net_bid_ask_clr": "",
  "bid_pric_9": "",
  "bid_pric_3": "",
  "bid_pric_4": "",
  "bid_pric_1": "",
  "bid_pric_2": "",
  "bid_pric_7": "",
  "pre_bid_qty_clr": "",
  "bid_pric_8": "",
  "exch_tm": "",
  "bid_pric_5": "",
  "bid_pric_6": "",
  "bid_cnt_10": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `KB`
- 원본 범위: `A1:O207`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K22 |
| OUTPUT | A24:J201 |
| Request JSON (Input) | A203:A204 |
| Response JSON (Output) | A206:A207 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
