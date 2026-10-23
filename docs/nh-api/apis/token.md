# 접근토큰 발급

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | token |
| API 통신 방식 | HTTP |
| API 명 | 접근토큰 발급 |
| HTTP Method | POST |
| Content-Type | application/x-www-form-urlencoded |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /auth-service/v1/token |
| API 요청 제한 | API 디폴트 |

## 설명

```text
접근토큰을 발급합니다.
*********************************************************************************
해외 실시간 시세 이용 가능 내역이 변경된 경우
기존 접근토큰 폐기 후 접근토큰을 발급하셔야 변경 종목이
반영됩니다.
*********************************************************************************
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `grant_type` | OAuth 권한 부여 타입 | `String` | 20 | 일반 | 0 | client_credentials | client_credentials로 고정 | Y | client_credentials |
|  | `appkey` | 앱키 | `String` | 100 | 일반 | 1 |  | REST API 신청 후 발급받은 APP Key | Y |  |
|  | `appsecret` | 앱 시크릿 | `String` | 100 | 일반 | 1 |  | REST API 신청 후 발급받은 Secret Key | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `access_token` | 접근토큰 | `String` | 1000 | 일반 | 1 |  | Access 토큰 | 없음 |
|  | `token_type` | 토큰 타입 | `String` | 6 | 일반 | 0 |  | Bearer | 없음 |
|  | `scopes` | 운영, 모의투자 구분 | `String` | 4 | 일반 | 0 |  | R:운영, S:모의투자 | 없음 |
|  | `expires_in` | 토큰 만료 기한 | `String` | 5 | 일반 | 0 |  | 토큰 만료 기한(초 단위) | 없음 |
|  | `expires_at` | 토큰 만료 일시 | `String` | 19 | 일반 | 1 |  | 토큰 만료 일시<br>(YYYY-MM-DD HH:mm:ss) | 없음 |

## Request JSON (Input)

```json
{
  "grant_type": "client_credentials",
  "appsecret": null,
  "appkey": null
}
```

## Response JSON (Output)

```json
{
  "access_token": null,
  "expires_at": null,
  "scopes": null,
  "token_type": null,
  "expires_in": null
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `token`
- 원본 범위: `A1:O33`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K19 |
| OUTPUT | A21:J27 |
| Request JSON (Input) | A29:A30 |
| Response JSON (Output) | A32:A33 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
