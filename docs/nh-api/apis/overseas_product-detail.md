# 해외_품목별세부정보

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/product-detail |
| API 통신 방식 | HTTP |
| API 명 | 해외_품목별세부정보 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/product-detail |
| API 요청 제한 | 계좌 LIMIT |

## 설명

해외 품목별 세부정보	SGBS7108Q01	 상품명세 + 증거금

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |
|  | `fut_opt_div_cd` | 상품구분코드 | `char` | 1 | 일반 | 0 |  | 공백:전체, F:선물, O:옵션, S:스프레드 | N |  |
|  | `prd_grp_cd` | 품목그룹코드 | `char` | 3 | 일반 | 0 |  | 공백:전체, FG1:금리, FG2:통화, <br>FG3:지수, FG4:금속, FG5:농축산물<br>FG6:에너지, FG9:SOFT | N |  |
|  | `exch_cd` | 거래소코드 | `char` | 10 | 일반 | 0 |  | 공백:전체 | N |  |
|  | `cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  | 공백:전체 | N |  |
|  | `sett_cd` | 결제구분코드 | `char` | 1 | 일반 | 0 |  | 결제구분코드<br>공백:전체조회<br>1:현금결제<br>2:실물인수도 | N |  |
|  | `prd_cd` | 검색구분코드 | `char` | 1 | 일반 | 0 |  | 상품검색구분<br>공백:전체<br>1:상품명 (prd_nm에 이름 필요)<br>2:상품코드 | N |  |
|  | `prd_nm` | 품목명 | `char` | 50 | 일반 | 0 |  | prd_cd(검색구분코드)에 따라 입력<br>공백:공백<br>1:품목명<br>2:공백 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 5 | 일반 | 0 |  | 그리드01건수 | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_prd_cd` | 품목코드 | `char` | 10 | 일반 | 0 |  | 상품코드 | 없음 |
| Occurs1 | `occurs1_ko_prd_nm` | 상품명(한글) | `char` | 50 | 일반 | 0 |  | 상품명(한글) | 없음 |
| Occurs1 | `occurs1_fut_opt_div_cd` | 상품구분코드 | `char` | 1 | 일반 | 0 |  | F:선물, O:옵션, S:스프레드, Z:기타 | 없음 |
| Occurs1 | `occurs1_prd_grp_nm` | 품목그룹명 | `char` | 50 | 일반 | 0 |  | 상품군 | 없음 |
| Occurs1 | `occurs1_exch_cd` | 거래소V코드 | `char` | 10 | 일반 | 0 |  | 거래소코드<br>예) CME | 없음 |
| Occurs1 | `occurs1_cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  | 거래통화<br>예) USD | 없음 |
| Occurs1 | `occurs1_ctr_unt` | 계약단위 | `char` | 26 | 일반 | 0 |  | 계약단위 | 없음 |
| Occurs1 | `occurs1_tick_unt` | 틱사이즈 | `char` | 30 | 일반 | 0 |  | 틱사이즈 | 없음 |
| Occurs1 | `occurs1_tick_val` | 틱값 | `char` | 26 | 일반 | 0 |  | 틱값 | 없음 |
| Occurs1 | `occurs1_dlv_div` | 인수도구분 | `char` | 1 | 일반 | 0 |  | 1:현금, 2:인수도 | 없음 |
| Occurs1 | `occurs1_apl_dt` | 등록일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |

## Request JSON (Input)

```json
{
  "sett_cd": "",
  "fut_opt_div_cd": "",
  "cur_cd": "",
  "prd_grp_cd": "",
  "exch_cd": "",
  "nxt_key": "",
  "prd_nm": "",
  "prd_cd": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_dlv_div": "",
  "nxt_key": "",
  "occurs1_apl_dt": "",
  "Occurs1": "",
  "occurs1_prd_cd": "",
  "occurs1_tick_unt": "",
  "nrec": "",
  "occurs1_exch_cd": "",
  "occurs1_prd_grp_nm": "",
  "occurs1_cur_cd": "",
  "occurs1_ko_prd_nm": "",
  "occurs1_tick_val": "",
  "occurs1_ctr_unt": "",
  "occurs1_fut_opt_div_cd": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_product-detail`
- 원본 범위: `A1:O47`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K24 |
| OUTPUT | A26:J41 |
| Request JSON (Input) | A43:A44 |
| Response JSON (Output) | A46:A47 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
