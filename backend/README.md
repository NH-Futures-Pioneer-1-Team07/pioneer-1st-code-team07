# 백엔드

## 기술 스택

| 구분 | 기술 | 역할 |
| --- | --- | --- |
| 언어 | Python | 전략·지표 계산과 백테스트 |
| 웹 프레임워크 | FastAPI | 프론트엔드 API와 실시간 통신 |
| 환경·패키지 관리 | uv | Python 버전·가상환경·의존성 관리 |

- 의존성은 `pyproject.toml`과 `uv.lock`으로 관리한다.
- 매매 실행은 백엔드에서 관리한다.
- 모의매매와 백테스트는 같은 전략 판단 코드를 공유한다.

## 실행

환경 파일을 만들고 의존성을 설치한 뒤 서버를 실행한다.

```bash
cp .env.example .env
```

```bash
uv sync
```

```bash
uv run uvicorn app.main:create_app --factory --reload
```

- `TRADING_ENV`는 필수다. `mock`(모의) 또는 `real`(실전)을 쓴다. 없으면 서버가 시작되지 않고 없는 변수 이름을 알려 준다.
- `STRATEGIES_DIR`, `RUNS_DIR`는 선택이다. 생략하면 `backend/strategies`, `backend/runs`를 쓴다.
- `NH_APP_KEY`, `NH_APP_SECRET`는 NH선물 API를 부를 때만 필요하다. `TRADING_ENV`가 고른 환경(모의 또는 실전)의 키를 넣는다. 없으면 서버는 시작하지만 NH를 부르는 순간 필요한 변수 이름을 알려 주는 오류가 난다.
- `.env`에는 비밀정보가 들어갈 수 있으므로 커밋하지 않는다.

테스트는 다음 명령으로 실행한다.

```bash
uv run pytest
```

## 폴더 구조

| 경로 | 내용 |
| --- | --- |
| `app/` | FastAPI 앱. 설정(`config.py`), 앱 생성(`main.py`), API(`api/`) |
| `strategy_base/` | 전략 인터페이스(`interface.py`), 입력·출력 형식(`models.py`), 전략 폴더 형식(`manifest.py`), 등록(`registry.py`), 공통 지표(`indicators.py`), 테스트 도우미(`testing.py`) |
| `strategies/` | 전략 폴더. 폴더 하나가 전략 하나다 |
| `strategies/_template/` | 새 전략을 만들 때 복사하는 템플릿. `_`로 시작하는 폴더는 등록하지 않는다 |
| `app/nh/` | NH선물 API 호출(인증, 호출 제한, 시세 조회) |
| `app/records/` | 실행 기록의 저장·조회와 비밀정보 제거 |
| `runs/` | 실행 기록. 구조는 [runs/README.md](runs/README.md) |
| `tests/` | 테스트 |

## 전략 추가 방법

1. `strategies/_template/`을 `strategies/<전략 id>/`로 복사한다.
   - 폴더명이 전략 `id`다. 소문자 영문으로 시작하고 소문자·숫자·밑줄만 쓴다. 예: `week02_samsung_futures_intraday`
2. `manifest.json`을 고친다.
   - `name`, `description`: UI에 표시한다.
   - `instruments`: 지원 종목. 첫 번째 종목이 기본 종목이다.
   - `bar`: 봉 단위. 예: `{"unit": "minute", "size": 3}`
   - `parameters`: 파라미터 이름, 기본값, 설명. 전략 문서의 파라미터 목록과 같은 이름을 쓴다.
3. `strategy.py`의 `Strategy` 클래스에 전략 문서의 판단 규칙을 구현한다.
4. `README.md`에 전략 문서 링크와 구현 메모를 쓴다.
5. `tests/`에 전략 테스트를 추가하고 `uv run pytest`로 확인한다.
6. 서버를 다시 시작하면 `GET /api/strategies`에 나타난다. `manifest.json`이나 `strategy.py`에 문제가 있으면 서버 로그에 폴더명과 원인이 남고 목록에서 제외된다.

### 전략이 하는 일

- 전략은 `Context`를 읽고 `StrategyOutput`을 돌려준다. 형식은 `strategy_base/models.py`에 있다.
- 봉이 마감될 때 `on_bar(ctx)`가 호출된다. 장중 가격 갱신에 반응해야 하면 `on_price(ctx)`도 구현한다.
- 입력 `ctx`: 완성된 봉(`bars`, 마지막이 판단 대상), 현재 시각, 종목 최종거래일, 진입분별 포지션(`lots`), 미체결 주문(`open_orders`), 파라미터, 직전 호출의 상태(`state`)
- 출력 `StrategyOutput`: 주문 의도(`orders`), 미체결 취소 요청(`cancels`), 매매 판단 기록(`decisions`), 다음 호출에 넘길 상태(`state`)
- 주문 의도는 방향, 수량, 진입·청산 구분, 진입분 id, 이유, 주문 유형, 유효 시한(봉 개수)으로 이루어진다.
- 전략은 시세 수신, 주문 전송, 계좌 조회, 파일 저장을 직접 호출하지 않는다.
- 아무것도 하지 않으려면 빈 `StrategyOutput()`을 돌려준다.

