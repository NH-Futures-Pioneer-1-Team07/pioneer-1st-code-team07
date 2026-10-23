# 해외_주문

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/order |
| API 통신 방식 | HTTP |
| API 명 | 해외_주문 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/order |
| API 요청 제한 | 주문 LIMIT |

## 설명

해외 주문/정정/취소 SGBS3500U03

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `qt_div_cd` | 호가구분코드 | `char` | 1 | 일반 | 0 |  | 1:주문신규, 2:정정, 3:취소 | Y |  |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  | 필수입력 | N |  |
|  | `trd_div_cd` | 매수매도구분코드 | `char` | 1 | 일반 | 0 |  | 1.매수 2.매도 | Y |  |
|  | `glb_ord_tp_cd` | 해외주문유형코드 | `char` | 1 | 일반 | 0 |  | 1.시장가 <br>2.지정가 <br>3.STOP-M <br>4.STOP-L | Y |  |
|  | `ord_qty` | 주문수량 | `char` | 24 | 일반 | 0 |  | 신규, 정정 필수입력 | Y |  |
|  | `ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  | glb_ord_tp_cd (해외주문유형코드)에 따라 입력<br>1(시장가) : 0<br>2(지정가) : 주문가격<br>3(STOP-M) : 0<br>4(STOP-L) : 주문가격 | N |  |
|  | `stop_pric` | 스탑가격 | `char` | 24 | 일반 | 0 |  | glb_ord_tp_cd (해외주문유형코드)에 따라 입력<br>1(시장가) : 공백<br>2(지정가) : 공백<br>3(STOP-M) : STOP가격<br>4(STOP-L) : STOP가격 | N |  |
|  | `org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 | 0 | 정정, 취소 필수입력 | Y | 0 |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `biz_dt` | 영업일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `mo_ord_no` | 모주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `ord_no` | 주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
|  | `ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `ord_qty` | 주문수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `qt_div_cd` | 호가구분코드 | `char` | 1 | 일반 | 0 |  | 1:주문신규, 2:정정, 3:취소 | 없음 |
|  | `trd_div_cd` | 매수매도구분코드 | `char` | 1 | 일반 | 0 |  | 1 -매수,  2 -매도 | 없음 |
|  | `err_cd` | 에러코드 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `err_msg` | 에러메세지 | `char` | 100 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "trd_div_cd": "",
  "stop_pric": "",
  "ord_qty": "",
  "org_ord_no": "0",
  "sym": "",
  "ord_pric": "",
  "qt_div_cd": "",
  "glb_ord_tp_cd": ""
}
```

## Response JSON (Output)

```json
{
  "ord_no": "",
  "trd_div_cd": "",
  "ord_qty": "",
  "org_ord_no": "",
  "sym": "",
  "ord_pric": "",
  "err_msg": "",
  "biz_dt": "",
  "mo_ord_no": "",
  "qt_div_cd": "",
  "err_cd": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_order`
- 원본 범위: `A1:O44`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K24 |
| OUTPUT | A26:J38 |
| Request JSON (Input) | A40:A41 |
| Response JSON (Output) | A43:A44 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
