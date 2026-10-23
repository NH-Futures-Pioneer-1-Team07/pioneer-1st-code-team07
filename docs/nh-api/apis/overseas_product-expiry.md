# 해외_만기일조회

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/product-expiry |
| API 통신 방식 | HTTP |
| API 명 | 해외_만기일조회 |
| HTTP Method | POST |
| Content-Type |  |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/product-expiry |
| API 요청 제한 | 계좌 LIMIT |

## 설명

해외 만기일조회 SGBS3577Q01

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |
|  | `rem_dy` | 잔존일 | `char` | 5 | 일반 | 0 | 30 | 기본 : 30<br>조회시 입력할 기준 잔존일 | N | 30 |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | Y |  |
|  | `fut_opt_div_cd` | 상품구분코드 | `char` | 1 | 일반 | 0 |  | 공백:전체, F:선물 O:옵션 S:스프레드 Z.기타<br>기본:공백 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym_nm` | 종목명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sett_nm` | 결제방법명 | `char` | 50 | 일반 | 0 |  | 결제방법명 (현금, 인수도) | 없음 |
| Occurs1 | `occurs1_exch_cd` | 거래소V코드 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fst_ntf_dt` | 최초통보일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_exp_dt` | 만기일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_lst_sett_dt` | 최종결제일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_rem_dy` | 잔존일자수 | `char` | 6 | 일반 | 0 |  | 만기일까지 남은 만기일 포함일 | 없음 |
| Occurs1 | `occurs1_prd_cd` | 품목코드 | `char` | 10 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "rem_dy": "30",
  "fut_opt_div_cd": "",
  "sym": "",
  "nxt_key": ""
}
```

## Response JSON (Output)

```json
{
  "nrec": "",
  "occurs1_sym": "",
  "occurs1_lst_sett_dt": "",
  "occurs1_exch_cd": "",
  "occurs1_exp_dt": "",
  "occurs1_sett_nm": "",
  "nxt_key": "",
  "occurs1_rem_dy": "",
  "Occurs1": "",
  "occurs1_fst_ntf_dt": "",
  "occurs1_prd_cd": "",
  "occurs1_sym_nm": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_product-expiry`
- 원본 범위: `A1:O41`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K20 |
| OUTPUT | A22:J35 |
| Request JSON (Input) | A37:A38 |
| Response JSON (Output) | A40:A41 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
