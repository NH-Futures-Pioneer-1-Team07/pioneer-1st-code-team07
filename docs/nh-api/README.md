# NH선물 API 문서

원본 엑셀의 전체 API 목록·상세 명세·오류코드 정의서와 공식 개발자센터의 공통 안내를 Markdown으로 정리한 문서다.
종목 마스터 TXT 원본과 파일 형식·검색 방법도 함께 관리한다.

## API 명세 엑셀 원본 정보

| 항목 | 값 |
| --- | --- |
| 원본 파일 | [전체_API_문서.xlsx](전체_API_문서.xlsx) |
| 정리 기준 | 저장된 원본 엑셀의 내용 |
| 시트 수 | 50개: API 목록 1개, API 상세 49개 |
| API 통신 방식 | HTTP 41개, WEBSOCKET 8개 |
| 원본 파일 SHA256 | `8661fe1db218b6113fab7040667cdbe7a5bff9fffd1d31cbed6f5ddfa2e5739b` |

## 읽는 방법

- 아래 목록에서 API 이름이나 URL 명을 검색한 뒤 상세 문서로 이동한다.
- 상세 문서는 기본 정보, 설명, INPUT, OUTPUT, 요청·응답 JSON, 원본 위치 순서로 읽는다.
- 개별 API 상세 명세는 원본 엑셀을 기준으로 확인한다.
- 공통 가이드는 각 문서의 웹 출처와 확인일을 기준으로 확인한다.
- 오류코드는 오류코드 정의서에서 코드 또는 메시지로 검색한다.
- 종목 마스터는 자료 목록과 파일 형식을 확인한 뒤 원본 TXT에서 검색한다.
- 출처에 명시되지 않은 지원 여부나 제한값을 추정하지 않는다.

## 공통 가이드

