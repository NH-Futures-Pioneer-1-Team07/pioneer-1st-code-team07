# 국내_주문/체결

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | O1_K |
| API 통신 방식 | WEBSOCKET |
| API 명 | 국내_주문/체결 |
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
| header | `api_ver` | api 버전 | `char` | 1 | 일반 | 0 | 1 |  | Y |  |
| header | `action` | 구독 / 구독 해제 | `char` | 1 | 일반 | 1 |  | A:구독, D:해제 | N |  |
|  | `body` | 웹소켓 바디 | `struct` | 0 | Object | 1 |  |  | N |  |
| body | `action_code` | 실시간 구분 | `char` | 12 | 일반 | 1 | O1 | 실시간 구분 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `ac_no` | 계좌번호 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `mkt_tp` | 시장구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ord_dt` | 주문일자 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ord_no` | 주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `org_ord_dt` | 원주문일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `sym_tp` | 종목구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
|  | `ord_sts` | 처리구분 | `char` | 1 | 일반 | 0 |  | 1:접수, 3:확인, 4:부분체결, 6:전체체결, 8:자동취소, 9:거부 | 없음 |
|  | `trd_div` | 매매구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | 없음 |
|  | `mod_tp` | 정정취소구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `pric_cnd` | 가격조건 | `char` | 1 | 일반 | 0 |  | 가격조건 ([국내]-1:지정가 ,2:시장가, 3:조건부, 4:최유리, [해외]-1:시장가, 2:지정가, 3:STOP시장가, 4:STOP지정가, 5:OCO) | 없음 |
|  | `eff_tp` | 유효구분 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ord_qty` | 주문수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `exec_qty` | 체결수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `mod_qty` | 정정수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `cxl_qty` | 취소수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ord_pric` | 주문가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `exec_pric` | 체결가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `exec_avg_pric` | 체결평균가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `tpf_pric` | 익절가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `sl_pric` | 손절가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `sl_ts` | 손절틱사이즈 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `rcv_tm` | 접수시간 | `char` | 14 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `exec_tm` | 체결시간 | `char` | 14 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `work_empl` | 작업사원 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `blk_no` | 일괄번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `str_tp` | 전략구분 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `med_div` | 매체구분 | `char` | 1 | 일반 | 0 |  | A:API<br>R:RESTApi<br>B:Back<br>D:DMA<br>F:FRONT<br>H:HTS<br>M:MTS<br>I:WTS<br>Y:YES<br>X:Expert<br>Z:FIX | 없음 |
|  | `err_cd` | 에러코드 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  |  | 없음 |
|  | `exec_no` | 체결번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `per_exec_qty` | 건별체결량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `hdg_tp` | 헤지구분 | `char` | 1 | 일반 | 0 |  | 0:일반, 1:헤지 | 없음 |
|  | `stop_pric` | 스탑주문가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `opt_strk_bkg_yn` | 옵션행사가예약여부 | `char` | 1 | 일반 | 0 |  |  | 없음 |
|  | `ord_ed_dt` | 주문종료일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `opt_ord_amt` | 옵션주문금액 | `char` | 15 | 일반 | 0 |  |  | 없음 |
|  | `rem_ord_qty` | 주문잔량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
|  | `ref_ord_no` | 참조 주문 번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `exec_cnd_div` | 체결조건구분 | `char` | 1 | 일반 | 0 |  | 1:FAS, 2:FOK, 3:FAK | 없음 |
|  | `cls_pstn_no` | 청산포지션번호 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `fcm_ord_rcv_tm` | FCM주문접수시간 | `char` | 14 | 일반 | 0 |  |  | 없음 |
|  | `fcm_exec_proc_tm` | FCM체결처리시간 | `char` | 14 | 일반 | 0 |  | YYYYMMDDHHMMSS | 없음 |

## Request JSON (Input)

```json
{
  "api_ver": "1",
  "action_code": "O1",
  "header": null,
  "action": null,
  "body": null
}
```

## Response JSON (Output)

```json
{
  "ord_no": "",
  "blk_no": "",
  "sym": "",
  "ord_pric": "",
  "exec_pric": "",
  "exec_cnd_div": "",
  "org_ord_dt": "",
  "med_div": "",
  "stop_pric": "",
  "mod_tp": "",
  "ord_qty": "",
  "cur_cd": "",
  "ord_sts": "",
  "mkt_tp": "",
  "str_tp": "",
  "pric_cnd": "",
  "rcv_tm": "",
  "sl_ts": "",
  "per_exec_qty": "",
  "org_ord_no": "",
  "cxl_qty": "",
  "sl_pric": "",
  "mod_qty": "",
  "ord_ed_dt": "",
  "cls_pstn_no": "",
  "work_empl": "",
  "sym_tp": "",
  "tpf_pric": "",
  "err_cd": "",
  "eff_tp": "",
  "ref_ord_no": "",
  "ord_dt": "",
  "trd_div": "",
  "exec_qty": "",
  "fcm_ord_rcv_tm": "",
  "exec_avg_pric": "",
  "exec_no": "",
  "opt_ord_amt": "",
  "hdg_tp": "",
  "ac_no": "",
  "rem_ord_qty": "",
  "fcm_exec_proc_tm": "",
  "exec_tm": "",
  "opt_strk_bkg_yn": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `O1_K`
- 원본 범위: `A1:O74`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K21 |
| OUTPUT | A23:J68 |
| Request JSON (Input) | A70:A71 |
| Response JSON (Output) | A73:A74 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
