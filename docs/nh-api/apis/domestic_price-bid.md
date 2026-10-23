# 국내_호가

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/price-bid |
| API 통신 방식 | HTTP |
| API 명 | 국내_호가 |
| HTTP Method | POST |
| Content-Type |  |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/price-bid |
| API 요청 제한 | 시세 LIMIT |

## 설명

호가	SDIFPIBOQ01	구분자로 주간/야간 구분  (* 야간 모의 환경 미지원)

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `exch_cd` | 거래소코드 | `char` | 3 | 일반 | 0 |  | KSP:주간, NDV:야간 | Y |  |
|  | `sym` | 종목코드 | `char` | 12 | 일반 | 0 |  |  | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `real` | 실시간종목코드 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `qt_tm` | 호가시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
|  | `ask_qty` | 총매도잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `pre_ask_qty` | 총매도잔량직전대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `ask_cnt` | 총매도건수 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_qty` | 총매수잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `pre_bid_qty` | 총매수잔량직전대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `bid_cnt` | 총매수건수 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `net_bid_ask` | 총매수매도잔량차이 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `last_pric` | 현재가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `diff_rt` | 전일대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `rt` | 등락률 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `open_pric` | 시가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `high_pric` | 고가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `low_pric` | 저가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `pd_close_pric` | 전일종가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `cum_trd_qty` | 누적거래량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `cum_trd_amt` | 거래대금 | `char` | 9 | 일반 | 0 |  |  | 없음 |
|  | `up_act_pric` | 실시간상한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `lo_act_pric` | 실시간하한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `up_pric_1` | 1단계상한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `lo_pric_1` | 1단계하한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `up_pric_2` | 2단계상한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `lo_pric_2` | 2단계하한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `up_pric_3` | 3단계상한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `lo_pric_3` | 3단계하한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `up` | 상한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `lo` | 하한가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `est_exec_pric` | 예상체결가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
|  | `nrec` | 호가 개수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}], 호가 데이터 배열의 각 항목에 대한 매도/매수 호가 정보 | 없음 |
| Occurs1 | `occurs1_ask_best_pric` | 매도호가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ask_rt` | 매도등락률 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ask_qty` | 총매도잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ask_cnt` | 총매도건수 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pre_ask_qty` | 총매도잔량직전대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_bid_best_pric` | 매수호가 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_bid_rt` | 매수호가등락률 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_bid_qty` | 총매수잔량 | `char` | 9 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_bid_cnt` | 총매수건수 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pre_bid_qty` | 총매수잔량직전대비 | `char` | 8 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "exch_cd": "",
  "sym": ""
}
```

## Response JSON (Output)

```json
{
  "rt": "",
  "lo": "",
  "occurs1_bid_best_pric": "",
  "up_act_pric": "",
  "occurs1_pre_ask_qty": "",
  "sym": "",
  "pre_ask_qty": "",
  "bid_qty": "",
  "occurs1_ask_rt": "",
  "lo_pric_3": "",
  "lo_pric_2": "",
  "Occurs1": "",
  "lo_pric_1": "",
  "occurs1_bid_cnt": "",
  "occurs1_ask_best_pric": "",
  "lo_act_pric": "",
  "nrec": "",
  "diff_rt": "",
  "cum_trd_amt": "",
  "pre_bid_qty": "",
  "net_bid_ask": "",
  "open_pric": "",
  "bid_cnt": "",
  "last_pric": "",
  "up": "",
  "pd_close_pric": "",
  "up_pric_1": "",
  "occurs1_ask_cnt": "",
  "occurs1_bid_rt": "",
  "up_pric_2": "",
  "up_pric_3": "",
  "cum_trd_qty": "",
  "high_pric": "",
  "ask_cnt": "",
  "real": "",
  "occurs1_pre_bid_qty": "",
  "est_exec_pric": "",
  "low_pric": "",
  "occurs1_ask_qty": "",
  "ask_qty": "",
  "qt_tm": "",
  "occurs1_bid_qty": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_price-bid`
- 원본 범위: `A1:O69`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K18 |
| OUTPUT | A20:J63 |
| Request JSON (Input) | A65:A66 |
| Response JSON (Output) | A68:A69 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
