# 해외_주문가능수량

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/orderable-quantity |
| API 통신 방식 | HTTP |
| API 명 | 해외_주문가능수량 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/orderable-quantity |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
해외 주문가능수량	SGBS3500Q07	

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  | 필수입력 | Y |  |
|  | `glb_ord_tp_cd` | 해외주문유형코드 | `char` | 1 | 일반 | 0 |  | 1.시장가 2.지정가 3.STOP-M 4.STOP-L | Y |  |
|  | `ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  | 필수입력 | Y |  |
|  | `stop_pric` | 스탑가격 | `char` | 24 | 일반 | 0 |  | 해외주문유형이 STOP 주문의 유형일때 필수 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `prd_cd` | 품목코드 | `char` | 10 | 일반 | 0 |  |  | 없음 |
|  | `cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_amt` | 주문가능금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `new_buy_ord_psb_qty` | 신규매수주문가능수량 | `char` | 24 | 일반 | 0 |  | 매수주문 가능수량 | 없음 |
|  | `buy_cls_psb_qty` | 매수청산가능수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `buy_ord_psb_qty` | 매수주문가능수량 | `char` | 24 | 일반 | 0 |  | 신규매수가능과 청산가능 수량의 합 | 없음 |
|  | `new_sel_ord_psb_qty` | 신규매도주문가능수량 | `char` | 24 | 일반 | 0 |  | 매도주문 가능수량 | 없음 |
|  | `sel_cls_psb_qty` | 매도청산가능수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `sel_ord_psb_qty` | 매도주문가능수량 | `char` | 24 | 일반 | 0 |  | 신규매도가능과 청산가능 수량의 합 | 없음 |

## Request JSON (Input)

```json
{
  "stop_pric": "",
  "sym": "",
  "ord_pric": "",
  "glb_ord_tp_cd": ""
}
```

## Response JSON (Output)

```json
{
  "buy_cls_psb_qty": "",
  "new_buy_ord_psb_qty": "",
  "cur_cd": "",
  "sel_ord_psb_qty": "",
  "new_sel_ord_psb_qty": "",
  "buy_ord_psb_qty": "",
  "prd_cd": "",
  "ord_psb_amt": "",
  "sel_cls_psb_qty": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_orderable-quantity`
- 원본 범위: `A1:O38`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K20 |
| OUTPUT | A22:J32 |
| Request JSON (Input) | A34:A35 |
| Response JSON (Output) | A37:A38 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
