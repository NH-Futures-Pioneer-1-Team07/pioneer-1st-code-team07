# 해외_옵션전체시세

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/price-all-option |
| API 통신 방식 | HTTP |
| API 명 | 해외_옵션전체시세 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/price-all-option |
| API 요청 제한 | 시세 LIMIT |

## 설명

해외 옵션전체시세	PIBO7051	

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `exch_cd` | 거래소코드 | `char` | 8 | 일반 | 0 |  | 옵션구분+거래소코드<br>ex)<br>CME 옵션 : OCME<br>HKE 옵션 : OHKE | Y |  |
|  | `sym` | 월물품목코드 | `char` | 20 | 일반 | 0 |  | 옵션품목(가변) + 월물(2) +년 뒤 2자리<br>옵션품목 : O_BRN , O_ES,O_CL 등<br>월물 :<br>1월 : F<br>2월 : G<br>3월 : H<br>4월 : J<br>5월 : K<br>6월 : M<br>7월 : N<br>8월 : Q<br>9월 : U<br>10 월 : V<br>11 월 : X<br>12 월 : Z<br>ex)<br>미니S&amp;P500 2026년 9월물<br>   =&gt; O_ESU26 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nrec` | 조회건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `rem_dy` | 만기잔존일 | `char` | 4 | 일반 | 0 |  | 만기일까지 남은 만기일 포함일 | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_strk_pric` | 행사가격 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pric_ind` | 진법구분 | `char` | 1 | 일반 | 0 |  | 진법구분<br>1:정수<br>2:소수점1자리<br>3:소수점2자리<br>9:소수점8자리<br>A:1/2진법<br>B:1/4진법<br>C:1/8진법<br>D:1/16진법<br>E:1/32진법<br>F:1/64진법<br>G:1/128진법<br>H:1/256진법<br>I:0.5/32진법<br>J:0.5/64진법<br>K:0.25/32진법<br>L:0.125/32진법<br>M:0.065/32진법 | 없음 |
| Occurs1 | `occurs1_c_exec_cd` | 콜종목코드 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_sym` | 종목코드 | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_last_pric` | 콜현재가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_diff` | 콜 대비 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_rt` | 콜등락률 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_bid_pric` | 콜매수가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_ask_pric` | 콜매도가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_bid_qty` | 콜매수수량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_ask_qty` | 콜매도수량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_trd_qty` | 콜거래량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_atm_flag` | 콜ATM여부 | `char` | 1 | 일반 | 0 |  | 1:ATM | 없음 |
| Occurs1 | `occurs1_p_exec_cd` | 풋종목코드 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_sym` | 종목코드 | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_last_pric` | 풋현재가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_diff` | 풋 대비 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_rt` | 풋등락률 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_bid_pric` | 풋매수가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_ask_pric` | 풋매도가 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_bid_qty` | 풋매수수량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_ask_qty` | 풋매도수량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_trd_qty` | 풋거래량 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_atm_flag` | 풋ATM여부 | `char` | 1 | 일반 | 0 |  | 1:ATM | 없음 |

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
  "occurs1_p_bid_qty": "",
  "occurs1_p_atm_flag": "",
  "occurs1_c_sym": "",
  "occurs1_p_exec_cd": "",
  "occurs1_c_trd_qty": "",
  "occurs1_p_ask_pric": "",
  "Occurs1": "",
  "rem_dy": "",
  "nrec": "",
  "occurs1_p_ask_qty": "",
  "occurs1_c_diff": "",
  "occurs1_c_ask_qty": "",
  "occurs1_c_bid_qty": "",
  "occurs1_p_diff": "",
  "occurs1_c_atm_flag": "",
  "occurs1_c_ask_pric": "",
  "occurs1_p_rt": "",
  "occurs1_p_trd_qty": "",
  "occurs1_p_sym": "",
  "occurs1_p_last_pric": "",
  "occurs1_strk_pric": "",
  "occurs1_c_exec_cd": "",
  "occurs1_c_rt": "",
  "occurs1_c_bid_pric": "",
  "occurs1_pric_ind": "",
  "occurs1_c_last_pric": "",
  "occurs1_p_bid_pric": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_price-all-option`
- 원본 범위: `A1:O54`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K18 |
| OUTPUT | A20:J48 |
| Request JSON (Input) | A50:A51 |
| Response JSON (Output) | A53:A54 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
