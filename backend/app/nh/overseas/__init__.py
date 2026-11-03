"""해외(CME 등) 종목용 NH 연동. `/trade/v1/overseas/*` 호출은 해외 키(`NH_OVERSEAS_APP_KEY`)가 필요하다.

시세는 `quotes`, 주문은 `orders`, 계좌·상품 조회는 `account`에 있다. 결과 형식은 국내(`app.nh.domestic`)와 같다.
러너는 아직 해외 종목을 거부한다. 해외 종목을 실행하는 경로는 전략 입력을 확장하는 작업에서 연결한다.
"""

OVERSEAS_UNSUPPORTED = "해외 종목은 아직 지원하지 않습니다"
