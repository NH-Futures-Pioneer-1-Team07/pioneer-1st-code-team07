# 웹소켓 키 발급

## 기본 정보

| 항목 | 값 |
| --- | --- |
| 문서명 | web-socket-key |
| API 통신 방식 | HTTP |
| API 명 | 웹소켓 키 발급 |
| HTTP Method | GET |
| Content-Type |  |
| 실전 Domain | https://api.futures.co.kr |
| 모의 Domain | https://apidemo.futures.co.kr |
| URL 명 | /permission/v1/web-socket-key |
| API 요청 제한 | API 디폴트 |

## 설명

```text
웹소켓(WebSocket) 연결 안내

실시간 웹소켓 연결을 위한 키가 발급되었습니다. 아래 안내에 따라 연결을 진행해 주시기 바랍니다.
발급된 키 값은 wss 연결 시 access_key 항목에 입력해 주세요. (웹소켓 연결 시 1회 사용)

1. 연결 후 session_init 전송
웹소켓 연결이 완료되면 아래와 같은 형식으로 session_init 데이터를 전송해 주세요.
전송 데이터
{
    header: {
        api_ver: "1",
        action: "0"   // 값은 무관합니다
    },
    body: {
        action_code: "session_init",
        session_token: "{JWT Token}"
    }
}

2. 서버 응답 확인
session_init 전송 후 서버로부터 아래와 같은 응답을 받게 됩니다.
응답 데이터
{
    code: "INIT",
    msg: "INIT_SUCCESS"   // 성공 시 값이며, 그 외의 값은 실패를 의미합니다
}

3. 세션 유지 (Ping-Pong)
서버는 세션 유지를 위해 주기적으로 Ping-Pong 신호를 전송합니다. 아래 데이터를 수신하면, 받은 내용을 그대로 서버에 재전송해 주셔야 합니다.
응답 데이터
{
    code: "pingpong",
    msg: "pingpong"
}
⚠️ 주의: 서버로 Ping-Pong 응답을 보내지 않을 경우, 세션이 자동으로 종료됩니다.


[안내] 정기 시스템 점검 안내
 - 점검 일시 : 매주 일요일 06:00 ~ 06:15 (약 15분간)
 - 영향 범위 : 점검 시간 동안 시스템이 일시 중단되며, 연결되어 있던 모든 WebSocket 세션이 종료됩니다.
 - 조치 사항 : 점검 종료 후 실시간 연결이 원활히 재개될 수 있도록, 연결이 끊긴 경우 클라이언트에서 재연결을 수행해 주시기 바랍니다.
                     (인증 키가 만료된 경우 재발급 후 재연결)
```

## INPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 필수 | 기본값 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## OUTPUT

| 상위 Object | Key | 한글명 | Type | 길이 | Meta 타입 | 배열 길이 | 샘플 | 설명 | 마스킹 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | `access_key` | 웹소켓 접근키 | `String` | 36 | 일반 | 1 |  |  | 없음 |

## Request JSON (Input)

```json
{}
```

## Response JSON (Output)

```json
{
  "access_key": null
}
```

## 원본 위치

- 원본 파일: `전체_API_문서.xlsx`
- 원본 시트: `web-socket-key`
- 원본 범위: `A1:O26`
- 빈 셀은 빈 값으로 유지.
- 표의 셀 내부 줄바꿈은 `<br>`로 표시.
- JSON 예제는 키·값·순서·구조를 유지하고 줄바꿈과 들여쓰기만 적용.

| 문서 요소 | 원본 셀·범위 |
| --- | --- |
| 기본 정보 | A3:B10, A12:B12 |
| 설명 | A11:B11 |
| INPUT | A14:K15 |
| OUTPUT | A18:J20 |
| Request JSON (Input) | A22:A23 |
| Response JSON (Output) | A25:A26 |
| API 목록으로 이동 | A1 |

원본 Excel의 `API 목록으로 이동` 하이퍼링크 대상: `#'API 목록'!A1`.
