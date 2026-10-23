# 국내_잔고내역

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/open-interest |
| API 통신 방식 | HTTP |
| API 명 | 국내_잔고내역 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/open-interest |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
잔고내역	SDBS3085Q01	결과 값 리스트의 구분자로 주간/야간 구분

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
| Occurs1 | `occurs1_ac_nm` | 위탁계좌명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ko_sym_nm` | 한글종목명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_div` | 매매구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | 없음 |
| Occurs1 | `occurs1_trd_div_nm_v2` | 매매구분명 | `char` | 50 | 일반 | 0 |  | 매수,매도 | 없음 |
| Occurs1 | `occurs1_fut_opt_div_cd` | 상품구분코드 | `char` | 1 | 일반 | 0 |  | 1:선물<br>2:옵션 <br>3:그외 | 없음 |
| Occurs1 | `occurs1_opint_amt` | 미결제금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opint_qty` | 미결제수량 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cls_psb_qty` | 청산가능수량 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_avg_pric` | 평균가격 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_close_pric` | 종가 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pl_amt` | 평가손익금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pl_rt` | 수익률 | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exch_cd` | 거래소코드 | `char` | 10 | 일반 | 0 |  | 국내주야간구분<br>KRX:주간<br>KRX_NDV:야간 | 없음 |

## Request JSON (Input)

```json
{
  "nxt_key": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_sym": "",
  "occurs1_close_pric": "",
  "occurs1_ko_sym_nm": "",
  "occurs1_opint_qty": "",
  "nxt_key": "",
  "occurs1_trd_div": "",
  "Occurs1": "",
  "occurs1_cls_psb_qty": "",
  "nrec": "",
  "occurs1_ac_no": "",
  "occurs1_avg_pric": "",
  "occurs1_exch_cd": "",
  "occurs1_opint_amt": "",
  "occurs1_trd_div_nm_v2": "",
  "occurs1_fut_opt_div_cd": "",
  "occurs1_pl_amt": "",
  "occurs1_ac_nm": "",
  "occurs1_pl_rt": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_open-interest`
- 원본 범위: `A1:O44`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K17 |
| OUTPUT | A19:J38 |
| Request JSON (Input) | A40:A41 |
| Response JSON (Output) | A43:A44 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
