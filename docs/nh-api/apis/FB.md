# 해외_시세호가

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | FB |
| API 통신 방식 | WEBSOCKET |
| API 명 | 해외_시세호가 |
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
실시간 동시 구독은 호가, 체결, 주문체결을 모두 합산하여 최대 20건까지 가능합니다.
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `header` | 공통헤더 | `struct` | 0 | Object | 0 |  |  | N |  |
| header | `api_ver` | api 버전 | `char` | 1 | 일반 | 1 | 1 |  | Y | 1 |
| header | `action` | 구독 / 구독 해제 | `char` | 1 | 일반 | 1 |  | A:구독, D:해제 | N |  |
|  | `body` | 웹소켓 바디 | `struct` | 0 | Object | 1 |  |  | N |  |
| body | `action_code` | 실시간 구분 | `char` | 12 | 일반 | 1 |  | 실시간 구분 | N |  |
| body | `action_sym` | 실시간 구독/해제 종목코드 | `char` | 12 | 일반 | 1 |  | 구독/해제 종목코드 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 20 | 일반 | 0 |  |  | 없음 |
|  | `prd` | 품목코드 | `char` | 10 | 일반 | 0 |  | 6AU26인 경우 6A | 없음 |
|  | `pric_ind` | 진법구분 | `char` | 1 | 일반 | 0 |  | 진법구분<br>1:정수<br>2:소수점1자리<br>3:소수점2자리<br>9:소수점8자리<br>A:1/2진법<br>B:1/4진법<br>C:1/8진법<br>D:1/16진법<br>E:1/32진법<br>F:1/64진법<br>G:1/128진법<br>H:1/256진법<br>I:0.5/32진법<br>J:0.5/64진법<br>K:0.25/32진법<br>L:0.125/32진법<br>M:0.065/32진법 | 없음 |
|  | `ko_exec_tm` | 체결시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `exch_tm` | 거래소시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `ask_qty` | 총매도잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt` | 총매도건수 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `pre_ask_qty` | 총매도잔량직전대비 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty` | 총매수잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt` | 총매수건수 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `pre_bid_qty` | 총매수잔량직전대비 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_1` | 매도호가1 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_1` | 매도수량1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_1` | 매도건수1 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_1` | 매도직전대비1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_1` | 매수호가1 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_1` | 매수잔량1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_1` | 매수건수1 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_1` | 매수직전대비1 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_2` | 매도호가2 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_2` | 매도수량2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_2` | 매도건수2 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_2` | 매도직전대비2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_2` | 매수호가2 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_2` | 매수잔량2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_2` | 매수건수2 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_2` | 매수직전대비2 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_3` | 매도호가3 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_3` | 매도수량3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_3` | 매도건수3 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_3` | 매도직전대비3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_3` | 매수호가3 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_3` | 매수잔량3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_3` | 매수건수3 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_3` | 매수직전대비3 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_4` | 매도호가4 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_4` | 매도수량4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_4` | 매도건수4 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_4` | 매도직전대비4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_4` | 매수호가4 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_4` | 매수잔량4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_4` | 매수건수4 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_4` | 매수직전대비4 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric_5` | 매도호가5 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty_5` | 매도수량5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt_5` | 매도건수5 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ask_pre_5` | 매도직전대비5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric_5` | 매수호가5 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty_5` | 매수잔량5 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt_5` | 매수건수5 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `bid_pre_5` | 매수직전대비5 | `char` | 9 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "api_ver": "1",
  "action_code": null,
  "action_sym": "",
  "header": null,
  "action": null,
  "body": null
}
```

## Response JSON (Output)

```json
{
  "ask_pre_1": "",
  "ask_cnt_3": "",
  "ask_cnt_2": "",
  "ask_cnt_1": "",
  "pre_ask_qty": "",
  "bid_qty": "",
  "ask_cnt_5": "",
  "ask_cnt_4": "",
  "pre_bid_qty": "",
  "ask_pre_2": "",
  "ask_pre_3": "",
  "ask_pre_4": "",
  "ask_pre_5": "",
  "bid_qty_3": "",
  "bid_qty_4": "",
  "bid_qty_5": "",
  "prd": "",
  "ask_cnt": "",
  "bid_pre_1": "",
  "bid_pre_3": "",
  "bid_pre_2": "",
  "bid_qty_1": "",
  "bid_pre_5": "",
  "bid_qty_2": "",
  "bid_pre_4": "",
  "sym": "",
  "ko_exec_tm": "",
  "bid_cnt_1": "",
  "bid_cnt": "",
  "bid_cnt_2": "",
  "bid_cnt_3": "",
  "bid_cnt_4": "",
  "bid_cnt_5": "",
  "ask_pric_2": "",
  "ask_pric_1": "",
  "ask_pric_4": "",
  "ask_pric_3": "",
  "pric_ind": "",
  "ask_pric_5": "",
  "ask_qty_2": "",
  "bid_pric_3": "",
  "ask_qty_1": "",
  "bid_pric_4": "",
  "ask_qty": "",
  "bid_pric_1": "",
  "bid_pric_2": "",
  "ask_qty_5": "",
  "exch_tm": "",
  "ask_qty_4": "",
  "bid_pric_5": "",
  "ask_qty_3": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `FB`
- 원본 범위: `A1:O82`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K22 |
| OUTPUT | A24:J76 |
| Request JSON (Input) | A78:A79 |
| Response JSON (Output) | A81:A82 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