| 문서 | 내용 | 출처 | 확인일 |
| --- | --- | --- | --- |
| [응답 테스트 개요 및 설명](guides/response-overview.md) | 실전·모의 환경, 접근토큰, HTTP 요청·응답, 호출·구독 제한 | [공식 페이지](https://apidev.futures.co.kr/#/api/info/response-overview) | 2026-10-24 |
| [소켓 연결 및 세션 초기화 안내](guides/socket-overview.md) | 접근토큰·웹소켓 키 발급, 소켓 연결, 세션 초기화, 실시간 구독 | [공식 페이지](https://apidev.futures.co.kr/#/api/info/socket-overview) | 2026-10-24 |

## 오류코드 정의서

| 문서 | 내용 | 원본 |
| --- | --- | --- |
| [오류코드 정의서](error-codes.md) | 시스템 ERROR 19행, 주문오류 ERROR 103행, errorCode 판별 예시 | [오류코드_정의서.xlsx](오류코드_정의서.xlsx) |

## 종목 마스터 파일

| 문서 | 내용 |
| --- | --- |
| [자료 목록·검색 방법](symbol-master/README.md) | 국내 3개·해외 5개 TXT 원본, 파일별 행 수·크기·SHA256, 검색 예시, 관련 API |
| [파일 형식·필드 확인 상태](symbol-master/formats.md) | 파일별 열 수·구분 규칙·원문 샘플·열별 확인 상태 |

## API 목록

| API 명 | URL 명 | 바로가기 | 원본 Excel 링크 |
| --- | --- | --- | --- |
| 국내_현재가 | domestic_price | [이동](apis/domestic_price.md) | `#'domestic_price'!A1` |
| 국내_호가 | domestic_price-bid | [이동](apis/domestic_price-bid.md) | `#'domestic_price-bid'!A1` |
| 국내_차트(일) | domestic_chart-daily | [이동](apis/domestic_chart-daily.md) | `#'domestic_chart-daily'!A1` |
| 국내_차트(분) | domestic_chart-minute | [이동](apis/domestic_chart-minute.md) | `#'domestic_chart-minute'!A1` |
| 국내_선물전체시세 | domestic_price-all-futures | [이동](apis/domestic_price-all-futures.md) | `#'domestic_price-all-futures'!A1` |
| 국내_옵션전체시세 | domestic_price-all-option | [이동](apis/domestic_price-all-option.md) | `#'domestic_price-all-option'!A1` |
| 국내_투자자직전매매동향 | domestic_trend-investor | [이동](apis/domestic_trend-investor.md) | `#'domestic_trend-investor'!A1` |
| 국내_종목예상체결가 | domestic_price-expect-fill | [이동](apis/domestic_price-expect-fill.md) | `#'domestic_price-expect-fill'!A1` |
| 국내_품목별세부정보 | domestic_product-detail | [이동](apis/domestic_product-detail.md) | `#'domestic_product-detail'!A1` |
| 국내_현재가(야간) | domestic_price-night | [이동](apis/domestic_price-night.md) | `#'domestic_price-night'!A1` |
| 국내_옵션전체시세(야간) | domestic_price-all-option-night | [이동](apis/domestic_price-all-option-night.md) | `#'domestic_price-all-option-night'!A1` |
| 국내_신규주문 | domestic_order | [이동](apis/domestic_order.md) | `#'domestic_order'!A1` |
| 국내_정정주문 | domestic_modify | [이동](apis/domestic_modify.md) | `#'domestic_modify'!A1` |
| 국내_취소주문 | domestic_cancel | [이동](apis/domestic_cancel.md) | `#'domestic_cancel'!A1` |
| 국내_주문가능수량 | domestic_orderable-quantity | [이동](apis/domestic_orderable-quantity.md) | `#'domestic_orderable-quantity'!A1` |
| 국내_잔고내역 | domestic_open-interest | [이동](apis/domestic_open-interest.md) | `#'domestic_open-interest'!A1` |
| 국내_주문오류내역 | domestic_order-error | [이동](apis/domestic_order-error.md) | `#'domestic_order-error'!A1` |
| 국내_주문내역 | domestic_order-history | [이동](apis/domestic_order-history.md) | `#'domestic_order-history'!A1` |
| 국내_예수금조회 | domestic_deposit | [이동](apis/domestic_deposit.md) | `#'domestic_deposit'!A1` |
| 국내_신규주문(야간) | domestic_order-night | [이동](apis/domestic_order-night.md) | `#'domestic_order-night'!A1` |
| 국내_정정주문(야간) | domestic_modify-night | [이동](apis/domestic_modify-night.md) | `#'domestic_modify-night'!A1` |
| 국내_취소주문(야간) | domestic_cancel-night | [이동](apis/domestic_cancel-night.md) | `#'domestic_cancel-night'!A1` |
| 국내_시세체결 | KA | [이동](apis/KA.md) | `#'KA'!A1` |
| 국내_시세호가 | KB | [이동](apis/KB.md) | `#'KB'!A1` |
| 국내_시세체결(야간) | KC | [이동](apis/KC.md) | `#'KC'!A1` |
| 국내_시세호가(야간) | KD | [이동](apis/KD.md) | `#'KD'!A1` |
| 국내_주문/체결 | O1_K | [이동](apis/O1_K.md) | `#'O1_K'!A1` |
| 해외_현재가 | overseas_price | [이동](apis/overseas_price.md) | `#'overseas_price'!A1` |
| 해외_호가 | overseas_bid-price | [이동](apis/overseas_bid-price.md) | `#'overseas_bid-price'!A1` |
| 해외_차트(일) | overseas_chart-daily | [이동](apis/overseas_chart-daily.md) | `#'overseas_chart-daily'!A1` |
| 해외_차트(분) | overseas_chart-minute | [이동](apis/overseas_chart-minute.md) | `#'overseas_chart-minute'!A1` |
| 해외_옵션전체시세 | overseas_price-all-option | [이동](apis/overseas_price-all-option.md) | `#'overseas_price-all-option'!A1` |
| 해외_품목별세부정보 | overseas_product-detail | [이동](apis/overseas_product-detail.md) | `#'overseas_product-detail'!A1` |
| 해외_장운영정보 | overseas_market-operations | [이동](apis/overseas_market-operations.md) | `#'overseas_market-operations'!A1` |
| 해외_주문 | overseas_order | [이동](apis/overseas_order.md) | `#'overseas_order'!A1` |
| 해외_주문가능수량 | overseas_orderable-quantity | [이동](apis/overseas_orderable-quantity.md) | `#'overseas_orderable-quantity'!A1` |
| 해외_주문오류내역 | overseas_order-error | [이동](apis/overseas_order-error.md) | `#'overseas_order-error'!A1` |
| 해외_주문내역 | overseas_order-history | [이동](apis/overseas_order-history.md) | `#'overseas_order-history'!A1` |
| 해외_잔고내역 | overseas_open-interest | [이동](apis/overseas_open-interest.md) | `#'overseas_open-interest'!A1` |
| 해외_예수금조회 | overseas_deposit | [이동](apis/overseas_deposit.md) | `#'overseas_deposit'!A1` |
| 해외_만기일조회 | overseas_product-expiry | [이동](apis/overseas_product-expiry.md) | `#'overseas_product-expiry'!A1` |
| 해외_보유포지션만기조회 | overseas_open-interest-expiry | [이동](apis/overseas_open-interest-expiry.md) | `#'overseas_open-interest-expiry'!A1` |
| 해외_누적손익현황 | overseas_cumulative-pl | [이동](apis/overseas_cumulative-pl.md) | `#'overseas_cumulative-pl'!A1` |
| 해외_시세체결 | FA | [이동](apis/FA.md) | `#'FA'!A1` |
| 해외_시세호가 | FB | [이동](apis/FB.md) | `#'FB'!A1` |
| 해외_주문/체결 | O1 | [이동](apis/O1.md) | `#'O1'!A1` |
| 접근토큰 발급 | token | [이동](apis/token.md) | `#'token'!A1` |
| 접근토큰 폐기 | revoke | [이동](apis/revoke.md) | `#'revoke'!A1` |
| 웹소켓 키 발급 | web-socket-key | [이동](apis/web-socket-key.md) | `#'web-socket-key'!A1` |

## API 명세 엑셀 변환 기준

- 모든 시트의 값과 원본 순서를 유지.
- INPUT 11개 열과 OUTPUT 10개 열을 모두 보존.
- 빈 셀, 숫자 0, 문자열의 선행 0, 필수 여부, 마스킹 값을 구분.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- 표의 특수문자와 앞뒤 공백은 필요한 경우 HTML 문자 참조로 표시.
- 여러 줄 설명은 원문의 줄바꿈·들여쓰기를 유지하는 텍스트 코드 블록으로 표시.
- JSON 예제는 문자열 밖의 줄바꿈·들여쓰기만 정리.
- 원본 표와 JSON 예제의 내용이 달라도 원문 그대로 보존.
- 목록의 이동 링크는 해당 Markdown 상세 문서로 연결.
- 원본 Excel 링크 대상은 목록의 추가 열과 상세 문서의 원본 위치에 보존.

## API 명세 엑셀 원본 위치

- 원본 시트: `API 목록`
- 원본 범위: `A1:C51`
- 제목: `A1`
- 표 머리글: `A2:C2`
- API 목록: `A3:C51`
