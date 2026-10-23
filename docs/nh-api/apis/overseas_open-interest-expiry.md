# 해외_보유포지션만기조회

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/open-interest-expiry |
| API 통신 방식 | HTTP |
| API 명 | 해외_보유포지션만기조회 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/open-interest-expiry |
| API 요청 제한 | 계좌 LIMIT |

## 설명

해외 보유포지션만기도래현황 SGBS3554Q01

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 | 000 | 기본 : 공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N | 000 |
|  | `und_sym` | 기초자산선물품목코드 | `char` | 10 | 일반 | 0 |  | 공백 : 전체<br>6A/6B/6C 등:품목별 조회 시 | N |  |
|  | `inq_dy_cnt` | 조회할 최대 잔존일수 | `char` | 6 | 일반 | 0 | 2000 | 공백 : 2000일 | N | 2000 |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym_nm` | 종목명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cd_nm` | 매매구분 (매도/매수) | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pstn_qty` | 포지션수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_pric` | 체결가격 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_dt` | 체결일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_dlv_sett_div_nm` | 인수도결제구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fst_ntf_dt` | 최초통보일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_exp_dt` | 만기일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_rem_dy` | 잔존일자수 | `char` | 6 | 일반 | 0 |  | 만기일까지 남은 만기일 포함일 | 없음 |

## Request JSON (Input)

```json
{
  "inq_dy_cnt": "2000",
  "nxt_key": "000",
  "und_sym": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_pstn_qty": "",
  "occurs1_sym": "",
  "occurs1_exec_pric": "",
  "nxt_key": "",
  "Occurs1": "",
  "occurs1_sym_nm": "",
  "nrec": "",
  "occurs1_exec_dt": "",
  "occurs1_exp_dt": "",
  "occurs1_cur_cd": "",
  "occurs1_rem_dy": "",
  "occurs1_dlv_sett_div_nm": "",
  "occurs1_cd_nm": "",
  "occurs1_fst_ntf_dt": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_open-interest-expiry`
- 원본 범위: `A1:O42`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K19 |
| OUTPUT | A21:J36 |
| Request JSON (Input) | A38:A39 |
| Response JSON (Output) | A41:A42 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
