# 해외_잔고내역

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/open-interest |
| API 통신 방식 | HTTP |
| API 명 | 해외_잔고내역 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/open-interest |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
해외 잔고내역	SGBS9001Q03	

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_ac_no` | 계좌번호 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fut_opt_tp` | 선물옵션구분 | `char` | 1 | 일반 | 0 |  | 1:선물, 2:옵션, 3:스프레드 | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_tp` | 매수매도구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | 없음 |
| Occurs1 | `occurs1_td_opint_qty` | 당일미결제수량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pd_buy_opint_qty` | 전일매수미결제수량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pd_sel_opint_qty` | 전일매도미결제수량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opint_qty` | 미결제량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cls_psb_qty` | 청산가능수량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_buy_urez_exec_qty` | 매수미체결수량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sel_urez_exec_qty` | 매도미체결수량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_avg_pric` | 평균단가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pl_amt` | 평가손익 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_usd_exrt` | 원화환산환율 | `char` | 21 | 일반 | 0 |  | USD, HKD, 등 | 없음 |
| Occurs1 | `occurs1_last_pric` | 현재가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_amt` | 거래금액 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ctr_unt_amt` | 계약당금액 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pstn_blc_amt` | 포지션잔고금액 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pstn_amt` | 포지션평가금액 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exp_dt` | 만기일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |

## Request JSON (Input)

```json
{
  "nxt_key": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_sel_urez_exec_qty": "",
  "occurs1_sym": "",
  "occurs1_pd_buy_opint_qty": "",
  "occurs1_last_pric": "",
  "occurs1_pstn_blc_amt": "",
  "occurs1_td_opint_qty": "",
  "occurs1_opint_qty": "",
  "nxt_key": "",
  "Occurs1": "",
  "occurs1_cls_psb_qty": "",
  "occurs1_ctr_unt_amt": "",
  "nrec": "",
  "occurs1_ac_no": "",
  "occurs1_buy_urez_exec_qty": "",
  "occurs1_avg_pric": "",
  "occurs1_trd_amt": "",
  "occurs1_usd_exrt": "",
  "occurs1_pstn_amt": "",
  "occurs1_exp_dt": "",
  "occurs1_cur_cd": "",
  "occurs1_fut_opt_tp": "",
  "occurs1_trd_tp": "",
  "occurs1_pd_sel_opint_qty": "",
  "occurs1_pl_amt": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_open-interest`
- 원본 범위: `A1:O50`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K17 |
| OUTPUT | A19:J44 |
| Request JSON (Input) | A46:A47 |
| Response JSON (Output) | A49:A50 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
