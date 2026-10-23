# 접근토큰 폐기

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | revoke |
| API 통신 방식 | HTTP |
| API 명 | 접근토큰 폐기 |
| HTTP Method | POST |
| Content-Type | application/json |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /auth-service/v1/revoke |
| API 요청 제한 | API 디폴트 |

## 설명

```text
발급된 토큰을 폐기합니다.
*********************************************************************************
해외 실시간 시세 신청 후 이용 시세 가능 내역 변경 시 
기존 접근토큰 폐기 후 접근토큰을 발급하셔야 변경 종목이
반영됩니다.
*********************************************************************************
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `appkey` | 앱키 | `String` | 100 | 일반 | 1 |  |  | Y |  |
|  | `appsecret` | 앱 시크릿 | `String` | 100 | 일반 | 1 |  |  | Y |  |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `timestamp` | 응답일시 | `String` | 29 | 일반 | 1 |  |  | 없음 |
|  | `status` | 요청 결과 코드 | `String` | 4 | 일반 | 0 |  |  | 없음 |
|  | `message` | 응답 메시지 | `String` | 1000 | 일반 | 1 |  |  | 없음 |

## Request JSON (Input)

```json
{
  "appsecret": null,
  "appkey": null
}
```

## Response JSON (Output)

```json
{
  "message": null,
  "timestamp": null,
  "status": null
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `revoke`
- 원본 범위: `A1:O30`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K18 |
| OUTPUT | A20:J24 |
| Request JSON (Input) | A26:A27 |
| Response JSON (Output) | A29:A30 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
