# 해외_시세체결

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | FA |
| API 통신 방식 | WEBSOCKET |
| API 명 | 해외_시세체결 |
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
| body | `action_code` | 실시간 구분 | `char` | 12 | 일반 | 1 | FA | 실시간 구분 | N |  |
| body | `action_sym` | 실시간 종목코드 | `char` | 12 | 일반 | 1 | 6AU26 | 구독/해제 시 종목코드 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 20 | 일반 | 0 |  |  | 없음 |
|  | `prd` | 품목코드 | `char` | 10 | 일반 | 0 |  | 6AU26인 경우 6A | 없음 |
|  | `pric_ind` | 진법구분 | `char` | 1 | 일반 | 0 |  | 진법구분<br>1:정수<br>2:소수점1자리<br>3:소수점2자리<br>9:소수점8자리<br>A:1/2진법<br>B:1/4진법<br>C:1/8진법<br>D:1/16진법<br>E:1/32진법<br>F:1/64진법<br>G:1/128진법<br>H:1/256진법<br>I:0.5/32진법<br>J:0.5/64진법<br>K:0.25/32진법<br>L:0.125/32진법<br>M:0.065/32진법 | 없음 |
|  | `tick_div` | 틱구분 | `char` | 1 | 일반 | 0 |  | 틱구분<br>(국내KA/KC의 경우 1인 경우만 이용, 0인 값은 기타 데이터로 체결량이 0인 값 존재) | 없음 |
|  | `ko_trd_dt` | 한국체결일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `ko_exec_tm` | 체결시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `ref_dt` | 기준일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `exch_tm` | 거래소시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `open_pric` | 시가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `high_pric` | 고가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `low_pric` | 저가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `last_pric` | 현재가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `chg_div` | 등락구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `diff_rt` | 전일대비 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `rt` | 등락률 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `exec_qty` | 체결량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `cum_trd_qty` | 누적거래량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `exec_div` | 체결구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_best_pric` | 매도호가 | `char` | 15 | 일반 | 1 |  |  | 없음 |
|  | `bid_best_pric` | 매수호가 | `char` | 15 | 일반 | 1 |  |  | 없음 |
|  | `opint` | 미결제약정(차트) | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `pd_trd_qty` | 전일거래량(차트) | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `pd_trd_qty_rt` | 전일거래량비율(차트) | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `cum_buy_exec_qty` | 누적매수체결수량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `cum_sel_exec_qty` | 누적매도체결수량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `biz_dt` | 영업일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `seq_no` | 일련번호 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `cum_buy_exec_amt` | 누적매수체결금액 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `cum_sel_exec_amt` | 누적매도체결금액 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `qt_fgr` | 호가소수점자리 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_qty` | 총매도잔량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty` | 총매수잔량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `ris_trd_qty` | 상승거래량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `fal_trd_qty` | 하강거래량 | `char` | 12 | 일반 | 1 |  | 하강거래량 | 없음 |

## Request JSON (Input)

```json
{
  "api_ver": "1",
  "action_code": "FA",
  "action_sym": "6AU26",
  "header": null,
  "action": null,
  "body": null
}
```

## Response JSON (Output)

```json
{
  "cum_sel_exec_amt": "",
  "rt": "",
  "fal_trd_qty": null,
  "sym": "",
  "biz_dt": "",
  "bid_qty": "",
  "ko_exec_tm": "",
  "ko_trd_dt": "",
  "diff_rt": "",
  "qt_fgr": "",
  "open_pric": "",
  "exec_div": "",
  "tick_div": "",
  "last_pric": "",
  "seq_no": "",
  "prd": "",
  "pd_trd_qty_rt": "",
  "bid_best_pric": null,
  "cum_trd_qty": "",
  "pd_trd_qty": "",
  "high_pric": "",
  "pric_ind": "",
  "cum_buy_exec_amt": "",
  "chg_div": "",
  "ask_best_pric": null,
  "cum_sel_exec_qty": "",
  "exec_qty": "",
  "low_pric": "",
  "ris_trd_qty": "",
  "cum_buy_exec_qty": "",
  "ask_qty": "",
  "ref_dt": "",
  "exch_tm": "",
  "opint": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `FA`
- 원본 범위: `A1:O65`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K22 |
| OUTPUT | A24:J59 |
| Request JSON (Input) | A61:A62 |
| Response JSON (Output) | A64:A65 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