### 공통 지표

`strategy_base/indicators.py`의 함수는 입력만 보고 결과를 돌려주는 순수 함수다.

| 함수 | 내용 |
| --- | --- |
| `confirmed_swings(bars, side_bars)` | 주어진 봉에서 확정된 고점·저점을 시간순으로 돌려준다. 뒤쪽 `side_bars`개 봉이 완성돼야 확정된다 |
| `latest_swings(swings, kind, count)` | 종류별로 가장 최근 확정 `count`개를 돌려준다 |
| `average_volume(bars, count)` | 마지막 `count`개 봉의 평균 거래량. 봉이 모자라면 `None` |

- "신호 봉이 시작되기 전에 확정된" 값이 필요하면 신호 봉을 뺀 `bars[:-1]`을 넘긴다.
- 평균 거래량에서 신호 봉을 빼야 하면 `bars[:-1]`을 넘긴다.

### 전략 테스트

`strategy_base/testing.py`로 서버 없이 고정 봉 데이터에 전략을 실행한다.

- `make_bars(rows, start, minutes)`: (고가, 저가, 종가, 거래량) 목록으로 연속한 봉을 만든다.
- `run_on_bars(strategy, bars, lots=..., open_orders=..., last_trading_day=...)`: 봉이 하나씩 마감되는 것처럼 `on_bar`를 호출하고 호출마다 출력을 돌려준다. 체결은 흉내 내지 않는다.
- 예시는 `tests/test_template_strategy.py`를 따른다.

## NH선물 API

`app/nh/`가 NH선물 API 호출을 맡는다. 전략은 직접 부르지 않고 러너가 부른다.

| 파일 | 내용 |
| --- | --- |
| `client.py` | `NHClient.call(경로, 본문, 호출 등급)`. 접근토큰을 붙이고, 호출 제한을 지키고, 실패를 예외로 바꾼다 |
| `auth.py` | 접근토큰 발급·보관. 메모리에만 두고 만료 5분 전에 다시 발급한다 |
| `rate_limit.py` | 주문 5건/초, 계좌 10건/초, 시세 10건/초 간격을 지킨다. 환경마다 따로 센다 |
| `errors.py` | `TransportError`, `HttpError`, `BusinessError`, `GatewayError`, `NHConfigError` |
| `quotes.py` | `fetch_minute_bars`(국내 분봉 → `Bar`), `fetch_quote`(현재가·최종거래일) |
| `account.py` | `fetch_deposit`(예탁금), `fetch_positions`(보유 포지션), `fetch_orders`(주문 내역), `fetch_orderable_quantity`(주문가능수량) |
| `orders.py` | `place_order`(신규 주문), `cancel_order`(취소 주문). 모의 환경에서만 낸다 |
| `realtime.py` | `RealtimeConnection`. 실시간 웹소켓 연결, 구독, 재연결 |
| `realtime_data.py` | 실시간 구독(`Feed`)과 수신 데이터(`Trade`, `OrderBook`, `OrderEvent`), 알림(`SubscriptionFailed`, `Reconnected`) |
| `values.py` | 응답의 문자열 값을 숫자·날짜로 바꾸는 함수 |

- 환경: `TRADING_ENV=mock`이면 `apidemo.futures.co.kr`, `real`이면 `api.futures.co.kr`을 부른다.
- 성공 판단: HTTP 200이어도 본문에 `errorCode`나 `msg_cd`가 있으면 실패로 본다. `EG`·`EST`로 시작하는 코드는 `GatewayError`, 그 밖은 `BusinessError`다.
- 다시 보내기: 실패해도 다시 보내지 않는다. 예외는 토큰이 거부된 경우(HTTP 401, 토큰 재발급 코드)로, 토큰을 새로 받아 한 번만 다시 보낸다. 시간 초과는 처리 여부를 알 수 없으므로 다시 보내지 않는다.
- 비밀정보: 키와 토큰은 로그, 예외 메시지, 객체 표시에 나오지 않는다.

### 분봉 조회

