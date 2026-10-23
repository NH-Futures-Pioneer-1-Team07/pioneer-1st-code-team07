# 해외_주문내역

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/order-history |
| API 통신 방식 | HTTP |
| API 명 | 해외_주문내역 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/order-history |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
해외 주문/체결/미체결내역	SGBS9001Q01	

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |
|  | `inq_div` | 조회구분 | `char` | 1 | 일반 | 0 |  | 0.전체 1.주문 2.체결 3.미체결 4.미체결(지정청산) | Y |  |
|  | `prd_cd` | 품목코드 | `char` | 10 | 일반 | 0 |  | 널 허용 | N |  |
|  | `trd_div_cd` | 매수매도구분코드 | `char` | 1 | 일반 | 0 |  | 0.전체 1.매수 2.매도 | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_ac_no` | 계좌번호 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_dt` | 주문일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_ord_no` | 주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_org_ord_dt` | 원주문일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fut_opt_tp` | 선물옵션구분 | `char` | 1 | 일반 | 0 |  | 1:선물, 2:옵션 3:스프레드 | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_sts` | 주문상태 | `char` | 1 | 일반 | 0 |  | 1:접수, 3:확인, 4:부분체결, 6:전체체결, 8:자동취소, 9:거부 | 없음 |
| Occurs1 | `occurs1_trd_tp` | 매수매도구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | 없음 |
| Occurs1 | `occurs1_qt_tp` | 주문구분 | `char` | 1 | 일반 | 0 |  | 1:신규, 2:정정, 3:취소 | 없음 |
| Occurs1 | `occurs1_ord_tp` | 주문유형 | `char` | 1 | 일반 | 0 |  | 1:시장가, 2:지정가, 3:STOP-M, 4:STOP-L | 없음 |
| Occurs1 | `occurs1_ord_div` | 주문구분 | `char` | 1 | 일반 | 0 |  | 0:DAY, 1:GTC, 6:GTD | 없음 |
| Occurs1 | `occurs1_ord_qty` | 주문수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_qty` | 체결수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_mod_qty` | 정정수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cxl_qty` | 취소수량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_pric` | 주문가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_pric` | 체결가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_avg_pric` | 주문평균가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_tpf_pric` | 익절가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sl_pric` | 손절가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pric_diff_tick` | 가격변동틱 | `char` | 5 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_rcv_tm` | 주문접수시간 | `char` | 14 | 일반 | 0 |  | YYYYMMDDHHMMSS | 없음 |
| Occurs1 | `occurs1_exec_tm` | 체결시각 | `char` | 14 | 일반 | 0 |  | YYYYMMDDHHMMSS | 없음 |
| Occurs1 | `occurs1_user_id` | 작업사원 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_grp_ord_no` | 일괄주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_str_div` | 전략구분 | `char` | 6 | 일반 | 0 |  | 1:일반주문<br>2:STOP주문<br>3:SCALE주문<br>4:반복주문<br>5:복수계좌주문<br>6:OCO주문<br>7:예약주문<br>9:OCO STOP<br>a:시장조성주문<br>b:합성주문<br>c:합성전략<br>d:반대매매<br>g:협의대량<br>h:주문취소시체크함<br>i:반대매매강제취소<br>m:야간시장<br>n:협의매매 | 없음 |
| Occurs1 | `occurs1_med_div` | 주문매체 | `char` | 1 | 일반 | 0 |  | A:API, R:RESTApi, B:Back, D:DMA, F:FRONT, H:HTS, M:MTS, I:WTS, Y:YES, X:Expert, Z:FIX | 없음 |
| Occurs1 | `occurs1_err_cd` | 오류코드 | `char` | 5 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_rejt_rsn` | 거부사유 | `char` | 200 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_no` | 체결번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_per_exec_qty` | 건별체결량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_hdg_tp` | 헤지구분 | `char` | 1 | 일반 | 0 |  | 0:넷, 1:헤지 | 없음 |
| Occurs1 | `occurs1_stop_pric` | STOP가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opt_strk_bkg_yn` | 행사예약여부 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_ed_dt` | 주문종료일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
| Occurs1 | `occurs1_opt_ord_amt` | 옵션주문금액 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_rem_qty` | 주문잔량 | `char` | 7 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ref_ord_no` | 참조주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cls_pstn_no` | 청산포지션번호 | `char` | 18 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_mo_ord_no` | 모주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fcm_ord_rcv_tm` | FCM주문접수시간 | `char` | 14 | 일반 | 0 |  | YYYYMMDDHHMMSS | 없음 |
| Occurs1 | `occurs1_fcm_exec_rcv_tm` | FCM체결수신시간 | `char` | 14 | 일반 | 0 |  | YYYYMMDDHHMMSS | 없음 |
| Occurs1 | `occurs1_user_proc_item` | 사용자처리항목 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_err_msg` | 오류메세지 | `char` | 200 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ip_addr` | 주문IP(사설) | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_tpf_ord_tp_cd` | 익절주문유형코드 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_tpf_ord_pric` | 익절주문가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sl_ord_tp_cd` | 손절주문유형코드 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sl_ord_pric` | 손절주문가격 | `char` | 15 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ptt_proc_no` | 분할처리번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "trd_div_cd": "",
  "inq_div": "",
  "nxt_key": "",
  "prd_cd": ""
}
```

## Response JSON (Output)

```json
{
  "occurs1_sym": "",
  "occurs1_per_exec_qty": null,
  "occurs1_ord_tp": "",
  "occurs1_sl_ord_tp_cd": "",
  "occurs1_ord_pric": "",
  "occurs1_ord_rcv_tm": "",
  "occurs1_err_cd": "",
  "occurs1_hdg_tp": "",
  "occurs1_exec_pric": "",
  "occurs1_tpf_ord_pric": "",
  "occurs1_mod_qty": "",
  "occurs1_user_id": "",
  "occurs1_exec_tm": "",
  "occurs1_tpf_pric": "",
  "occurs1_mo_ord_no": "",
  "occurs1_ord_div": "",
  "occurs1_ptt_proc_no": "",
  "occurs1_org_ord_no": "",
  "occurs1_cur_cd": "",
  "occurs1_grp_ord_no": "",
  "occurs1_med_div": "",
  "occurs1_fut_opt_tp": "",
  "occurs1_ref_ord_no": "",
  "occurs1_user_proc_item": "",
  "nxt_key": "",
  "occurs1_opt_strk_bkg_yn": "",
  "Occurs1": "",
  "occurs1_opt_ord_amt": "",
  "occurs1_ord_rem_qty": "",
  "occurs1_ord_avg_pric": "",
  "nrec": "",
  "occurs1_ac_no": "",
  "occurs1_ord_sts": "",
  "occurs1_stop_pric": "",
  "occurs1_exec_qty": "",
  "occurs1_str_div": "",
  "occurs1_ord_no": "",
  "occurs1_exec_no": "",
  "occurs1_err_msg": "",
  "occurs1_tpf_ord_tp_cd": "",
  "occurs1_qt_tp": "",
  "occurs1_ip_addr": "",
  "occurs1_org_ord_dt": "",
  "occurs1_sl_pric": "",
  "occurs1_ord_dt": "",
  "occurs1_ord_ed_dt": "",
  "occurs1_ord_qty": "",
  "occurs1_fcm_exec_rcv_tm": "",
  "occurs1_cxl_qty": "",
  "occurs1_rejt_rsn": "",
  "occurs1_trd_tp": "",
  "occurs1_cls_pstn_no": null,
  "occurs1_fcm_ord_rcv_tm": "",
  "occurs1_sl_ord_pric": "",
  "occurs1_pric_diff_tick": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_order-history`
- 원본 범위: `A1:O84`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K20 |
| OUTPUT | A22:J78 |
| Request JSON (Input) | A80:A81 |
| Response JSON (Output) | A83:A84 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
