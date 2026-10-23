# 국내_현재가(야간)

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/price-night |
| API 통신 방식 | HTTP |
| API 명 | 국내_현재가(야간) |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/price-night |
| API 요청 제한 | 시세 LIMIT |

## 설명

```text
현재가 (야간)	SDIF7223Q01  (* 모의 환경 미지원)

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `chg_sign` | 전일대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
|  | `sym_exch` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
|  | `sym_nm` | 종목명 | `char` | 30 | 일반 | 0 |  |  | 없음 |
|  | `last_pric` | 현재가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `ref_pric` | 기준가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `chg` | 전일대비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `rt` | 등락률 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `ask_pric` | 매도호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `bid_pric` | 매수호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `trd_qty` | 거래량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `pd_trd_qty` | 전일거래량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `trd_amt` | 거래대금 | `char` | 16 | 일반 | 0 |  | 단위(백만) | 없음 |
|  | `pd_trd_amt` | 전일거래대금 | `char` | 16 | 일반 | 0 |  | 단위(백만) | 없음 |
|  | `opint` | 미결제약정 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `opint_chg_sign` | 미결제대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
|  | `opint_chg` | 미결제약정대비 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `life_high_pric` | 월물최고가 | `char` | 16 | 일반 | 1 |  |  | 없음 |
|  | `high_pric_dt` | 최고가일 | `char` | 8 | 일반 | 1 |  | YYYYMMDD | 없음 |
|  | `life_low_pric` | 월물최저가 | `char` | 16 | 일반 | 1 |  |  | 없음 |
|  | `low_pric_dt` | 최저가일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `up` | 상한가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `lo` | 하한가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `open_pric` | 시가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `high_pric` | 고가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `low_pric` | 저가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `pd_close_pric` | 전일종가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `lst_trd_dt` | 최종거래일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `rem_dy` | 잔존일수 | `char` | 5 | 일반 | 0 |  | 만기일까지 남은 만기일 포함일 | 없음 |
|  | `pl_rt` | 수익률 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `spt_cd` | 현물 대상물코드 | `char` | 2 | 일반 | 0 |  | ex) A0169000:01, A7569000:75 | 없음 |
|  | `spt_sym` | 현물대상 종목코드 | `char` | 32 | 일반 | 0 |  | ex) A0169000:KRD020020016, A7569000:USD | 없음 |
|  | `spt_chg_sign` | 현물가대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
|  | `spt_pric` | 현물가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `spt_chg` | 현물가 증감 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `spt_rt` | 현물가 대비율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `theo_bas` | 이론베이시스 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `fact_bas` | 실제베이시스 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `dev` | 괴리도 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `dev_rt` | 괴리율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `theo_pric` | 이론가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `ivol` | 내재변동성 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `theo_pric_chg` | 이론가대비 | `char` | 16 | 일반 | 0 |  | 이론가의 이전 대비 | 없음 |
|  | `pd_theo_pric` | 전일이론가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `pd_opint` | 전일미결제약정 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `mltplr` | 거래승수 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `act_pric_yn` | 동적가격제한여부(Y/N) | `char` | 1 | 일반 | 0 |  | (미사용) | 없음 |
|  | `up_act_pric` | 실시간상한가 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `lo_act_pric` | 실시간하한가 | `char` | 10 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "sym": null
}
```

## Response JSON (Output)

```json
{
  "spt_chg": "",
  "theo_bas": "",
  "rt": "",
  "low_pric_dt": "",
  "lo": "",
  "up_act_pric": "",
  "dev_rt": "",
  "mltplr": "",
  "rem_dy": "",
  "lo_act_pric": "",
  "ref_pric": "",
  "pd_trd_amt": "",
  "trd_qty": "",
  "dev": "",
  "life_high_pric": null,
  "spt_rt": "",
  "open_pric": "",
  "theo_pric_chg": "",
  "spt_chg_sign": "",
  "last_pric": "",
  "up": "",
  "pd_close_pric": "",
  "lst_trd_dt": "",
  "chg": "",
  "spt_sym": "",
  "ask_pric": "",
  "trd_amt": "",
  "spt_pric": "",
  "pd_trd_qty": "",
  "high_pric": "",
  "pd_theo_pric": "",
  "chg_sign": "",
  "bid_pric": "",
  "high_pric_dt": null,
  "sym_nm": "",
  "opint_chg_sign": "",
  "fact_bas": "",
  "sym_exch": "",
  "opint_chg": "",
  "act_pric_yn": "",
  "spt_cd": "",
  "low_pric": "",
  "theo_pric": "",
  "pl_rt": "",
  "ivol": "",
  "pd_opint": "",
  "opint": "",
  "life_low_pric": null
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_price-night`
- 원본 범위: `A1:O74`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K17 |
| OUTPUT | A19:J68 |
| Request JSON (Input) | A70:A71 |
| Response JSON (Output) | A73:A74 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
