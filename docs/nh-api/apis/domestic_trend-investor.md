# 국내_투자자직전매매동향

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | domestic/trend-investor |
| API 통신 방식 | HTTP |
| API 명 | 국내_투자자직전매매동향 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /trade/v1/domestic/trend-investor |
| API 요청 제한 | 시세 LIMIT |

## 설명

```text
투자자 직전 매매동향 (30초 지연)	SDIF7172Q01	(* 야간 미지원)
국내 선물 옵션 시장의 투자자별 매수/매도 및 순매수 동향을 조회합니다.
개인, 외국인, 증권∙선물, 보험, 투신, 은행, 연기금, 등의 투자자별 거래 동향을 수량 또는 금액 기준으로 제공합니다.
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `opt_prd` | 품목선물옵션코드 | `char` | 4 | 일반 | 0 |  | 거래소코드(2)+선물옵션구분(1)1:선물, 2:콜, 3:풋<br>예)거래소 선물 : 거래소코드(01) + 선물(1) =&gt; 011 | Y |  |
|  | `ref_dt` | 기준일 | `char` | 8 | 일반 | 0 |  | YYYYMMDD | Y |  |
|  | `inq_tp` | 투자자조회구분 | `char` | 1 | 일반 | 0 | 1 | 1:수량, 2:금액(기본:1) | N | 1 |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `tm` | 수신시간 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `ind_buy` | 개인매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ind_pre_buy` | 개인직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ind_buy_rt` | 개인매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `ind_sel` | 개인매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ind_pre_sel` | 개인직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ind_sel_rt` | 개인매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `ind_net_buy` | 개인순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `frgn_buy` | 외국인매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `frgn_pre_buy` | 외국인직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `frgn_buy_rt` | 외국인매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `frgn_sel` | 외국인매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `frgn_pre_sel` | 외국인직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `frgn_sel_rt` | 외국인매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `frgn_net_buy` | 외국인순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `scrt_buy` | 증권선물매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `scrt_pre_buy` | 증권선물직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `scrt_buy_rt` | 증권선물매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `scrt_sel` | 증권선물매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `scrt_pre_sel` | 증권선물직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `scrt_sel_rt` | 증권선물매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `scrt_net_buy` | 증권선물순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ins_buy` | 보험매수 | `char` | 18 | 일반 | 1 |  |  | 없음 |
|  | `ins_pre_buy` | 보험직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ins_buy_rt` | 보험매수대비율 | `char` | 6 | 일반 | 1 |  |  | 없음 |
|  | `ins_sel` | 보험매도 | `char` | 18 | 일반 | 1 |  |  | 없음 |
|  | `ins_pre_sel` | 보험직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `ins_sel_rt` | 모험매도대비율 | `char` | 6 | 일반 | 1 |  |  | 없음 |
|  | `ins_buy_net` | 보험순매수 | `char` | 18 | 일반 | 1 |  |  | 없음 |
|  | `invt_buy` | 투신매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `invt_pre_buy` | 투신직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `invt_buy_rt` | 투신매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `invt_sel` | 투신매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `invt_pre_sel` | 투신직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `invt_sel_rt` | 투신매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `invt_net_buy` | 투신순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `bank_buy` | 은행매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `bank_pre_buy` | 은행직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `bank_buy_rt` | 은행매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `bank_sel` | 은행매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `bank_pre_sel` | 은행직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `bank_sel_rt` | 은행매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `bank_net_buy` | 은행순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `mb_buy` | 종금매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `mb_pre_buy` | 종금직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `mb_buy_rt` | 종금매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `mb_sel` | 종금매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `mb_pre_sel` | 종금직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `mb_sel_rt` | 종금매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `mb_net_buy` | 종금순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_buy` | 연기금매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_pre_buy` | 연기금직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_buy_rt` | 연기금매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_sel` | 연기금매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_pre_sel` | 연기금직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_sel_rt` | 연기금매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `penfnd_net_buy` | 연기금순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `cntry_buy` | 국가기금공제매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `cntry_pre_buy` | 국가기금공제직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `cntry_buy_rt` | 국가기금공제매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `cntry_sel` | 국가기금공제매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `cntry_pre_sel` | 국가기금공제직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `cntry_sel_rt` | 국가공제매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `cntry_net_buy` | 국가공제순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `etc_buy` | 기타매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `etc_pre_buy` | 기타직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `etc_buy_rt` | 기타매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `etc_sel` | 기타매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `etc_pre_sel` | 기타직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `etc_sel_rt` | 기타매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `etc_net_buy` | 기타순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `grs_buy` | 합계매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `grs_pre_buy` | 합계직전매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `grs_buy_rt` | 합계매수대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `grs_sel` | 합계매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `grs_pre_sel` | 합계직전매도 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `grs_sel_rt` | 합계매도대비율 | `char` | 6 | 일반 | 0 |  |  | 없음 |
|  | `grs_net_buy` | 합계순매수 | `char` | 18 | 일반 | 0 |  |  | 없음 |
|  | `inst_cd` | 투자자코드 | `char` | 16 | 일반 | 0 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "inq_tp": "1",
  "opt_prd": "",
  "ref_dt": ""
}
```

