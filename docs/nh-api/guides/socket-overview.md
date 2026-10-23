# 소켓 연결 및 세션 초기화 안내

- 출처 URL: [소켓 연결 및 세션 초기화 안내](https://apidev.futures.co.kr/#/api/info/socket-overview)
- 확인일: 2026-10-24 (Asia/Seoul)
- 수록 범위: 페이지 본문의 연결 절차·필드 표·요청·응답 예제와 지원 링크.
- 원문 간 차이는 마지막의 정리 메모에 별도 표시.

<!-- source-content:start -->

실시간 API 테스트를 시작하기 전 인증과 연결 절차를 안내합니다.

01

## 접근 토큰 발급

- App Key와 Secret Key를 이용하여 인증에 필요한 접근 토큰을 발급받습니다.
- 발급받은 접근 토큰은 웹소켓 키 발급 요청 시 인증 정보로 사용됩니다.

### 접근 토큰 발급 예시

```http
POST /auth-service/v1/token HTTP/1.1
Accept: application/json, text/plain, */*
Content-Type: application/x-www-form-urlencoded

{
  "grant_type": "client_credentials",
  "appkey": "975...",
  "appsecret": "eGT..."
}
```

### 응답

```json
{
  "access_token": "erJ...",
  "token_type": "Bearer",
  "scopes": "S",
  "expires_in": "86400",
  "expires_at": "2026-08-26 10:50:00"
}
```

다음 단계

응답의 access_token 값을 복사하여 웹소켓 키 발급 요청의 Authorization 헤더에 사용합니다.

02

## 웹소켓 키 발급

- 1단계에서 발급받은 접근 토큰을 이용해 실시간 웹소켓 연결에 필요한 웹소켓 키를 발급받습니다.
- 웹소켓 연결 시 응답으로 받은 access_key를 WEBSOCKET_KEY 항목에 설정합니다.

체크 포인트

웹소켓 키는 웹소켓 연결 시 1회 사용합니다.

### 웹소켓 키 발급

```http
GET /permission/v1/web-socket-key HTTP/1.1
Accept: application/json, text/plain, */*
Authorization: Bearer erJ...
```

### 응답

```json
{
  "access_key": "1e0..."
}
```

03

## 소켓 연결 및 세션 초기화

- 2단계에서 발급받은 웹소켓 키를 이용하여 실시간 웹소켓 서버에 연결합니다.
- 최초 연결 후 접근 토큰을 이용해 session_init 메시지를 전송하여 세션을 초기화합니다.
- 세션 초기화가 완료되면 이용하려는 실시간 API의 본문 메시지를 전송하여 응답을 수신합니다.

### 1. 웹소켓 연결

```text
websocket "wss://apidev.futures.co.kr/trade/ws-stream?access_key=1e0..." # access_key 입력
```

### 2. 세션 초기화

```json
{
  "header": {
      "api_ver": "1",
      "action": "0"
  },
  "body": {
      "action_code": "session_init",
      "session_token": "erJ..."
  }
}
```

| 이름 | 타입 | 필수 | 샘플 | 설명 |
| --- | --- | --- | --- | --- |
| header<br>공통 헤더 | Object | N |  |  |
| - api_ver<br>api 버전 | String | Y | 1 |  |
| - action<br>action 값 | String | Y | 0 | 값 무관 |
| body<br>웹소켓 바디 | Object | N |  |  |
| - action_code<br>action 코드 | String | Y | session_init |  |
| - session_token<br>접근토큰 값 | String | Y | erJ... | 발급받은 access_token 값을 설정합니다. |

체크 포인트

session_init 전송 후 서버로부터 온 INIT_SUCCESS 응답을 확인 후 본문 메시지를 전송하세요.

### 3-1. 본문 메시지 전송 - 국내 시세체결 예시

```json
{
  "header" : {
      "api_ver": "1",
      "action": "A"
  },
  "body" : {
      "action_code": "KA",
      "action_sym": "A0169000"
  }
}
```

| 이름 | 타입 | 필수 | 샘플 | 설명 |
| --- | --- | --- | --- | --- |
| header<br>공통 헤더 | Object | N |  |  |
| - api_ver<br>api 버전 | String | Y | 1 |  |
| - action<br>구독 / 구독 해제 | String | Y | A | A: 구독, D: 해제 |
| body<br>웹소켓 바디 | Object | N |  |  |
| - action_code<br>실시간 구분 | String | Y | KA | 국내 시세 체결: KA(주간), KC(야간)<br>국내 시세 호가: KB(주간), KD(야간)<br>해외 시세 체결: FA<br>해외 시세 호가: FB |
| - action_sym<br>실시간 종목코드 | String | Y | A0169000 |  |

### 3-2. 본문 메시지 전송 - 국내 주문/체결 예시

```json
{
  "header" : {
      "api_ver": "1",
      "action": "A"
  },
  "body" : {
      "action_code": "O1"
  }
}
```

| 이름 | 타입 | 필수 | 샘플 | 설명 |
| --- | --- | --- | --- | --- |
| header<br>공통 헤더 | Object | N |  |  |
| - api_ver<br>api 버전 | String | Y | 1 |  |
| - action<br>구독 / 구독 해제 | String | N | A | A: 구독, D: 해제 |
| body<br>웹소켓 바디 | Object | N |  |  |
| - action_code<br>실시간 구분 | String | N | O1 | 주문 체결: O1 |

※ 자세한 내용은 [API 개발하기](https://apidev.futures.co.kr/#/api) 페이지에서 확인하실 수 있습니다.

<!-- source-content:end -->

## 지원 링크

- 더 궁금한 내용이 있나요? [자주 묻는 질문](https://apidev.futures.co.kr/#/support/faq)
- 기술지원이 필요한가요? [문의하기](https://apidev.futures.co.kr/#/support/qna)

## 원문 간 차이 (정리 메모)

아래 표는 원문을 비교한 정리 메모다.

| 항목 | 이 페이지의 원문 | 다른 출처의 원문 | 정리 상태 |
| --- | --- | --- | --- |
| 토큰 발급 요청 본문 | Content-Type은 `application/x-www-form-urlencoded`이지만 요청 예제 본문은 JSON 객체 | [응답 안내](response-overview.md)의 토큰 발급 예제는 같은 Content-Type 아래 폼 형식 본문을 제시. [엑셀 명세](../apis/token.md)의 Content-Type도 `application/x-www-form-urlencoded`. | 원문 예제를 각각 보존. 실제 전송 규격은 별도 확인 필요. |
| WebSocket 연결 예제 주소 | `wss://apidev.futures.co.kr/trade/ws-stream?access_key=1e0...` | [엑셀 국내 시세체결 명세](../apis/KA.md)의 실전 Domain은 `wss://api.futures.co.kr`, 모의 Domain은 `wss://apidemo.futures.co.kr`이며 경로는 `/trade/ws-stream?access_key={{WEBSOCKET_KEY}}` | 원문 주소를 각각 보존. 개요 예제와 개별 명세의 도메인이 다르며, 실제 연결 주소는 별도 확인 필요. |
| api_ver 타입 표기 | 세션 초기화·시세체결·주문/체결 표에서 `String` | [엑셀 국내 시세체결 명세](../apis/KA.md)는 `int`, [엑셀 국내 주문/체결 명세](../apis/O1_K.md)는 `char` | 출처별 타입 표기를 그대로 보존. 원문 예제의 `"1"`도 유지. |

문서명 `O1_K`과 전송 필드 `action_code`의 값 `O1`을 구분한다.
이 페이지의 국내 주문/체결 예제와 [엑셀 명세](../apis/O1_K.md)의 해당 필드 샘플은 모두 `O1`이다.

## 관련 문서

- [응답 테스트 개요 및 설명](response-overview.md)
- [접근토큰 발급 API](../apis/token.md)
- [웹소켓 키 발급 API](../apis/web-socket-key.md)
- [국내 시세체결 API](../apis/KA.md)
- [국내 주문/체결 API](../apis/O1_K.md)
- [전체 API 목록](../README.md)
