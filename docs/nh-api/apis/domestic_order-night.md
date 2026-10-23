# 국내_신규주문(야간)

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/order-night |
| API 통신 방식 | HTTP |
| API 명 | 국내_신규주문(야간) |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/order-night |
| API 요청 제한 | 주문 LIMIT |

## 설명

```text
신규주문 (야간)	SDBS1234U01	 (* 모의 환경 미지원)

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | Y |  |
|  | `trd_div` | 매매구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | Y |  |
|  | `ord_tp_cd` | 주문유형코드 | `char` | 1 | 일반 | 0 |  | 1:지정가, 2:시장가, 3:조건부, 4:최유리 | Y |  |
|  | `ord_qty` | 주문수량 | `char` | 24 | 일반 | 0 |  |  | Y |  |
|  | `ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  |  | Y |  |
|  | `exec_cnd_cd` | 체결조건구분코드 | `char` | 1 | 일반 | 0 |  | 1:FAS, 2:FOK, 3:FAK | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `ord_no` | 주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `msg_cd` | 메세지코드 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `msg_cntn` | 메세지내용 | `char` | 100 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "trd_div": "",
  "ord_tp_cd": "",
  "ord_qty": "",
  "sym": "",
  "ord_pric": "",
  "exec_cnd_cd": ""
}
```

## Response JSON (Output)

```json
{
  "ord_no": "",
  "msg_cd": "",
  "msg_cntn": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_order-night`
- 원본 범위: `A1:O34`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K22 |
| OUTPUT | A24:J28 |
| Request JSON (Input) | A30:A31 |
| Response JSON (Output) | A33:A34 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
