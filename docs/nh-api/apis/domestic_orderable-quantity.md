# 국내_주문가능수량

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/orderable-quantity |
| API 통신 방식 | HTTP |
| API 명 | 국내_주문가능수량 |
| HTTP Method | POST |
| Content-Type |  |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/orderable-quantity |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
주문가능수량	SDBS1261Q01	 구분자로 주간/야간 구분 (법인 구분 따로 있음)  (* 야간 모의 환경 미지원)

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `ord_sts` | 처리구분 | `char` | 1 | 일반 | 0 |  | 1:주간_일반<br>2:주간_법인<br>3:야간_일반<br>4:야간_법인 | Y |  |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | Y |  |
|  | `trd_div` | 매매구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | Y |  |
|  | `ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  |  | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `ord_psb_qty` | 주문가능수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `cls_psb_qty` | 청산가능수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `tot_psb_qty` | 총가능수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_amt` | 주문가능금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "trd_div": "",
  "sym": "",
  "ord_pric": "",
  "ord_sts": ""
}
```

## Response JSON (Output)

```json
{
  "cls_psb_qty": "",
  "tot_psb_qty": "",
  "ord_psb_qty": "",
  "ord_psb_amt": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_orderable-quantity`
- 원본 범위: `A1:O33`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K20 |
| OUTPUT | A22:J27 |
| Request JSON (Input) | A29:A30 |
| Response JSON (Output) | A32:A33 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
