"""해외(CME 등) 종목용 NH 연동. `/trade/v1/overseas/*` 호출은 해외 키(`NH_OVERSEAS_APP_KEY`)가 필요하다.

시세는 `quotes`, 주문은 `orders`, 계좌·상품 조회는 `account`에 있다. 결과 형식은 국내(`app.nh.domestic`)와 같다.
"""
