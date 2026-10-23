# 해외_예수금조회

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | overseas/deposit |
| API 통신 방식 | HTTP |
| API 명 | 해외_예수금조회 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/overseas/deposit |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
해외 예수금 조회  SGBS3205Q01

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `biz_dt` | 영업일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | N |  |
|  | `cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  | 통화 코드 | Y |  |
|  | `cvs_div` | 환산구분 | `char` | 1 | 일반 | 0 |  | 1:개별, 2:환산 | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `biz_dt` | 영업일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | 없음 |
|  | `ac_no` | 계좌번호 | `char` | 12 | 일반 | 0 |  |  | 없음 |
|  | `cur_cd` | 통화코드 | `char` | 3 | 일반 | 0 |  | 통화 코드 | 없음 |
|  | `strt_dps_tot_amt` | 개시예탁총금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `strt_dps_sbst_amt` | 개시예탁대용금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `strt_dps_csh_amt` | 개시예탁현금금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `strt_dps_fcur_blc_amt` | 개시예탁외화잔고금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `dps_tot_amt` | 예탁총액금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `dps_sbst_amt` | 대용평가금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `dps_fcur_amt` | 예탁외화금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `dps_csh_amt` | 예탁현금금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `td_rnd_amt` | 당일입출금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `rnd_amt` | 입출금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `td_csh_dps_amt` | 당일현금입금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `td_csh_wdw_amt` | 당일현금출금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `td_ck_dps_amt` | 당일수표입금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `td_ck_wdw_amt` | 당일수표출금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `etc_rnd_amt` | 기타입출금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `pv_typ_amt` | 기타입금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `etc_out_amt` | 기타출금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `ftr_drw_pla_amt` | 이체출금예정금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `cls_pl_amt` | 실현손익 또는선물청산손익 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fut_cls_pl_amt` | 장중선물순손실상당액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fut_tp_opt_opint_cls_amt` | 선물형옵션청산손익금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_trd_amt` | 옵션매매금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_buy_amt` | 옵션매수대금금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_sel_amt` | 옵션매도대금금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `urv_amt` | 미수금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fee` | 위탁수수료 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fut_fee` | 선물수수료 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_fee` | 옵션수수료 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `etc_fee` | 기타수수료 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `nxd_stl_pla_amt` | 익일결제예정금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `nxd_dpg_csh_amt` | 익일예탁현금금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `pl_amt` | 평가손익금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fut_opint_pl_amt` | 선물평가손익 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fut_tp_opt_opint_pl_amt` | 선물형옵션시장가치 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `dps_aset_amt` | 예탁자산평가금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_mkt_val_amt` | 옵션시장가치금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_buy_mkt_val_amt` | 옵션매수시장가치금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_sel_mkt_val_amt` | 옵션매도시장가치금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `tot_acc_aset_wth_amt` | 총계정자산가치금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `mgg_incd_tot_acc_aset_wth_amt` | 담보포함총계정자산가치금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `aff_mrgn_amt` | 사후증거금금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `adt_mrgn` | 추가증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `init_mrgn` | 위탁증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `ord_mrgn` | 주문증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fut_ord_mrgn` | 선물주문증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `opt_ord_mrgn` | 옵션주문증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `pstn_mrgn` | 포지션증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `mtn_mrgn` | 유지증거금 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_amt` | 주문가능금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `wdw_psb_amt` | 인출가능금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `fx_psb_amt` | 환전가능금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |
|  | `cur_fgr_cnt` | 통화자리수 | `char` | 4 | 일반 | 0 |  |  | 없음 |
|  | `ref_exrt` | 기준환율 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `rsk_rt` | 위험비율 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_pl_amt` | 옵션평가손익금액 | `char` | 24 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "cvs_div": "",
  "cur_cd": "",
  "biz_dt": ""
}
```

## Response JSON (Output)

```json
{
  "cur_fgr_cnt": "",
  "fut_cls_pl_amt": "",
  "pstn_mrgn": "",
  "biz_dt": "",
  "fee": "",
  "aff_mrgn_amt": "",
  "td_ck_dps_amt": "",
  "strt_dps_sbst_amt": "",
  "opt_ord_mrgn": "",
  "opt_sel_amt": "",
  "td_rnd_amt": "",
  "dps_tot_amt": "",
  "cls_pl_amt": "",
  "nxd_stl_pla_amt": "",
  "fut_opint_pl_amt": "",
  "tot_acc_aset_wth_amt": "",
  "opt_mkt_val_amt": "",
  "nxd_dpg_csh_amt": "",
  "td_csh_dps_amt": "",
  "mtn_mrgn": "",
  "wdw_psb_amt": "",
  "fx_psb_amt": "",
  "pl_amt": "",
  "init_mrgn": "",
  "pv_typ_amt": "",
  "adt_mrgn": "",
  "strt_dps_tot_amt": "",
  "etc_fee": "",
  "dps_sbst_amt": "",
  "td_ck_wdw_amt": "",
  "fut_fee": "",
  "strt_dps_csh_amt": "",
  "etc_out_amt": "",
  "dps_aset_amt": "",
  "opt_trd_amt": "",
  "dps_fcur_amt": "",
  "ord_mrgn": "",
  "fut_ord_mrgn": "",
  "cur_cd": "",
  "fut_tp_opt_opint_pl_amt": "",
  "opt_buy_mkt_val_amt": "",
  "strt_dps_fcur_blc_amt": "",
  "dps_csh_amt": "",
  "rnd_amt": "",
  "rsk_rt": "",
  "ord_psb_amt": "",
  "ftr_drw_pla_amt": "",
  "opt_sel_mkt_val_amt": "",
  "fut_tp_opt_opint_cls_amt": "",
  "urv_amt": "",
  "opt_pl_amt": "",
  "td_csh_wdw_amt": "",
  "ref_exrt": "",
  "etc_rnd_amt": "",
  "ac_no": "",
  "opt_fee": "",
  "mgg_incd_tot_acc_aset_wth_amt": "",
  "opt_buy_amt": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `overseas_deposit`
- 원본 범위: `A1:O86`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K19 |
| OUTPUT | A21:J80 |
| Request JSON (Input) | A82:A83 |
| Response JSON (Output) | A85:A86 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
