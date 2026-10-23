# 국내_옵션전체시세

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/price-all-option |
| API 통신 방식 | HTTP |
| API 명 | 국내_옵션전체시세 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/price-all-option |
| API 요청 제한 | 시세 LIMIT |

## 설명

옵션전체시세	SDIF7057Q03

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `prd` | 품목코드 | `char` | 2 | 일반 | 0 |  | 01:코스피200<br>05:미니코스피200<br>06:코스닥150 | Y |  |
|  | `exp_mon` | 만기년월 | `char` | 6 | 일반 | 0 |  | YYMMDD<br>종목정보의 옵션종목 만기일값 8자리중 뒤 6자리만 사용 | Y |  |
|  | `nxt_stkr_pric` | 다음 행사가 | `char` | 16 | 일반 | 0 | 99999999 | 기본:99999999<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N | 99999999 |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_stkr_pric` | 다음 행사가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `spt_cd` | 현물 대상물코드 | `char` | 2 | 일반 | 0 |  | ex) A0169000:01, A7569000:75 | 없음 |
|  | `spt_sym` | 현물대상 종목코드 | `char` | 32 | 일반 | 0 |  | ex) A0169000:KRD020020016, A7569000:USD | 없음 |
|  | `und_nm` | 기초자산명 | `char` | 30 | 일반 | 0 |  |  | 없음 |
|  | `chg_sign` | 전일대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
|  | `spt_pric` | 현물가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `chg` | 전일대비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `rt` | 등락률 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `fut_sym` | 선물종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
|  | `fut_last_pric` | 당월선물현재가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `fut_sign` | 당월선물대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
|  | `fut_chg` | 당월선물대비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `fut_rt` | 당월선물등락률 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `fut_rem_dy` | 당월선물잔존일수 | `char` | 16 | 일반 | 0 |  | 만기일까지 남은 만기일 포함일 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_c_sym_exch` | 콜종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_sym_nm` | 콜종목명 | `char` | 30 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_chg_sign` | 콜대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
| Occurs1 | `occurs1_c_pd_close_pric` | 전일종가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_last_pric` | 현재가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_chg_rt` | 전일대비율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_chg` | 전일비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_open_pric` | 콜시가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_high_pric` | 콜고가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_low_pric` | 콜저가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_ask_pric` | 콜매도호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_bid_pric` | 콜매수호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_opint` | 콜미결제약정 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_opint_chg` | 콜미결제약정대비 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_trd_qty` | 콜거래량 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_theo_pric` | 콜이론가 | `char` | 16 | 일반 | 0 |  | 시장 가격이 고평가인지 저평가인지 판단 기준 | 없음 |
| Occurs1 | `occurs1_c_theo_pric_chg` | 이론가대비 | `char` | 16 | 일반 | 0 |  | 이론가의 이전 대비 | 없음 |
| Occurs1 | `occurs1_c_vol` | 변동성(IV) | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_dev` | 콜괴리도 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_dev_rt` | 콜괴리율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_delta` | 콜델타 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_gamma` | 콜감마 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_theta` | 콜세타 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_vega` | 콜베가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_c_rho` | 콜로 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_strk_pric` | 행사가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_sym_exch` | 풋종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_sym_nm` | 풋종목명 | `char` | 30 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_chg_sign` | 풋대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
| Occurs1 | `occurs1_p_pd_close_pric` | 전일종가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_last_pric` | 현재가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_chg_rt` | 전일대비율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_chg` | 전일비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_open_pric` | 풋시가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_high_pric` | 풋고가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_low_pric` | 풋저가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_ask_pric` | 풋매도호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_bid_pric` | 풋매수호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_opint` | 풋미결제약정 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_opint_chg` | 풋미결제약정대비 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_trd_qty` | 풋거래량 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_theo_pric` | 풋이론가 | `char` | 16 | 일반 | 0 |  | 시장 가격이 고평가인지 저평가인지 판단 기준 | 없음 |
| Occurs1 | `occurs1_p_theo_pric_chg` | 이론가대비 | `char` | 16 | 일반 | 0 |  | 이론가의 이전 대비 | 없음 |
| Occurs1 | `occurs1_p_vol` | 변동성(IV) | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_dev` | 풋괴리도 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_dev_rt` | 풋괴리율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_delta` | 풋델타 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_gamma` | 풋감마 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_theta` | 풋세타 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_vega` | 풋베가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_p_rho` | 풋로 | `char` | 16 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "prd": "",
  "nxt_stkr_pric": "99999999",
  "exp_mon": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_c_sym_nm": "",
  "fut_rt": "",
  "occurs1_p_chg_sign": "",
  "occurs1_p_pd_close_pric": "",
  "occurs1_p_ask_pric": "",
  "occurs1_c_theo_pric_chg": "",
  "occurs1_p_low_pric": "",
  "occurs1_p_gamma": "",
  "occurs1_c_vega": "",
  "occurs1_p_vega": "",
  "fut_rem_dy": "",
  "fut_chg": "",
  "occurs1_c_chg_rt": "",
  "occurs1_p_chg_rt": "",
  "occurs1_p_dev_rt": "",
  "occurs1_p_sym_exch": "",
  "occurs1_p_rho": "",
  "occurs1_p_opint_chg": "",
  "chg": "",
  "occurs1_c_pd_close_pric": "",
  "occurs1_c_chg": "",
  "spt_sym": "",
  "occurs1_p_vol": "",
  "occurs1_p_trd_qty": "",
  "occurs1_p_last_pric": "",
  "occurs1_strk_pric": "",
  "occurs1_p_high_pric": "",
  "fut_last_pric": "",
  "occurs1_p_theo_pric": "",
  "nxt_stkr_pric": "",
  "occurs1_p_theo_pric_chg": "",
  "occurs1_c_dev": "",
  "occurs1_c_open_pric": "",
  "occurs1_c_last_pric": "",
  "occurs1_p_delta": "",
  "occurs1_c_delta": "",
  "occurs1_p_bid_pric": "",
  "rt": "",
  "occurs1_p_opint": "",
  "occurs1_c_trd_qty": "",
  "Occurs1": "",
  "nrec": "",
  "occurs1_c_sym_exch": "",
  "occurs1_c_opint_chg": "",
  "occurs1_c_chg_sign": "",
  "occurs1_c_theo_pric": "",
  "occurs1_c_gamma": "",
  "occurs1_c_rho": "",
  "occurs1_p_open_pric": "",
  "occurs1_c_ask_pric": "",
  "occurs1_p_sym_nm": "",
  "fut_sign": "",
  "occurs1_c_opint": "",
  "spt_pric": "",
  "occurs1_c_dev_rt": "",
  "occurs1_c_low_pric": "",
  "occurs1_c_high_pric": "",
  "chg_sign": "",
  "occurs1_c_bid_pric": "",
  "occurs1_c_vol": "",
  "spt_cd": "",
  "occurs1_c_theta": "",
  "occurs1_p_theta": "",
  "und_nm": "",
  "occurs1_p_chg": "",
  "occurs1_p_dev": "",
  "fut_sym": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_price-all-option`
- 원본 범위: `A1:O95`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K19 |
| OUTPUT | A21:J89 |
| Request JSON (Input) | A91:A92 |
| Response JSON (Output) | A94:A95 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
