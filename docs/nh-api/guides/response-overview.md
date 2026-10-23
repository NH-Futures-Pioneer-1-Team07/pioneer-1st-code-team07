# 응답 테스트 개요 및 설명

- 출처 URL: [응답 테스트 개요 및 설명](https://apidev.futures.co.kr/#/api/info/response-overview)
- 확인일: 2026-10-24 (Asia/Seoul)
- 수록 범위: 페이지 본문의 설명·표·HTTP 요청·응답 예제와 지원 링크.
- 원문 간 차이는 마지막의 정리 메모에 별도 표시.

<!-- source-content:start -->

API 응답 테스트를 위한 기본 개념과 사용 방법을 안내합니다.

## 도메인 정보

NH선물은 안정적인 연동 및 테스트를 위해 실전 환경과 모의 환경을 분리하여 제공합니다.

- 실전 환경: 실제 운영 데이터가 처리되는 환경입니다.
- 모의 환경: 실제 데이터에 영향 없이 API 호출 규격 및 응답 동작을 사전에 검증하고 테스트할 수 있는 환경입니다.

실전 환경

[https://api.futures.co.kr](https://api.futures.co.kr)

모의 환경

[https://apidemo.futures.co.kr](https://apidemo.futures.co.kr)

## 접근토큰 발급 요청 안내

NH선물의 REST API를 호출하기 위해 아래 규격에 맞춰 POST 요청으로 접근토큰을 발급받야아 합니다.

- 호출 방식: POST 메서드로 /auth-service/v1/token 경로에 요청합니다.
- 요청 헤더: Content-Type 헤더를 application/x-www-form-urlencoded로 설정해야 합니다.
- 요청 바디: grant_type, appkey, appsecret을 바디(Body)에 포함하여 전송합니다.
- 호출 방식: 요청 및 인증 정보가 올바르면 HTTP 200 OK와 함께 토큰 정보(JSON)가 반환됩니다.

### HTTP 요청 샘플

```http
POST /auth-service/v1/token HTTP/1.1
Accept: application/json, text/plain, */*
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&appkey=975...&appsecret=eGT...
```

### HTTP 응답 샘플

```http
HTTP 200 OK

{
  "access_token": "erJ...",
  "token_type": "Bearer",
  "scopes": "S",
  "expires_in": "86400",
  "expires_at": "2026-08-26 10:50:00"
}
```

## 접근토큰 유의 사항

- 유효 시간(24시간): 발급된 접근토큰의 유효 시간은 최초 발급 시점 기준 24시간입니다. 만료 후에는 자동으로 삭제되므로 재발급받아야 합니다.
- 기존 유효 토큰 반환: 토큰 만료 시간 이내에 재발급을 요청하는 경우, 새로운 토큰이 생성되지 않고 현재 유효한 기존 토큰이 그대로 반환됩니다. 토큰이 만료되었거나 폐기된 경우에만 새 토큰이 발급됩니다.
- 토큰 폐기 및 차단: 토큰이 폐기된 경우 즉시 차단 처리되어 해당 토큰을 이용한 모든 API 호출이 제한됩니다.

## API 요청 정보 안내

NH선물의 REST API를 요청하기 위해 기본적으로 구성해야 하는 요청 규격 안내이며, 상세한 설정은 각 API 명세를 참조하시기 바랍니다.

- 호출 방식: 각 API 명세에 지정된 메서드(POST/GET)와 엔드포인트 URL로 요청합니다.
- Content-Type 설정: API 요청 시 본문은 JSON 형식을 사용하므로 Content-Type 헤더를 application/json로 설정합니다.
- 접근토큰(Bearer Token) 설정: Authorization 헤더에 발급받은 토큰 값을 Bearer {Access_Token} 형태로 전달해야 합니다. (Bearer 뒤 공백 필수)
- 요청 바디: API 가이드의 API 명세의 필수 파라미터를 확인하여 JSON 객체 포맷으로 전송합니다.

### API 조회/호출 횟수 제한

API 유형에 따라 초당 요청 가능한 최대 횟수가 제한됩니다.

| API 유형 | LV1 |
| --- | --- |
| 주문 LIMIT | 5건/초 |
| 계좌 LIMIT | 10건/초 |
| 시세 LIMIT | 10건/초 |

### 실시간 구독 건수 제한

실시간 서비스는 계정 당 전체 구독 가능 건수가 최대 20건으로 제한됩니다.

| API 유형 | LV1 |
| --- | --- |
| 실시간 | 20건 |

### HTTP 요청 샘플

```http
POST /trade/v1/domestic/order HTTP/1.1
Accept: application/json, text/plain, */*
Content-Type: application/json
Authorization: Bearer erJ...

{"sym":"","trd_div":"","ord_tp_cd":"","ord_qty":"","ord_pric":"","exec_cnd_cd":""}
```

### HTTP 응답 샘플

```http
HTTP 200 OK

{
  "ord_no": "",
  "msg_cd": "",
  "msg_cntn": ""
}
```

<!-- source-content:end -->

## 지원 링크

- 더 궁금한 내용이 있나요? [자주 묻는 질문](https://apidev.futures.co.kr/#/support/faq)
- 기술지원이 필요한가요? [문의하기](https://apidev.futures.co.kr/#/support/qna)

## 원문 간 차이 (정리 메모)

아래 표는 원문을 비교한 정리 메모다.

| 항목 | 이 페이지의 원문 | 다른 출처의 원문 | 정리 상태 |
| --- | --- | --- | --- |
| 토큰 발급 요청 본문 | Content-Type은 `application/x-www-form-urlencoded`이며 본문도 `grant_type=client_credentials&appkey=975...&appsecret=eGT...` 형식 | [소켓 안내](socket-overview.md)의 토큰 발급 예시는 같은 Content-Type 아래 JSON 객체를 본문으로 제시 | 원문 예제를 각각 보존. 본문 표현의 차이가 있으며, 실제 전송 규격은 별도 확인 필요. |

## 관련 문서

- [소켓 연결 및 세션 초기화 안내](socket-overview.md)
- [접근토큰 발급 API](../apis/token.md)
- [접근토큰 폐기 API](../apis/revoke.md)
- [전체 API 목록](../README.md)
