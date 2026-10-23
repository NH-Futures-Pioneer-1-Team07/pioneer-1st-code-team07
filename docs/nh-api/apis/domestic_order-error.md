# 국내_주문오류내역

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/order-error |
| API 통신 방식 | HTTP |
| API 명 | 국내_주문오류내역 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/order-error |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
주문오류내역	SDBS3068Q01	

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `inq_dt` | 조회일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | Y |  |
|  | `trd_div_cd` | 매수매도구분코드 | `char` | 1 | 일반 | 0 |  | 0:전체,1:매수, 2:매도 | Y |  |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `data_tot_cnt` | 데이터전체건수 | `char` | 11 | 일반 | 0 |  |  | 없음 |
|  | `nxt_data_yn` | 다음데이터여부 | `char` | 1 | 일반 | 0 |  | Y:다음조회있음, N:다음조회없음 | 없음 |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_rcv_tm` | 접수시간 | `char` | 9 | 일반 | 0 |  | HHMMSS | 없음 |
| Occurs1 | `occurs1_ac_no` | 계좌번호 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ac_nm` | 계좌명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym_nm` | 종목명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_msg_cd` | 메세지코드 | `char` | 5 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_msg` | 메세지 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_form_cd` | 주문형태코드 | `char` | 1 | 일반 | 0 |  | 1:일반주문, 2:STOP주문 | 없음 |
| Occurs1 | `occurs1_ord_form_nm` | 주문형태명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_qty` | 주문수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_div_cd` | 매수매도구분코드 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | 없음 |
| Occurs1 | `occurs1_trd_div_nm` | 거래구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_tp_cd` | 주문유형코드 | `char` | 1 | 일반 | 0 |  | 1:지정가, 2:시장가, 7:STOP주문 | 없음 |
| Occurs1 | `occurs1_ord_tp_nm` | 주문유형명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_div_cd` | 주문구분코드 | `char` | 1 | 일반 | 0 |  | 1:신규, 2:정정, 3:취소 | 없음 |
| Occurs1 | `occurs1_ord_div_nm` | 주문구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_cnd_cd` | 체결조건코드 | `char` | 1 | 일반 | 0 |  | 1:FAS, 2:FOK, 3:FAK | 없음 |
| Occurs1 | `occurs1_exec_cnd_nm` | 체결조건명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_med_div` | 매체구분코드 | `char` | 1 | 일반 | 0 |  | A:API<br>R:RESTApi<br>B:Back<br>D:DMA<br>F:FRONT<br>H:HTS<br>M:MTS<br>I:WTS<br>Y:YES<br>X:Expert<br>Z:FIX | 없음 |
| Occurs1 | `occurs1_med_div_nm` | 매체구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_div_nm_v2` | 매매구분명 | `char` | 50 | 일반 | 0 |  | 매수,매도 | 없음 |

## Request JSON (Input)

```json
{
  "trd_div_cd": "",
  "nxt_key": "",
  "inq_dt": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_sym": "",
  "occurs1_ord_form_nm": "",
  "occurs1_ord_tp_nm": "",
  "occurs1_ord_pric": "",
  "nxt_key": "",
  "occurs1_exec_cnd_nm": "",
  "Occurs1": "",
  "nrec": "",
  "occurs1_ac_no": "",
  "occurs1_trd_div_nm": "",
  "occurs1_rcv_tm": "",
  "occurs1_exec_cnd_cd": "",
  "occurs1_trd_div_nm_v2": "",
  "occurs1_ord_div_nm": "",
  "occurs1_ac_nm": "",
  "occurs1_msg": "",
  "occurs1_ord_form_cd": "",
  "occurs1_sym_nm": "",
  "occurs1_ord_qty": "",
  "data_tot_cnt": "",
  "occurs1_org_ord_no": "",
  "occurs1_trd_div_cd": "",
  "occurs1_ord_tp_cd": "",
  "occurs1_med_div": "",
  "occurs1_ord_div_cd": "",
  "occurs1_msg_cd": "",
  "occurs1_med_div_nm": "",
  "nxt_data_yn": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_order-error`
- 원본 범위: `A1:O56`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K19 |
| OUTPUT | A21:J50 |
| Request JSON (Input) | A52:A53 |
| Response JSON (Output) | A55:A56 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
