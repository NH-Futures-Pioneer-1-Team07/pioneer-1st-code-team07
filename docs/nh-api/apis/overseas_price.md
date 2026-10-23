# 해외_현재가

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/price |
| API 통신 방식 | HTTP |
| API 명 | 해외_현재가 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/price |
| API 요청 제한 | 시세 LIMIT |

## 설명

해외 현재가	PIBO7011D	

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `Iccurs1` | Iccurs1 |  | 0 | Object | 1 |  | 객체 | N |  |
| Iccurs1 | `iccurs1_exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | F:선물, O:옵션<br>선물/옵션 + 거래소코드<br>예) CME 선물 : FCME | Y |  |
| Iccurs1 | `iccurs1_sym` | 종목코드 | `char` | 20 | 일반 | 0 |  | 종목코드  <br>예) 6AU26 | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nrec` | 처리건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | 거래소코드<br>예)  CME | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 20 | 일반 | 0 |  | 종목코드  <br>예) 6AU26 | 없음 |
| Occurs1 | `occurs1_real_sym` | 실시간종목코드 | `char` | 20 | 일반 | 0 |  | 실시간종목코드 <br>예) 6AU26 | 없음 |
| Occurs1 | `occurs1_sym_nm` | 종목명 | `char` | 50 | 일반 | 0 |  | 종목명 | 없음 |
| Occurs1 | `occurs1_last_pric` | 현재가 | `char` | 15 | 일반 | 0 |  | 현재가 | 없음 |
| Occurs1 | `occurs1_diff_rt` | 전일대비 | `char` | 15 | 일반 | 0 |  | 등락폭 | 없음 |
| Occurs1 | `occurs1_rt` | 등락률 | `char` | 12 | 일반 | 0 |  | 등락률 | 없음 |
| Occurs1 | `occurs1_open_pric` | 시가 | `char` | 15 | 일반 | 0 |  | 시가 | 없음 |
| Occurs1 | `occurs1_high_pric` | 고가 | `char` | 15 | 일반 | 0 |  | 고가 | 없음 |
| Occurs1 | `occurs1_low_pric` | 저가 | `char` | 15 | 일반 | 0 |  | 저가 | 없음 |
| Occurs1 | `occurs1_bid_pric` | 매수가 | `char` | 15 | 일반 | 0 |  | 매수호가 | 없음 |
| Occurs1 | `occurs1_ask_pric` | 매도가 | `char` | 15 | 일반 | 0 |  | 매도호가 | 없음 |
| Occurs1 | `occurs1_bid_qty` | 매수수량 | `char` | 12 | 일반 | 0 |  | 매수호가수량 | 없음 |
| Occurs1 | `occurs1_ask_qty` | 매도수량 | `char` | 12 | 일반 | 0 |  | 매도호가수량 | 없음 |
| Occurs1 | `occurs1_cum_trd_qty` | 누적거래량 | `char` | 12 | 일반 | 0 |  | 거래량 | 없음 |
| Occurs1 | `occurs1_sett_pric` | 정산가 | `char` | 15 | 일반 | 0 |  | 정산가 | 없음 |
| Occurs1 | `occurs1_pre_sett_dy` | 최종결제일 | `char` | 8 | 일반 | 1 |  | 최종결제일 | 없음 |
| Occurs1 | `occurs1_biz_dt` | 영업일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_trd_tm` | 거래시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
| Occurs1 | `occurs1_life_high_pric` | 월물최고가 | `char` | 15 | 일반 | 0 |  | 해당 월물의 최고가&#32; | 없음 |
| Occurs1 | `occurs1_life_high_dt` | 월물최고가일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_life_low_pric` | 월물최저가 | `char` | 15 | 일반 | 0 |  | 해당 월물의 최저가&#32; | 없음 |
| Occurs1 | `occurs1_life_low_dt` | 월물최저가일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_pre_close_pric` | 전일종가 | `char` | 15 | 일반 | 0 |  | 전일종가 | 없음 |
| Occurs1 | `occurs1_ris_trd_qty` | 상승거래량 | `char` | 12 | 일반 | 0 |  | 상승거래량 | 없음 |
| Occurs1 | `occurs1_fal_trd_qty` | 하강거래량 | `char` | 12 | 일반 | 1 |  | 하강거래량 | 없음 |

## Request JSON (Input)

```json
{
  "iccurs1_exch_cd": "",
  "Iccurs1": "",
  "iccurs1_sym": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_sym": "",
  "occurs1_high_pric": "",
  "occurs1_last_pric": "",
  "occurs1_rt": "",
  "occurs1_life_high_dt": "",
  "occurs1_sett_pric": "",
  "occurs1_life_low_dt": "",
  "Occurs1": "",
  "occurs1_ris_trd_qty": "",
  "nrec": "",
  "occurs1_fal_trd_qty": null,
  "occurs1_life_high_pric": "",
  "occurs1_pre_close_pric": "",
  "occurs1_biz_dt": "",
  "occurs1_cum_trd_qty": "",
  "occurs1_open_pric": "",
  "occurs1_low_pric": "",
  "occurs1_ask_pric": "",
  "occurs1_diff_rt": "",
  "occurs1_sym_nm": "",
  "occurs1_life_low_pric": "",
  "occurs1_exch_cd": "",
  "occurs1_bid_pric": "",
  "occurs1_trd_tm": "",
  "occurs1_real_sym": "",
  "occurs1_ask_qty": "",
  "occurs1_bid_qty": "",
  "occurs1_pre_sett_dy": null
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_price`
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
