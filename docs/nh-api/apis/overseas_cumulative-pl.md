# 해외_누적손익현황

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/cumulative-pl |
| API 통신 방식 | HTTP |
| API 명 | 해외_누적손익현황 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/cumulative-pl |
| API 요청 제한 | 계좌 LIMIT |

## 설명

해외 누적손익현황 SGBS5502Q01

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |
|  | `inq_strt_dt` | 조회시작일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | Y | 00000000 |
|  | `inq_ed_dt` | 조회종료일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | Y |  |
|  | `prd_cd` | 품목코드 | `char` | 10 | 일반 | 0 |  |  | N |  |
|  | `cvs_cur_cd` | 환산통화코드 | `char` | 3 | 일반 | 0 | USD | 실제로 표시되는 통화 지정<br>기본:USD<br>USD, KRW (2가지만 사용 가능) | N | USD |
|  | `cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  | 기본:전체<br>공백:전체, USD, KRW, 등 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_prd_cd` | 품목코드 | `char` | 10 | 일반 | 0 |  | 마지막 행데이터 총합값  : -------- | 없음 |
| Occurs1 | `occurs1_prd_nm` | 품목명 | `char` | 50 | 일반 | 0 |  | 마지막 행데이터 총합값 : 환산통화의 환산합계 | 없음 |
| Occurs1 | `occurs1_cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  | USD, KRW, 등 | 없음 |
| Occurs1 | `occurs1_cls_pl_amt` | 실현손익 또는선물청산손익 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pl_amt` | 평가손익금액 | `char` | 24 | 일반 | 0 |  | 평가손익증감분 | 없음 |
| Occurs1 | `occurs1_fee` | 위탁수수료 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_net_pl_amt` | 순손익 | `char` | 24 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "inq_ed_dt": "",
  "cvs_cur_cd": "USD",
  "inq_strt_dt": "",
  "cur_cd": "",
  "nxt_key": "",
  "prd_cd": ""
}
```

## Response JSON (Output)

```json
{
  "nrec": "",
  "occurs1_fee": "",
  "occurs1_cls_pl_amt": "",
  "occurs1_cur_cd": "",
  "nxt_key": "",
  "occurs1_net_pl_amt": "",
  "Occurs1": "",
  "occurs1_prd_cd": "",
  "occurs1_pl_amt": "",
  "occurs1_prd_nm": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_cumulative-pl`
- 원본 범위: `A1:O41`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K22 |
| OUTPUT | A24:J35 |
| Request JSON (Input) | A37:A38 |
| Response JSON (Output) | A40:A41 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