- `fetch_minute_bars(client, 종목코드, minutes=3, start=날짜, end=날짜)`는 하루씩 나눠 조회한다. 주말은 건너뛰고 휴장일은 빈 응답이라 봉이 없다. 하루 분량이 한 번에 오기 때문에 다음 데이터 키로 이어받지 않는다.
- 주간(`nght_tp=1`)만 조회한다. 모의환경은 야간을 지원하지 않는다.
- 거래량은 `occurs1_cum_trd_qty`를 봉 구간 거래량으로 쓴다. 이름은 누적이지만 모의환경의 삼성전자선물 2026-10-27 데이터에서는 봉 구간 값으로 관찰됐다는 것이 전략 문서의 기록이다.
- **미확인**: 응답의 봉 시각(`occurs1_exch_tm`)이 봉의 시작인지 마감인지는 모의환경 호출로 확인하지 못했다. 기본값은 시작 시각(`time_marks="start"`)으로 본다. 마감 시각이면 `time_marks="end"`로 부르면 봉 길이를 빼서 시작 시각으로 바꾼다. 모의환경 키로 확인한 뒤 이 항목을 갱신해야 한다.

### 계좌 조회와 주문

- 계좌 조회는 계좌 LIMIT(10건/초), 주문과 취소는 주문 LIMIT(5건/초)로 호출한다.
- 보유 포지션과 주문 내역은 다음 데이터 키가 있으면 이어받아 합친다. 같은 키가 반복되면 멈춘다.
- 응답에 실리는 계좌번호·계좌명은 읽지 않고, 요청에도 계좌번호를 넣지 않는다.
- `fetch_orders(client, open_only=True)`는 미체결 주문만 조회한다. 주문 상태는 `OrderStatus`(접수·확인·부분체결·전체체결·자동취소·거부)로 바뀌고, 접수·확인·부분체결이 `is_open`이다.
- `place_order`와 `cancel_order`는 `TRADING_ENV=mock`일 때만 요청을 보낸다. 실전이면 `OrderBlocked`를 내고 요청하지 않는다.
- 신규 주문의 체결조건은 FAS다. 시장가는 가격을 `0`으로 보내고, 지정가는 가격이 필요하다.
- `cancel_order`의 매매구분은 원주문의 매매구분이다.
- 주문 거부(`msg_cd`)는 `BusinessError`다. 시간 초과(`TransportError`)는 접수 여부를 알 수 없으므로 다시 보내지 않고 `fetch_orders`로 확인해야 한다.
- 정정 주문은 구현하지 않았다.

### 실시간 수신

`RealtimeConnection`이 웹소켓 하나를 열어 구독을 지키고 끊기면 다시 붙는다. 이벤트 루프 안에서 쓴다.

```python
connection = RealtimeConnection(client, on_event=handle, on_state=show_state)
await connection.subscribe(Feed("KA", "A116B000"))   # 체결
await connection.subscribe(Feed("KB", "A116B000"))   # 호가
await connection.subscribe(Feed("O1"))               # 주문/체결 알림(종목 없음)
connection.start()
...
await connection.stop()
```

- `handle(event)`는 `Trade`, `OrderBook`, `OrderEvent`, `SubscriptionFailed`, `Reconnected` 중 하나를 받는다. 이벤트 루프에서 불리므로 오래 걸리는 일을 하지 않는다.
- 상태는 `connecting`, `live`, `reconnecting`, `stopped`이고 `on_state(state, detail)`로 알린다.
- 접속키는 연결할 때마다 새로 발급받고, 연결 후 접근토큰으로 세션을 초기화한 뒤 구독을 건다.
- 서버의 `pingpong`은 받은 그대로 되돌린다. 웹소켓 핑 프레임은 끈다.
- 서버가 90초 동안 아무것도 보내지 않으면 끊긴 연결로 보고 다시 붙는다.
- 끊기면 0·1·2·5·10·30·60초로 기다리는 시간을 늘리며 다시 붙고, 60초 넘게 붙어 있었으면 바로 다시 붙는다. 붙고 나면 구독을 모두 다시 걸고 `Reconnected`를 알린다.
- **`Reconnected`를 받으면 분봉·호가·미체결 주문을 조회로 다시 채워야 한다.** 끊긴 동안의 값은 다시 오지 않는다.
- 구독은 `Feed` 단위로 전체 20건까지다. 넘기면 요청 없이 `SubscriptionLimitExceeded`를 낸다. 실시간 구독 상한은 계정 하나에 걸리므로 다른 곳에서 구독하면 서버가 거절할 수 있고, 이때 `SubscriptionFailed`로 알린다.
- `Trade.is_trade`가 거짓이면 체결량이 0인 기타 틱이다. 체결로 쓰려면 `is_trade`인 것만 쓴다.
- `OrderEvent`의 계좌번호는 읽지 않는다.
- 접속 주소에 접속키가 붙으므로 주소와 연결 예외의 글은 로그에 남기지 않고 예외 종류만 남긴다.
- **미확인**: 모의환경 서버로 직접 연결해 보지 못했다. 구독 거절 응답의 `code`·`data` 형식은 명세 문서와 참고한 구현을 따랐으므로, 키로 확인하며 다르면 고쳐야 한다.
