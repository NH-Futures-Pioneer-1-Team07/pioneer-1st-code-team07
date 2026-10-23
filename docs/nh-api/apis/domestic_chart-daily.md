# 국내_차트(일)

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/chart-daily |
| API 통신 방식 | HTTP |
| API 명 | 국내_차트(일) |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/chart-daily |
| API 요청 제한 | 시세 LIMIT |

## 설명

차트 기간별 데이터 (일/주/월) SDIF7201Q03	 (구분자로 주간/야간 구분)  (* 야간 모의 환경 미지원)

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nght_tp` | 주야간구분 | `char` | 1 | 일반 | 0 |  | 1:주간, 2:야간 | Y |  |
|  | `sym` | 종목코드 | `char` | 12 | 일반 | 0 |  |  | Y |  |
|  | `inq_strt_dt` | 조회 시작일 | `char` | 8 | 일반 | 0 | 00000000 | 기본:00000000<br>조회 시작일 | N | 00000000 |
|  | `inq_ed_dt` | 조회 종료일 | `char` | 8 | 일반 | 0 | 99999999 | 기본:99999999<br>조회 종료일 <br>(조건 적용 시 시작일 필수) | N | 99999999 |
|  | `req_qty` | 요청건수 | `char` | 4 | 일반 | 0 | 300 | 기본 300건<br>(최대 9999건) | N | 300 |
|  | `cidx_yn` | 연결지수여부 | `char` | 1 | 일반 | 0 | 0 | 기본:0<br>0:안함, 1:연결 | N | 0 |
|  | `nxt_key` | 다음데이터키 | `char` | 24 | 일반 | 0 | 99999999 | 기본:99999999,<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N | 99999999 |
|  | `fut_cidx_exp_mod` | 연속선물 만기수정 | `char` | 1 | 일반 | 0 | 0 | 기본:0<br>0:수정안함, 1:만기수정 | N | 0 |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `nght_tp` | 주야간구분 | `char` | 1 | 일반 | 0 |  | 1:주간, 2:야간 | 없음 |
|  | `sym` | 종목코드 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `nrec` | 데이터개수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_ref_dt` | 기준일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_open_pric` | 시가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_high_pric` | 고가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_low_pric` | 저가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_close_pric` | 종가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_diff_rt` | 전일대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cum_trd_qty` | 누적거래량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opint` | 미결제약정 | `char` | 9 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "inq_ed_dt": "99999999",
  "req_qty": "300",
  "inq_strt_dt": "00000000",
  "cidx_yn": "0",
  "nght_tp": "",
  "sym": "",
  "nxt_key": "99999999",
  "fut_cidx_exp_mod": "0"
}
```

## Response JSON (Output)

```json
{
  "occurs1_ref_dt": "",
  "occurs1_open_pric": "",
  "occurs1_high_pric": "",
  "occurs1_low_pric": "",
  "sym": "",
  "occurs1_close_pric": "",
  "nxt_key": "",
  "Occurs1": "",
  "occurs1_diff_rt": "",
  "nrec": "",
  "nght_tp": "",
  "occurs1_opint": "",
  "occurs1_cum_trd_qty": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_chart-daily`
- 원본 범위: `A1:O46`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K24 |
| OUTPUT | A26:J40 |
| Request JSON (Input) | A42:A43 |
| Response JSON (Output) | A45:A46 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
