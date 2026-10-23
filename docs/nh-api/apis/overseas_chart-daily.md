# 해외_차트(일)

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/chart-daily |
| API 통신 방식 | HTTP |
| API 명 | 해외_차트(일) |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/chart-daily |
| API 요청 제한 | 시세 LIMIT |

## 설명

```text
헤외 차트 기간별 데이터 (일) PIBO7503	

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | 거래소코드 예) FCME | Y |  |
|  | `sym` | 종목코드 | `char` | 20 | 일반 | 0 |  | 종목코드 예) 6AU26 | Y |  |
|  | `inq_strt_dt` | 조회시작일자 | `char` | 8 | 일반 | 0 | 00000000 | 기본:00000000<br>조회 시작일 | N | 00000000 |
|  | `inq_ed_dt` | 조회종료일 | `char` | 8 | 일반 | 0 | 99999999 | 기본:99999999<br>조회 종료일 <br>(조건 적용 시 시작일 필수) | N | 99999999 |
|  | `req_qty` | 요청건수 | `char` | 4 | 일반 | 0 | 300 | 기본 300건<br>(최대 9999건) | N | 300 |
|  | `cidx_yn` | 연결선물여부 | `char` | 1 | 일반 | 0 | 0 | 기본:0<br>0:안함, 1:연결 | N | 0 |
|  | `nxt_key` | 다음데이터키 | `char` | 32 | 일반 | 0 | 99999999 | 기본:99999999<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N | 99999999 |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 32 | 일반 | 0 |  | 기본:99999999 | 없음 |
|  | `exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | 거래소코드 예) FCME | 없음 |
|  | `sym` | 종목코드 | `char` | 20 | 일반 | 0 |  | 종목코드 예) 6AU26 | 없음 |
|  | `nrec` | 처리건수 | `char` | 4 | 일반 | 0 |  | 처리건수 | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_ref_dt` | 기준일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_open_pric` | 시가 | `char` | 15 | 일반 | 0 |  | 시가 | 없음 |
| Occurs1 | `occurs1_high_pric` | 고가 | `char` | 15 | 일반 | 0 |  | 고가 | 없음 |
| Occurs1 | `occurs1_low_pric` | 저가 | `char` | 15 | 일반 | 0 |  | 저가 | 없음 |
| Occurs1 | `occurs1_close_pric` | 종가 | `char` | 15 | 일반 | 0 |  | 종가 | 없음 |
| Occurs1 | `occurs1_diff_rt` | 전일대비 | `char` | 15 | 일반 | 0 |  | 전일대비 | 없음 |
| Occurs1 | `occurs1_rt` | 등락률 | `char` | 8 | 일반 | 0 |  | 등락률 | 없음 |
| Occurs1 | `occurs1_cum_trd_qty` | 누적거래량 | `char` | 9 | 일반 | 0 |  | 누적거래량 | 없음 |

## Request JSON (Input)

```json
{
  "inq_ed_dt": "99999999",
  "req_qty": "300",
  "inq_strt_dt": "00000000",
  "cidx_yn": "0",
  "exch_cd": "",
  "sym": "",
  "nxt_key": "99999999"
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
  "occurs1_rt": "",
  "nxt_key": "",
  "Occurs1": "",
  "occurs1_diff_rt": "",
  "nrec": "",
  "exch_cd": "",
  "occurs1_cum_trd_qty": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_chart-daily`
- 원본 범위: `A1:O45`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K23 |
| OUTPUT | A25:J39 |
| Request JSON (Input) | A41:A42 |
| Response JSON (Output) | A44:A45 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
