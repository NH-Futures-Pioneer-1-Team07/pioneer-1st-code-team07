# 국내_시세체결(야간)

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | KC |
| API 통신 방식 | WEBSOCKET |
| API 명 | 국내_시세체결(야간) |
| HTTP Method | WEBSOCKET |
| Content-Type |  |
| 실전 Domain | wss://api.futures.co.kr |
| 모의 Domain | wss://apidemo.futures.co.kr |
| URL 명 | /trade/ws-stream?access_key={{WEBSOCKET_KEY}} |
| API 요청 제한 | 전체 실시간 구독 제한은 20개입니다. |

## 설명

```text
실시간 처리 안내 (* 모의 환경 미지원)

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
| header | `api_ver` | api 버전 | `char` | 1 | 일반 | 1 | 1 |  | Y | 1 |
| header | `action` | 구독 / 구독 해제 | `char` | 1 | 일반 | 1 |  | A:구독, D:해제 | N |  |
|  | `body` | 웹소켓 바디 | `struct` | 0 | Object | 1 |  |  | N |  |
| body | `action_code` | 실시간 구분 | `char` | 12 | 일반 | 1 | KC | 실시간 구분 | N |  |
| body | `action_sym` | 실시간 구독/해제 종목코드 | `char` | 12 | 일반 | 1 | A0169000 | 구독/해제 종목코드 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `tick_div` | 틱구분 | `char` | 1 | 일반 | 0 |  | 틱구분<br>(국내KA/KC의 경우 1인 경우만 이용, 0인 값은 기타 데이터로 체결량이 0인 값 존재) | 없음 |
|  | `exch_tm` | 거래소시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `open_pric` | 시가 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `high_pric` | 고가 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `low_pric` | 저가 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `last_pric` | 현재가 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `chg_div` | 등락구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `diff_rt` | 전일대비 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `rt` | 등락률 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `exec_qty` | 체결량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `cum_trd_qty` | 누적거래량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `cum_trd_amt` | 거래대금 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `exec_div` | 체결구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ask_best_pric` | 매도호가 | `char` | 9 | 일반 | 1 |  |  | 없음 |
|  | `bid_best_pric` | 매수호가 | `char` | 9 | 일반 | 1 |  |  | 없음 |
|  | `opint` | 미결제약정(차트) | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `pd_trd_qty` | 전일거래량(차트) | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `pd_trd_qty_rt` | 전일거래량비율(차트) | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `und_last_pric` | 기초자산현재가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `cum_buy_exec_qty` | 누적매수체결수량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `cum_sel_exec_qty` | 누적매도체결수량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `cum_buy_exec_amt` | 누적매수체결금액 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `cum_sel_exec_amt` | 누적매도체결금액 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `mkt_bas` | 마켓베이시스 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `theo_bas` | 이론베이시스 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `cum_buy_cnt` | 누적매수건수 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `cum_sel_cnt` | 누적매도건수 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `up_act_pric` | 실시간상한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `lo_act_pric` | 실시간하한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `dev_rt` | 괴리율 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `theo_pric` | 이론가 | `char` | 8 | 일반 | 0 |  | 시장 가격이 고평가인지 저평가인지 판단 기준 | 없음 |
|  | `ival` | 내재가치 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `tm_val` | 시간가치 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ivol` | 내재변동성 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `delta` | 델타 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `gamma` | 감마 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `theta` | 세타 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `vega` | 베가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `rho` | 로 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `opint_diff` | 미결제약정증감 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `theo_chg` | 이론가대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `est_exec_pric` | 예상체결가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `dev` | 괴리도 | `char` | 8 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "api_ver": "1",
  "action_code": "KC",
  "action_sym": "A0169000",
  "header": null,
  "action": null,
  "body": null
}
```

## Response JSON (Output)

```json
{
  "cum_sel_exec_amt": "",
  "theo_bas": "",
  "rt": "",
  "tm_val": "",
  "up_act_pric": "",
  "sym": "",
  "mkt_bas": "",
  "dev_rt": "",
  "delta": "",
  "theta": "",
  "lo_act_pric": "",
  "dev": "",
  "diff_rt": "",
  "cum_trd_amt": "",
  "open_pric": "",
  "exec_div": "",
  "tick_div": "",
  "cum_sel_cnt": "",
  "last_pric": "",
  "opint_diff": "",
  "und_last_pric": "",
  "pd_trd_qty_rt": "",
  "bid_best_pric": null,
  "cum_trd_qty": "",
  "pd_trd_qty": "",
  "high_pric": "",
  "ival": "",
  "cum_buy_exec_amt": "",
  "chg_div": "",
  "ask_best_pric": null,
  "cum_sel_exec_qty": "",
  "exec_qty": "",
  "theo_chg": "",
  "est_exec_pric": "",
  "low_pric": "",
  "theo_pric": "",
  "cum_buy_exec_qty": "",
  "cum_buy_cnt": "",
  "rho": "",
  "ivol": "",
  "exch_tm": "",
  "opint": "",
  "gamma": "",
  "vega": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `KC`
- 원본 범위: `A1:O75`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K22 |
| OUTPUT | A24:J69 |
| Request JSON (Input) | A71:A72 |
| Response JSON (Output) | A74:A75 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
