"""해외(CME 등) 종목용 NH 연동 자리. `/trade/v1/overseas/*` 호출은 해외 키(`NH_OVERSEAS_APP_KEY`)가 필요하다.

시세·계좌·주문 함수는 국내(`app.nh.domestic`)와 같은 형태로 여기에 구현한다. 구현 전까지 러너는 해외 종목을 거부한다.
"""

OVERSEAS_UNSUPPORTED = "해외 종목은 아직 지원하지 않습니다"
