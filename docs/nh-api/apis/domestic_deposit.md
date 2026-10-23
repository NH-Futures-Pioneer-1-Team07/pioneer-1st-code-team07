# 국내_예수금조회

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/deposit |
| API 통신 방식 | HTTP |
| API 명 | 국내_예수금조회 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/deposit |
| API 요청 제한 | 계좌 LIMIT |

## 설명

```text
예수금 조회	SDBS5001Q01

```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `biz_dt` | 영업일자 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `strt_dps_tot_amt` | 개시예탁총금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `strt_dps_csh_amt` | 개시예탁현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `strt_dps_sbst_amt` | 개시예탁대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `strt_dps_fcur_blc_amt` | 개시예탁외화잔고금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `dps_aset_tot_amt` | 당일예탁자산금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `dps_csh_amt` | 예탁현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `dps_sbst_amt` | 대용평가금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `dps_fcur_amt` | 예탁외화금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_tot_amt` | 주문가능총금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_csh_amt` | 주문가능현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_sbst_amt` | 주문가능대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ord_psb_fcur_amt` | 주문가능외화금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `wdw_psb_tot_amt` | 인출가능총금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `wdw_psb_csh_amt` | 인출가능현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `wdw_psb_sbst_amt` | 인출가능대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `wdw_psb_fcur_amt` | 인출가능외화금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `init_mrgn_tot_amt` | 위탁증거금총액금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `init_mrgn_csh_amt` | 위탁증거금현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `init_mrgn_sbst_amt` | 위탁증거금대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `init_mrgn_fcur_amt` | 위탁증거금외화금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `mtn_mrgn_tam_amt` | 유지증거금총액금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `mtn_mrgn_csh_amt` | 유지증거금현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `mtn_mrgn_sbst_amt` | 유지증거금대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `mtn_mrgn_fcur_amt` | 유지증거금외화금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `adt_mrgn_tot_amt` | 추가증거금총금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `adt_mrgn_csh_amt` | 추가증거금현금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `adt_mrgn_sbst_amt` | 추가증거금대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `adt_mrgn_fcur_amt` | 추가증거금외화금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `adt_mrgn_ocu_div_nm` | 추가증거금발생구분명 | `char` | 50 | 일반 | 0 |  |  | 없음 |
|  | `nght_tot_amt` | 야간결제총액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `nght_sett_amt` | 야간정산차금 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `nght_fee` | 야간수수료 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `pl_tot_pric` | 손익총액금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `fut_rez_pl_amt` | 선물확정손익금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_rez_pl_amt` | 옵션확정손익금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `phd_dps_amt` | 실물인수예치금 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `paid_subs_amt` | 유상청약금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `emrg_init_mrgn` | 긴급 위탁증거금 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ck_amt` | 일반수표금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `etc_ck_amt` | 기타수표금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `sbst_sell_sett_pla_amt` | 대용매도결제예정금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ftr_drw_pla_amt` | 이체출금예정금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ftr_dlr_sbst_amt` | 이체출고대용금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `ftr_dlr_pla_amt` | 이체출고예정금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_pl_amt` | 옵션평가손익금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `nxd_stl_tot_amt` | 익일결제총금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `fut_sett_amt` | 선물정산차금 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_sett_amt` | 옵션결제대금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_buy_amt` | 옵션매수대금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_sel_amt` | 옵션매도대금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `phd_sett_pla_amt` | 인수도대금 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `fee` | 수수료 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `urv_tot_amt` | 미수총금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `urv_amt` | 미수금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `urv_ovd_amt` | 예상연체료 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `cls_amt` | 청산평가금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `dps_amt` | 입금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `pv_typ_amt` | 기타입금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `wdw_amt` | 출금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `etc_out_amt` | 기타출금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_strk_amt` | 옵션행사대금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `opt_alloc_amt` | 옵션배정대금금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `fut_cls_pl_amt` | 장중선물순손실상당액 | `char` | 22 | 일반 | 0 |  |  | 없음 |
|  | `dy_dps_aset_amt` | 일일예탁자산금액 | `char` | 22 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "biz_dt": ""
}
```

## Response JSON (Output)

```json
{
  "mtn_mrgn_sbst_amt": "",
  "fut_cls_pl_amt": "",
  "wdw_psb_sbst_amt": "",
  "fee": "",
  "pl_tot_pric": "",
  "strt_dps_sbst_amt": "",
  "dy_dps_aset_amt": "",
  "nght_sett_amt": "",
  "sbst_sell_sett_pla_amt": "",
  "urv_ovd_amt": "",
  "opt_sel_amt": "",
  "ord_psb_tot_amt": "",
  "adt_mrgn_csh_amt": "",
  "opt_rez_pl_amt": "",
  "phd_dps_amt": "",
  "nght_tot_amt": "",
  "nght_fee": "",
  "mtn_mrgn_fcur_amt": "",
  "ftr_dlr_pla_amt": "",
  "fut_sett_amt": "",
  "wdw_amt": "",
  "opt_alloc_amt": "",
  "mtn_mrgn_tam_amt": "",
  "mtn_mrgn_csh_amt": "",
  "pv_typ_amt": "",
  "opt_strk_amt": "",
  "strt_dps_tot_amt": "",
  "urv_tot_amt": "",
  "dps_sbst_amt": "",
  "strt_dps_csh_amt": "",
  "etc_out_amt": "",
  "dps_aset_tot_amt": "",
  "ord_psb_fcur_amt": "",
  "init_mrgn_sbst_amt": "",
  "dps_fcur_amt": "",
  "ord_psb_sbst_amt": "",
  "ftr_dlr_sbst_amt": "",
  "phd_sett_pla_amt": "",
  "strt_dps_fcur_blc_amt": "",
  "dps_csh_amt": "",
  "opt_sett_amt": "",
  "adt_mrgn_tot_amt": "",
  "fut_rez_pl_amt": "",
  "adt_mrgn_ocu_div_nm": "",
  "init_mrgn_fcur_amt": "",
  "ftr_drw_pla_amt": "",
  "ord_psb_csh_amt": "",
  "adt_mrgn_fcur_amt": "",
  "wdw_psb_tot_amt": "",
  "cls_amt": "",
  "paid_subs_amt": "",
  "opt_pl_amt": "",
  "urv_amt": "",
  "ck_amt": "",
  "wdw_psb_fcur_amt": "",
  "emrg_init_mrgn": "",
  "adt_mrgn_sbst_amt": "",
  "wdw_psb_csh_amt": "",
  "etc_ck_amt": "",
  "nxd_stl_tot_amt": "",
  "init_mrgn_tot_amt": "",
  "init_mrgn_csh_amt": "",
  "opt_buy_amt": "",
  "dps_amt": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_deposit`
- 원본 범위: `A1:O90`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K17 |
| OUTPUT | A19:J84 |
| Request JSON (Input) | A86:A87 |
| Response JSON (Output) | A89:A90 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
