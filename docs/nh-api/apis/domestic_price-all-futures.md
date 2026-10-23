# 국내_선물전체시세

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/price-all-futures |
| API 통신 방식 | HTTP |
| API 명 | 국내_선물전체시세 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/price-all-futures |
| API 요청 제한 | 시세 LIMIT |

## 설명

```text
선물전체시세	SDIF7023Q01	주간만 서비스 중

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `prd` | 품목코드 | `char` | 2 | 일반 | 0 |  | 01:KOSPI<br>05:MKOSPI<br>06:KOSDAQ<br>AG:KOSDAQGLOBAL<br>08:KRX300<br>04:VKOSPI<br>75:USD<br>77:EUR<br>76:JPY<br>78:CNH<br>65:KTB<br>67:10KTB<br>66:5KTB<br>70:30KTB<br>A3:K200경기소비재<br>A2:K200금융<br>A0:K200에너지<br>A1:K200정보기술<br>AC:BBIG<br>AD:2차전지TOP10<br>AE:바이오TOP10<br>AL:KRX반도체지수 | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nrec` | 요청응답건수 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}], 조회 조건에 해당하는 선물 종목별 시세가 배열 형태로 반환됨 | 없음 |
| Occurs1 | `occurs1_prd` | 품목코드 | `char` | 2 | 일반 | 0 |  | 01:KOSPI<br>05:MKOSPI<br>06:KOSDAQ<br>AG:KOSDAQGLOBAL<br>08:KRX300<br>04:VKOSPI<br>75:USD<br>77:EUR<br>76:JPY<br>78:CNH<br>65:KTB<br>67:10KTB<br>66:5KTB<br>70:30KTB<br>A3:K200경기소비재<br>A2:K200금융<br>A0:K200에너지<br>A1:K200정보기술<br>AC:BBIG<br>AD:2차전지TOP10<br>AE:바이오TOP10<br>AL:KRX반도체지수 | 없음 |
| Occurs1 | `occurs1_sym_exch` | 종목코드 | `char` | 32 | 일반 | 0 |  | 거래소 코드 | 없음 |
| Occurs1 | `occurs1_sym_nm` | 종목명 | `char` | 30 | 일반 | 0 |  | 국문 종목명 | 없음 |
| Occurs1 | `occurs1_exp_mon` | 만기년월 | `char` | 5 | 일반 | 0 |  | YYYYMM | 없음 |
| Occurs1 | `occurs1_chg_sign` | 전일대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
| Occurs1 | `occurs1_last_pric` | 현재가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_chg` | 전일대비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_rt` | 등락률 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_theo_pric` | 이론가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_theo_bas` | 이론베이시스 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fact_bas` | 실제베이시스 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_dev` | 괴리도 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_dev_rt` | 괴리율 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ask_pric` | 매도호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_bid_pric` | 매수호가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_open_pric` | 시가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_high_pric` | 고가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_low_pric` | 저가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opint` | 미결제약정 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_qty` | 거래량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pd_close_pric` | 전일종가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pd_trd_qty` | 전일거래량 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_high_pric_dt` | 최고가일 | `char` | 8 | 일반 | 1 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_up` | 최고가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_low_pric_dt` | 최저가일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_lo` | 최저가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_lst_trd_dt` | 최종거래일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_ask_qty` | 매도호가잔량 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_bid_qty` | 매수호가잔량 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_spt_cd` | 현물 대상물코드 | `char` | 2 | 일반 | 0 |  | ex) A0169000:01, A7569000:75 | 없음 |
| Occurs1 | `occurs1_spt_sym` | 현물대상 종목코드 | `char` | 32 | 일반 | 0 |  | ex) A0169000:KRD020020016, A7569000:USD | 없음 |
| Occurs1 | `occurs1_spt_pric` | 현물가 | `char` | 16 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "prd": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_exp_mon": "",
  "occurs1_high_pric": "",
  "occurs1_last_pric": "",
  "occurs1_high_pric_dt": "",
  "occurs1_rt": "",
  "occurs1_lo": "",
  "occurs1_sym_exch": "",
  "Occurs1": "",
  "nrec": "",
  "occurs1_chg_sign": "",
  "occurs1_spt_cd": "",
  "occurs1_spt_sym": "",
  "occurs1_opint": "",
  "occurs1_low_pric_dt": "",
  "occurs1_pd_close_pric": "",
  "occurs1_up": "",
  "occurs1_open_pric": "",
  "occurs1_low_pric": "",
  "occurs1_trd_qty": "",
  "occurs1_ask_pric": "",
  "occurs1_fact_bas": "",
  "occurs1_lst_trd_dt": "",
  "occurs1_sym_nm": "",
  "occurs1_pd_trd_qty": "",
  "occurs1_bid_pric": "",
  "occurs1_dev": "",
  "occurs1_dev_rt": "",
  "occurs1_theo_bas": "",
  "occurs1_theo_pric": "",
  "occurs1_ask_qty": "",
  "occurs1_spt_pric": "",
  "occurs1_prd": "",
  "occurs1_chg": "",
  "occurs1_bid_qty": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_price-all-futures`
- 원본 범위: `A1:O60`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K17 |
| OUTPUT | A19:J54 |
| Request JSON (Input) | A56:A57 |
| Response JSON (Output) | A59:A60 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
