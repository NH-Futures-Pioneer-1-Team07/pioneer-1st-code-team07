# 해외_주문오류내역

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/order-error |
| API 통신 방식 | HTTP |
| API 명 | 해외_주문오류내역 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/order-error |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
해외 주문오류내역	SGBS3534Q01	

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |
|  | `inq_dt` | 조회일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_inq_dt` | 주문일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_seq_no` | 일련번호 | `char` | 11 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_inp_tm` | 주문시간 | `char` | 8 | 일반 | 0 |  | HHMMSS | 없음 |
| Occurs1 | `occurs1_ord_no` | 주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_glb_ord_div_cd_nm` | 해외주문구분코드명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_qt_div_cd_nm` | 주문구분코드명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_trd_div_nm` | 매수매도구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_glb_ord_tp_cd_nm` | 해외주문유형코드명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_pric` | 주문가격 | `char` | 100 | 일반 | 0 |  | 주문가격 | 없음 |
| Occurs1 | `occurs1_ord_qty` | 주문수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_stop_pric` | 스탑주문가격 | `char` | 100 | 일반 | 0 |  | STOP가격 | 없음 |
| Occurs1 | `occurs1_msg_cd` | 메세지코드 | `char` | 5 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_err_msg` | 에러메세지 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ip_addr` | IP주소 | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fst_ord_id` | 최초주문ID | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_mltple_grp_no` | 복수그룹번호 | `char` | 11 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pric_ind` | 진법구분 | `char` | 1 | 일반 | 0 |  | 진법구분<br>1:정수<br>2~9:소수점 자리수 (-1)<br>A:1/2진법<br>B:1/4진법<br>C:1/8진법<br>D:1/16진법<br>E:1/32진법<br>F:1/64진법<br>G:1/128진법<br>H:1/256진법<br>I:0.5/32진법<br>J:0.5/64진법<br>K:0.25/32진법<br>L:0.125/32진법<br>M:0.065/32진법 | 없음 |
| Occurs1 | `occurs1_cme_yn` | CME여부 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_dom_dt` | 국내일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_dom_tm` | 국내시간 | `char` | 6 | 일반 | 0 |  | HHMMSS | 없음 |
| Occurs1 | `occurs1_ord_med_div_cd_nm` | 주문매체구분코드명 | `char` | 10 | 일반 | 0 |  | 주문 매체 구분명<br>(API, REST API ...) | 없음 |

## Request JSON (Input)

```json
{
  "nxt_key": "",
  "inq_dt": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_sym": "",
  "occurs1_ord_pric": "",
  "occurs1_cme_yn": "",
  "nxt_key": "",
  "Occurs1": "",
  "nrec": "",
  "occurs1_trd_div_nm": "",
  "occurs1_dom_tm": "",
  "occurs1_stop_pric": "",
  "occurs1_ord_med_div_cd_nm": "",
  "occurs1_inp_tm": "",
  "occurs1_ord_no": "",
  "occurs1_qt_div_cd_nm": "",
  "occurs1_err_msg": "",
  "occurs1_inq_dt": "",
  "occurs1_ip_addr": "",
  "occurs1_mltple_grp_no": "",
  "occurs1_glb_ord_tp_cd_nm": "",
  "occurs1_ord_qty": "",
  "occurs1_pric_ind": "",
  "occurs1_org_ord_no": "",
  "occurs1_glb_ord_div_cd_nm": "",
  "occurs1_msg_cd": "",
  "occurs1_dom_dt": "",
  "occurs1_seq_no": "",
  "occurs1_fst_ord_id": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_order-error`
- 원본 범위: `A1:O53`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K18 |
| OUTPUT | A20:J47 |
| Request JSON (Input) | A49:A50 |
| Response JSON (Output) | A52:A53 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
