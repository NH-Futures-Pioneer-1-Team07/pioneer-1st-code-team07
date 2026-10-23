# 국내_종목예상체결가

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/price-expect-fill |
| API 통신 방식 | HTTP |
| API 명 | 국내_종목예상체결가 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/price-expect-fill |
| API 요청 제한 | 시세 LIMIT |

## 설명

```text
종목별 예상 체결가	SDIF7021Q06	주간/야간 동일하게 사용,  (* 야간 모의 환경 미지원)
장 시작 전 동시호가 등 예상체결 구간에서 형성되는 예상체결가격과 예상체결수량을 조회합니다.
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `sym_exch` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
|  | `sym_nm` | 종목명 | `char` | 30 | 일반 | 0 |  |  | 없음 |
|  | `ref_pric` | 전일종가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 5 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_tm` | 시간 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_est_exec_pric` | 예상체결가 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_chg_sign` | 전일대비부호 | `char` | 1 | 일반 | 0 |  | +:상승, 공백:보합, -:하락 | 없음 |
| Occurs1 | `occurs1_chg` | 전일대비 | `char` | 16 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_est_exec_qty` | 예상체결수량 | `char` | 9 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "sym": null
}
```

## Response JSON (Output)

```json
{
  "ref_pric": "",
  "nrec": "",
  "sym_exch": "",
  "occurs1_chg_sign": "",
  "occurs1_est_exec_qty": "",
  "Occurs1": "",
  "sym_nm": "",
  "occurs1_chg": "",
  "occurs1_tm": "",
  "occurs1_est_exec_pric": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_price-expect-fill`
- 원본 범위: `A1:O36`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K17 |
| OUTPUT | A19:J30 |
| Request JSON (Input) | A32:A33 |
| Response JSON (Output) | A35:A36 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
