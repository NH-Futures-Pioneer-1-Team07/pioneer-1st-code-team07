# 국내_품목별세부정보

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/product-detail |
| API 통신 방식 | HTTP |
| API 명 | 국내_품목별세부정보 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/product-detail |
| API 요청 제한 | 계좌 LIMIT |

## 설명

품목별 세부정보	SDBS9003Q01	 주간/야간 데이터 한번에 조회  (* 야간 모의 환경 미지원)

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_dtl_cd_ko_nm` | 품목명 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cd_val_inf_1` | 틱 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_tick_val` | 틱가치 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_mltplr` | 거래승수 | `char` | 22 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cd_val_inf_4` | 거래시간 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cd_val_inf_2` | 단일가격 경쟁거래(개장시) | `char` | 50 | 일반 | 0 |  | 개장시 | 없음 |
| Occurs1 | `occurs1_cd_val_inf_3` | 단일가격 경쟁거래(거래종료시) | `char` | 50 | 일반 | 0 |  | 거래 종료시 | 없음 |
| Occurs1 | `occurs1_cd_val_inf_5` | 최종거래일 거래시간 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sett_nm` | 결제방법명 | `char` | 50 | 일반 | 0 |  | 결제방법명 (현금결제, 실물인수도) | 없음 |
| Occurs1 | `occurs1_exp_dt` | 최근월물 만기일 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_init_mrgn` | 개시증거금 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_mtn_mrgn` | 유지증거금 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ctr_init_mrgn` | 계약당개시증거금액 | `char` | 100 | 일반 | 0 |  | 계약당 개시증거금액 (단위:원) | 없음 |

## Request JSON (Input)

```json
{}
```

## Response JSON (Output)

```json
{
  "occurs1_mltplr": "",
  "occurs1_cd_val_inf_5": "",
  "occurs1_dtl_cd_ko_nm": "",
  "Occurs1": "",
  "nrec": "",
  "occurs1_init_mrgn": "",
  "occurs1_exp_dt": "",
  "occurs1_sett_nm": "",
  "occurs1_tick_val": "",
  "occurs1_cd_val_inf_1": "",
  "occurs1_cd_val_inf_2": "",
  "occurs1_cd_val_inf_3": "",
  "occurs1_cd_val_inf_4": "",
  "occurs1_mtn_mrgn": "",
  "occurs1_ctr_init_mrgn": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_product-detail`
- 원본 범위: `A1:O40`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K15 |
| OUTPUT | A18:J34 |
| Request JSON (Input) | A36:A37 |
| Response JSON (Output) | A39:A40 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
