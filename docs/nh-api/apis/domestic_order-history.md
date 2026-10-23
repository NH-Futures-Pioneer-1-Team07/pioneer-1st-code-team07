# 국내_주문내역

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/order-history |
| API 통신 방식 | HTTP |
| API 명 | 국내_주문내역 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/order-history |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
주문/체결/미체결내역 	SDBS3066Q01  구분자로 주간/야간 구분  (* 야간 모의 환경 미지원)

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `trd_div` | 매매구분 | `char` | 1 | 일반 | 0 |  | 0:전체, 1:매수, 2:매도 | Y |  |
|  | `exec_div` | 체결구분 | `char` | 1 | 일반 | 0 |  | 0:전체, 1:체결, 2:미체결, 3:미접수 | Y |  |
|  | `trd_tm_div_cd` | 거래시간구분코드 | `char` | 1 | 일반 | 0 | 0 | 0:전체, 1:주간, 2.야간 | Y |  |
|  | `ord_div_cd` | 주문구분코드 | `char` | 1 | 일반 | 0 | 0 | 0:전체, 1:거부, 2:오류 | Y |  |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본:공백<br>응답 데이터가 요청 건수를 초과하는 경우 다음 데이터를 조회하기 위해 응답에서 받은 값을 재요청에 사용 | N |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `nxt_key` | 다음데이터키 | `char` | 100 | 일반 | 0 |  | 기본 | 없음 |
|  | `nrec` | 요청응답건수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `Occurs1` | Occurs1 |  | 0 | Object | 1 |  | Array[{Object}] | 없음 |
| Occurs1 | `occurs1_trd_dt` | 거래일자 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ac_no` | 계좌번호 | `char` | 12 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ac_nm` | 위탁계좌명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_org_ord_no` | 원주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_no` | 주문번호 | `char` | 10 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym` | 종목코드 | `char` | 32 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_sym_nm` | 종목명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_und_sym` | 기초자산코드 | `char` | 2 | 일반 | 0 |  | 01:KOSPI<br>05:MKOSPI<br>06:KOSDAQ<br>AG:KOSDAQGLOBAL<br>08:KRX300<br>04:VKOSPI<br>75:USD<br>77:EUR<br>76:JPY<br>78:CNH<br>65:KTB<br>67:10KTB<br>66:5KTB<br>70:30KTB<br>A3:K200경기소비재<br>A2:K200금융<br>A0:K200에너지<br>A1:K200정보기술<br>AC:BBIG<br>AD:2차전지TOP10<br>AE:바이오TOP10<br>AL:KRX반도체지수 | 없음 |
| Occurs1 | `occurs1_exch_cd` | 거래소코드 | `char` | 10 | 일반 | 0 |  | 국내주야간구분<br>KRX:주간<br>KRX_NDV:야간 | 없음 |
| Occurs1 | `occurs1_trd_div` | 매매구분 | `char` | 1 | 일반 | 0 |  | 1:매수, 2:매도 | 없음 |
| Occurs1 | `occurs1_ord_sts` | 주문상태 | `char` | 1 | 일반 | 0 |  | 1:접수, 3:확인, 4:부분체결, 6:전체체결, 8:자동취소, 9:거부 | 없음 |
| Occurs1 | `occurs1_ord_sts_nm` | 처리상태명 | `char` | 50 | 일반 | 0 |  | 접수, 확인, 체결, 취소, 거부 | 없음 |
| Occurs1 | `occurs1_ord_qty` | 주문수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_pric` | 주문가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_qty` | 체결수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exec_pric` | 체결가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_rem_ord_qty` | 주문잔량수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_mod_qty` | 정정수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_cxl_qty` | 취소수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_div_cd` | 주문구분코드 | `char` | 1 | 일반 | 0 |  | 1:신규, 2:정정, 3:취소 | 없음 |
| Occurs1 | `occurs1_ord_div_nm` | 주문구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_fut_opt_div_cd` | 상품구분코드 | `char` | 1 | 일반 | 0 |  | 1:선물<br>2:콜옵션<br>3:풋옵션<br>4:스프레드 | 없음 |
| Occurs1 | `occurs1_exec_cnd_cd` | 체결조건코드 | `char` | 1 | 일반 | 0 |  | 1:FAS, 2:FOK, 3:FAK | 없음 |
| Occurs1 | `occurs1_exec_cnd_nm` | 체결조건명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pric_cnd_cd` | 가격조건코드 | `char` | 1 | 일반 | 0 |  | &#32;(미사용) | 없음 |
| Occurs1 | `occurs1_pric_cnd_nm` | 가격조건명 | `char` | 50 | 일반 | 0 |  | 지정가, 시장가, 조건부, 최유리,… | 없음 |
| Occurs1 | `occurs1_ord_form_cd` | 주문형태코드 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_form_nm` | 주문형태명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exch_rcv_tm` | 거래소접수시간 | `char` | 9 | 일반 | 0 |  | HHMMSS | 없음 |
| Occurs1 | `occurs1_exch_exec_tm` | 거래소체결시간 | `char` | 9 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_rejt_rsn_cd` | 거부코드 | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_rejt_rsn` | 주문거부사유 | `char` | 100 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_id` | 주문ID | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_user_ip_addr` | 사용자IP주소 | `char` | 20 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_med_div` | 매체구분코드 | `char` | 1 | 일반 | 0 |  | A:API<br>R:RESTApi<br>B:Back<br>D:DMA<br>F:FRONT<br>H:HTS<br>M:MTS<br>I:WTS<br>Y:YES<br>X:Expert<br>Z:FIX | 없음 |
| Occurs1 | `occurs1_org_ord_dt` | 원주문일자 | `char` | 8 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ord_vld_div_cd` | 주문유효구분코드 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_avg_exec_pric` | 평균체결가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pl_rez_pric` | 이익실현가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pl_lim_pric` | 손실제한가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_pric_var_tick_cnt` | 가격변동틱수 | `char` | 6 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_stg_div_cd` | 전략구분코드 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_exch_exec_no` | 거래소체결번호 | `char` | 26 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_hdg_tp` | 헤지구분코드 | `char` | 1 | 일반 | 0 |  | 0:일반, 1:헤지, 9:전체 | 없음 |
| Occurs1 | `occurs1_stop_pric` | 주문STOP가격 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opt_strk_bkg_yn` | 옵션행사가예약여부 | `char` | 1 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_opt_ord_amt` | 옵션주문금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_spd_proc_div_cd` | 스프레드처리구분코드 | `char` | 1 | 일반 | 0 |  | S:스프레드, G:나머지 | 없음 |
| Occurs1 | `occurs1_ord_src_tp` | 주문원천유형 | `char` | 2 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_per_exec_qty` | 건별체결수량 | `char` | 24 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_ptt_exec_cnt` | 분할체결건수 | `char` | 11 | 일반 | 0 |  |  | 없음 |
| Occurs1 | `occurs1_aut_cxl_tp_nm` | 자동취소유형명 | `char` | 50 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "trd_div": "",
  "ord_div_cd": "0",
  "exec_div": "",
  "nxt_key": "",
  "trd_tm_div_cd": "0"
}
```

## Response JSON (Output)

```json
{
  "occurs1_sym": "",
  "occurs1_per_exec_qty": "",
  "occurs1_pric_var_tick_cnt": "",
  "occurs1_ord_pric": "",
  "occurs1_aut_cxl_tp_nm": "",
  "occurs1_trd_div": "",
  "occurs1_rejt_rsn_cd": "",
  "occurs1_exch_exec_tm": "",
  "occurs1_ord_vld_div_cd": "",
  "occurs1_stg_div_cd": "",
  "occurs1_exec_cnd_cd": "",
  "occurs1_hdg_tp": "",
  "occurs1_avg_exec_pric": "",
  "occurs1_fut_opt_div_cd": "",
  "occurs1_exch_rcv_tm": "",
  "occurs1_ord_src_tp": "",
  "occurs1_exec_pric": "",
  "occurs1_mod_qty": "",
  "occurs1_spd_proc_div_cd": "",
  "occurs1_sym_nm": "",
  "occurs1_user_ip_addr": "",
  "occurs1_pric_cnd_nm": "",
  "occurs1_org_ord_no": "",
  "occurs1_med_div": "",
  "occurs1_ord_div_cd": "",
  "occurs1_ord_form_nm": "",
  "occurs1_pl_rez_pric": "",
  "occurs1_exch_exec_no": "",
  "nxt_key": "",
  "occurs1_exec_cnd_nm": "",
  "occurs1_opt_strk_bkg_yn": "",
  "occurs1_ptt_exec_cnt": "",
  "occurs1_ord_rejt_rsn": "",
  "Occurs1": "",
  "occurs1_opt_ord_amt": "",
  "occurs1_pl_lim_pric": "",
  "nrec": "",
  "occurs1_ac_no": "",
  "occurs1_ord_sts": "",
  "occurs1_pric_cnd_cd": "",
  "occurs1_stop_pric": "",
  "occurs1_exec_qty": "",
  "occurs1_ord_div_nm": "",
  "occurs1_ord_no": "",
  "occurs1_ac_nm": "",
  "occurs1_und_sym": "",
  "occurs1_org_ord_dt": "",
  "occurs1_ord_id": "",
  "occurs1_ord_form_cd": "",
  "occurs1_trd_dt": "",
  "occurs1_ord_qty": "",
  "occurs1_exch_cd": "",
  "occurs1_ord_sts_nm": "",
  "occurs1_rem_ord_qty": "",
  "occurs1_cxl_qty": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_order-history`
- 원본 범위: `A1:O85`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K21 |
| OUTPUT | A23:J79 |
| Request JSON (Input) | A81:A82 |
| Response JSON (Output) | A84:A85 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
