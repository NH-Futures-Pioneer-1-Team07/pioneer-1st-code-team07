# 해외_호가

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/bid-price |
| API 통신 방식 | HTTP |
| API 명 | 해외_호가 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/bid-price |
| API 요청 제한 | 시세 LIMIT |

## 설명

해외 호가  PIBO7012	

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | F:선물, O:옵션<br>선물/옵션 + 거래소코드<br>예) CME 선물 : FCME | Y |  |
|  | `sym` | 종목코드 | `char` | 20 | 일반 | 0 |  | 종목코드<br>예) 6AU26 | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | 예) CME | 없음 |
|  | `sym` | 종목코드 | `char` | 20 | 일반 | 0 |  | 종목코드   예) 6AU26 | 없음 |
|  | `real_sym` | 실시간종목코드 | `char` | 20 | 일반 | 0 |  | 실시간종목코드   예) 6AU26 | 없음 |
|  | `last_pric` | 현재가 | `char` | 15 | 일반 | 0 |  | 현재가 | 없음 |
|  | `diff_rt` | 전일대비 | `char` | 15 | 일반 | 0 |  | 등락폭 | 없음 |
|  | `rt` | 등락률 | `char` | 12 | 일반 | 0 |  | 등락률 | 없음 |
|  | `open_pric` | 시가 | `char` | 15 | 일반 | 0 |  | 시가 | 없음 |
|  | `high_pric` | 고가 | `char` | 15 | 일반 | 0 |  | 고가 | 없음 |
|  | `low_pric` | 저가 | `char` | 15 | 일반 | 0 |  | 저가 | 없음 |
|  | `pre_close_pric` | 전일종가 | `char` | 15 | 일반 | 0 |  | 전일종가 | 없음 |
|  | `cum_trd_qty` | 누적거래량 | `char` | 12 | 일반 | 0 |  | 누적거래량 | 없음 |
|  | `exec_qty` | 체결량 | `char` | 12 | 일반 | 0 |  | 체결수량 | 없음 |
|  | `qt_rcv_tm` | 호가접수시간 | `char` | 6 | 일반 | 0 |  | 시간표시 (HHMMSS) | 없음 |
|  | `ask_pric_1` | 매도호가1 | `char` | 15 | 일반 | 0 |  | 매도호가1 | 없음 |
|  | `ask_qty_1` | 매도잔량1 | `char` | 12 | 일반 | 0 |  | 매도잔량1 | 없음 |
|  | `ask_cnt_1` | 매도건수1 | `char` | 12 | 일반 | 0 |  | 매도건수1 | 없음 |
|  | `ask_rt_1` | 매도등락률1 | `char` | 9 | 일반 | 0 |  | 매도등락률1 | 없음 |
|  | `bid_pric_1` | 매수호가1 | `char` | 15 | 일반 | 0 |  | 매수호가1 | 없음 |
|  | `bid_qty_1` | 매수잔량1 | `char` | 12 | 일반 | 0 |  | 매수잔량1 | 없음 |
|  | `bid_cnt_1` | 매수건수1 | `char` | 12 | 일반 | 0 |  | 매수건수1 | 없음 |
|  | `bid_rt_1` | 매수등락률1 | `char` | 9 | 일반 | 0 |  | 매수등락률1 | 없음 |
|  | `ask_pric_2` | 매도호가2 | `char` | 15 | 일반 | 0 |  | 매도호가2 | 없음 |
|  | `ask_qty_2` | 매도잔량2 | `char` | 12 | 일반 | 0 |  | 매도잔량2 | 없음 |
|  | `ask_cnt_2` | 매도건수2 | `char` | 12 | 일반 | 0 |  | 매도건수2 | 없음 |
|  | `ask_rt_2` | 매도등락률2 | `char` | 9 | 일반 | 0 |  | 매도등락률2 | 없음 |
|  | `bid_pric_2` | 매수호가2 | `char` | 15 | 일반 | 0 |  | 매수호가2 | 없음 |
|  | `bid_qty_2` | 매수잔량2 | `char` | 12 | 일반 | 0 |  | 매수잔량2 | 없음 |
|  | `bid_cnt_2` | 매수건수2 | `char` | 12 | 일반 | 0 |  | 매수건수2 | 없음 |
|  | `bid_rt_2` | 매수등락률2 | `char` | 9 | 일반 | 0 |  | 매수등락률2 | 없음 |
|  | `ask_pric_3` | 매도호가3 | `char` | 15 | 일반 | 0 |  | 매도호가3 | 없음 |
|  | `ask_qty_3` | 매도잔량3 | `char` | 12 | 일반 | 0 |  | 매도잔량3 | 없음 |
|  | `ask_cnt_3` | 매도건수3 | `char` | 12 | 일반 | 0 |  | 매도건수3 | 없음 |
|  | `ask_rt_3` | 매도등락률3 | `char` | 9 | 일반 | 0 |  | 매도등락률3 | 없음 |
|  | `bid_pric_3` | 매수호가3 | `char` | 15 | 일반 | 0 |  | 매수호가3 | 없음 |
|  | `bid_qty_3` | 매수잔량3 | `char` | 12 | 일반 | 0 |  | 매수잔량3 | 없음 |
|  | `bid_cnt_3` | 매수건수3 | `char` | 12 | 일반 | 0 |  | 매수건수3 | 없음 |
|  | `bid_rt_3` | 매수등락률3 | `char` | 9 | 일반 | 0 |  | 매수등락률3 | 없음 |
|  | `ask_pric_4` | 매도호가4 | `char` | 15 | 일반 | 0 |  | 매도호가4 | 없음 |
|  | `ask_qty_4` | 매도잔량4 | `char` | 12 | 일반 | 0 |  | 매도잔량4 | 없음 |
|  | `ask_cnt_4` | 매도건수4 | `char` | 12 | 일반 | 0 |  | 매도건수4 | 없음 |
|  | `ask_rt_4` | 매도등락률4 | `char` | 9 | 일반 | 0 |  | 매도등락률4 | 없음 |
|  | `bid_pric_4` | 매수호가4 | `char` | 15 | 일반 | 0 |  | 매수호가4 | 없음 |
|  | `bid_qty_4` | 매수잔량4 | `char` | 12 | 일반 | 0 |  | 매수잔량4 | 없음 |
|  | `bid_cnt_4` | 매수건수4 | `char` | 12 | 일반 | 0 |  | 매수건수4 | 없음 |
|  | `bid_rt_4` | 매수등락률4 | `char` | 9 | 일반 | 0 |  | 매수등락률4 | 없음 |
|  | `ask_pric_5` | 매도호가5 | `char` | 15 | 일반 | 0 |  | 매도호가5 | 없음 |
|  | `ask_qty_5` | 매도잔량5 | `char` | 12 | 일반 | 0 |  | 매도잔량5 | 없음 |
|  | `ask_cnt_5` | 매도건수5 | `char` | 12 | 일반 | 0 |  | 매도건수5 | 없음 |
|  | `ask_rt_5` | 매도등락률5 | `char` | 9 | 일반 | 0 |  | 매도등락률5 | 없음 |
|  | `bid_pric_5` | 매수호가5 | `char` | 15 | 일반 | 0 |  | 매수호가5 | 없음 |
|  | `bid_qty_5` | 매수잔량5 | `char` | 12 | 일반 | 0 |  | 매수잔량5 | 없음 |
|  | `bid_cnt_5` | 매수건수5 | `char` | 12 | 일반 | 0 |  | 매수건수5 | 없음 |
|  | `bid_rt_5` | 매수등락률5 | `char` | 9 | 일반 | 0 |  | 매수등락률5 | 없음 |
|  | `ask_qty` | 총매도잔량 | `char` | 12 | 일반 | 0 |  | 총매도잔량 | 없음 |
|  | `bid_qty` | 총매수잔량 | `char` | 12 | 일반 | 0 |  | 총매수잔량 | 없음 |
|  | `ask_cnt` | 총매도건수 | `char` | 12 | 일반 | 0 |  | 총매도건수 | 없음 |
|  | `bid_cnt` | 총매수건수 | `char` | 12 | 일반 | 0 |  | 총매수건수 | 없음 |
|  | `pre_ask_qty` | 변경매도거래량 | `char` | 9 | 일반 | 0 |  | 변경매도거래량 | 없음 |
|  | `pre_bid_qty` | 변경매수거래량 | `char` | 9 | 일반 | 0 |  | 변경매수거래량 | 없음 |
|  | `biz_dt` | 영업일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |

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
  "ask_cnt_3": "",
  "ask_cnt_2": "",
  "ask_cnt_1": "",
  "biz_dt": "",
  "pre_ask_qty": "",
  "bid_qty": "",
  "ask_cnt_5": "",
  "ask_cnt_4": "",
  "exch_cd": "",
  "pre_bid_qty": "",
  "bid_qty_3": "",
  "bid_qty_4": "",
  "bid_qty_5": "",
  "cum_trd_qty": "",
  "high_pric": "",
  "ask_cnt": "",
  "bid_qty_1": "",
  "bid_qty_2": "",
  "exec_qty": "",
  "ask_rt_4": "",
  "ask_rt_3": "",
  "ask_rt_5": "",
  "ask_rt_2": "",
  "ask_rt_1": "",
  "bid_rt_1": "",
  "bid_rt_2": "",
  "rt": "",
  "sym": "",
  "bid_rt_5": "",
  "bid_rt_3": "",
  "bid_rt_4": "",
  "diff_rt": "",
  "open_pric": "",
  "bid_cnt_1": "",
  "bid_cnt_2": "",
  "bid_cnt": "",
  "last_pric": "",
  "bid_cnt_3": "",
  "bid_cnt_4": "",
  "bid_cnt_5": "",
  "ask_pric_2": "",
  "ask_pric_1": "",
  "ask_pric_4": "",
  "ask_pric_3": "",
  "real_sym": "",
  "pre_close_pric": "",
  "ask_pric_5": "",
  "qt_rcv_tm": "",
  "low_pric": "",
  "ask_qty_2": "",
  "bid_pric_3": "",
  "ask_qty_1": "",
  "bid_pric_4": "",
  "bid_pric_1": "",
  "ask_qty": "",
  "bid_pric_2": "",
  "ask_qty_5": "",
  "ask_qty_4": "",
  "bid_pric_5": "",
  "ask_qty_3": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_bid-price`
- 원본 범위: `A1:O87`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K18 |
| OUTPUT | A20:J81 |
| Request JSON (Input) | A83:A84 |
| Response JSON (Output) | A86:A87 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