## Response JSON (Output)

```json
{
  "cntry_net_buy": "",
  "grs_buy": "",
  "scrt_sel_rt": "",
  "bank_pre_buy": "",
  "penfnd_pre_buy": "",
  "invt_sel": "",
  "ins_buy_rt": "",
  "scrt_buy_rt": "",
  "ins_buy": null,
  "mb_pre_sel": "",
  "scrt_pre_sel": "",
  "frgn_pre_sel": "",
  "etc_pre_sel": "",
  "grs_pre_buy": "",
  "scrt_buy": "",
  "penfnd_sel_rt": "",
  "frgn_net_buy": "",
  "mb_sel": "",
  "ins_sel_rt": null,
  "cntry_pre_buy": "",
  "grs_sel": "",
  "ind_buy_rt": "",
  "ind_sel": "",
  "invt_net_buy": "",
  "penfnd_buy": "",
  "ins_sel": null,
  "etc_sel_rt": "",
  "invt_pre_sel": "",
  "ind_pre_buy": "",
  "mb_buy_rt": "",
  "cntry_buy_rt": "",
  "bank_buy": "",
  "etc_pre_buy": "",
  "etc_buy": "",
  "invt_sel_rt": "",
  "scrt_pre_buy": "",
  "ins_pre_buy": "",
  "invt_pre_buy": "",
  "etc_buy_rt": "",
  "ins_pre_sel": "",
  "mb_pre_buy": "",
  "frgn_buy": "",
  "bank_buy_rt": "",
  "etc_sel": "",
  "ind_sel_rt": "",
  "mb_buy": "",
  "grs_net_buy": "",
  "cntry_pre_sel": "",
  "grs_buy_rt": "",
  "inst_cd": "",
  "penfnd_buy_rt": "",
  "penfnd_net_buy": "",
  "frgn_buy_rt": "",
  "bank_net_buy": "",
  "ins_buy_net": null,
  "bank_pre_sel": "",
  "invt_buy": "",
  "cntry_buy": "",
  "frgn_sel_rt": "",
  "bank_sel": "",
  "cntry_sel": "",
  "grs_sel_rt": "",
  "cntry_sel_rt": "",
  "grs_pre_sel": "",
  "penfnd_pre_sel": "",
  "scrt_sel": "",
  "mb_net_buy": "",
  "etc_net_buy": "",
  "scrt_net_buy": "",
  "frgn_sel": "",
  "invt_buy_rt": "",
  "mb_sel_rt": "",
  "ind_buy": "",
  "tm": "",
  "ind_net_buy": "",
  "ind_pre_sel": "",
  "bank_sel_rt": "",
  "frgn_pre_buy": "",
  "penfnd_sel": ""
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `domestic_trend-investor`
- 원본 범위: `A1:O107`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K19 |
| OUTPUT | A21:J101 |
| Request JSON (Input) | A103:A104 |
| Response JSON (Output) | A106:A107 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
