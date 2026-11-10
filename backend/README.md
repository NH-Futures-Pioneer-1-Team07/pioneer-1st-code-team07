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
- `STRATEGIES_DIR`, `RUNS_DIR`, `SWEEPS_DIR`, `REPORTS_DIR`, `MINUTE_CACHE_DIR`는 선택이다. 생략하면 `backend/strategies`, `backend/runs`, `backend/sweeps`, `backend/reports`, `backend/data/minute_cache`를 쓴다.
- `NH_OVERSEAS_APP_KEY`, `NH_OVERSEAS_APP_SECRET`는 해외 API(`/trade/v1/overseas/*`)용 키다. 국내 키로는 해외 API가 `EGW016`(호출 권한 없음)으로 거절된다. 해외 전략을 쓸 때만 필요하다.
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
| `app/nh/` | NH선물 API 호출. 공통(인증, 호출 제한)은 바로 아래, 국내 종목은 `domestic/`, 해외 종목은 `overseas/` |
| `app/runners/` | 백테스트·모의매매 실행, 전략 입력 준비, 포지션·손익 계산, 계좌 정리 |
| `app/data/` | VIX 일 종가 읽기·갱신. 데이터 파일은 `data/vixcls.csv` |
| `app/records/` | 실행 기록의 저장·조회·변경 알림과 비밀정보 제거 |
| `app/reports/` | 검증 보고서 읽기(`report.md`의 JSON 머리말과 `table.csv`) |
| `app/sweep/` | 조합 탐색. 파라미터·기간 조합을 여러 개 백테스트하고 결과 요약을 쌓는다 |
| `runs/` | 실행 기록. 구조는 [runs/README.md](runs/README.md) |
| `sweeps/` | 조합 탐색 결과. 구조는 [조합 탐색](#조합-탐색) |
| `reports/` | 조합 탐색 비교표와 보고서 |
| `tests/` | 테스트 |

## 전략 추가 방법

1. `strategies/_template/`을 `strategies/<전략 id>/`로 복사한다.
   - 폴더명이 전략 `id`다. 소문자 영문으로 시작하고 소문자·숫자·밑줄만 쓴다. 예: `week03_zn_treasury_futures`
2. `manifest.json`을 고친다.
   - `name`, `description`: UI에 표시한다.
   - `instruments`: 지원 종목. 첫 번째 종목이 기본 종목이다. 각 종목에 `market`(`domestic` 또는 `overseas`)을 반드시 쓴다. 없거나 다른 값이면 전략이 등록되지 않는다. 해외 종목은 `exchange`(예: `FCME`)도 쓴다.
   - `bar`: 판단 기준 봉 단위. 봉이 마감될 때마다 `on_bar`가 호출된다. 예: `{"unit": "minute", "size": 3}`
   - `instruments[].margin`(선택): 계약당 기준 증거금. `ctx.margin`으로 받는다.
   - `instruments[].tick_size`(선택): 호가 단위. 백테스트의 슬리피지와 가격 경로가 쓰며, 없으면 봉 가격 차이로 추정한다(소수 둘째 자리까지만 구별하므로 ZN처럼 1/64 단위인 종목은 적어야 한다).
   - `instruments[].legs`(선택): 두 종목의 가격을 비율대로 합친 스프레드 종목을 선언한다. `[{"code": "ZFZ26", "ratio": 3}, {"code": "ZNZ26", "ratio": -2}]`처럼 종목 2개를 쓰며 스프레드 가격은 `3 × ZFZ26 − 2 × ZNZ26`이고 한 세트가 수량 1이다. 이때 `multiplier`·`margin`·`tick_size`는 한 세트 기준으로 적는다. `app/runners/spread.py`가 두 종목의 일봉(기준일)과 분봉(봉 시작 시각)을 짝지어 스프레드 봉을 만든다. 양쪽 종가가 양수이고 거래량이 0보다 큰 쌍만 쓰고, 고가·저가는 합친 시가와 종가의 최댓값·최솟값, 거래량은 두 종목 중 작은 값이다.
   - 스프레드 종목의 백테스트: `BacktestService`와 조합 탐색이 `legs`가 있는 종목이면 두 종목의 분봉·일봉을 각각 받아 스프레드 봉으로 합친다. 가능 기간은 두 종목 중 봉이 적은 쪽 기준이다. 수수료는 스프레드 가격이 아니라 두 종목 체결대금의 합(`Σ|비율| × 종목 종가`의 기간 평균 × 거래승수 × 수량)에 수수료율을 곱한다. 슬리피지 1틱은 `tick_size`만큼 불리한 체결이므로 스프레드 종목의 `tick_size`는 두 종목이 1호가씩 불리하게 체결되는 폭으로 적는다.
   - `series`(선택): 판단에 함께 쓰는 추가 봉 계열. 일봉만 지원한다. 예: `{"daily": {"unit": "day", "size": 1}}`. `ctx.series["daily"]`로 받는다.
   - `chart_lines`(선택): 모의매매 차트에 그릴 판단용 선. 항목은 `series`(`bar`는 판단 기준 봉 차트, `daily`는 일봉 차트), `kind`(`sma` 단순이동평균은 `period` 필요, `previous_close` 직전 거래일 종가선은 일봉만), `label`, 마우스를 올렸을 때 보이는 `description`이다. `label`을 `describe`의 항목 이름과 같게 쓰면 "현재 판단" 패널의 같은 항목에도 설명이 붙는다.
   - `history_bars`(선택, 기본 0): 장이 열린 첫 봉에서도 지표를 계산하도록 전날까지의 `bar` 봉을 이 개수만큼 앞에 이어 준다.
   - `parameters`: 파라미터 이름, 기본값, 설명. 전략 문서의 파라미터 목록과 같은 이름을 쓴다.
     - 화면에서 시작 전에 바꿀 수 있는 값이면 `editable`을 켜고, 입력칸 이름 `label`, `unit`(`percent`는 0.2를 20%로 표시), 허용 범위 `min`·`max`를 적는다. 모의매매·백테스트 시작 요청의 `params`가 범위를 벗어나거나 숫자가 아니면 `422`로 거부한다.
3. `strategy.py`의 `Strategy` 클래스에 전략 문서의 판단 규칙을 구현한다.
4. `README.md`에 전략 문서 링크와 구현 메모를 쓴다.
5. `tests/`에 전략 테스트를 추가하고 `uv run pytest`로 확인한다.
6. 서버를 다시 시작하면 `GET /api/strategies`에 나타난다. `manifest.json`이나 `strategy.py`에 문제가 있으면 서버 로그에 폴더명과 원인이 남고 목록에서 제외된다.

### 전략이 하는 일

- 전략은 `Context`를 읽고 `StrategyOutput`을 돌려준다. 형식은 `strategy_base/models.py`에 있다.
- 봉이 마감될 때 `on_bar(ctx)`가 호출된다. 장중 가격 갱신에 반응해야 하면 `on_price(ctx)`도 구현한다.
- 지금의 판단을 화면에 보여 주려면 `describe(ctx)`를 구현한다. 주문은 내지 않고 `{"sections": [{"title", "headline", "tone", "rows": [[이름, 값], ...]}]}`를 돌려준다(`tone`은 `buy`·`sell`·`neutral`). 모의매매가 매 판단 뒤와 운용 시작 직후에 부르고, 실패해도 매매는 계속한다. 결과에 `levels`(`[{"label", "value", "description"}]`)를 더하면 모의매매 차트가 운용 중 그 값을 수평선으로 그린다(스프레드 전략의 진입·청산 경계).
- 판단의 근거 수치는 `Decision.detail`에 담는다. 판단 기록(`decision`)의 `detail`로 모의매매·백테스트 기록에 남는다. 주문 사유(`OrderIntent.reason`)는 체결 기록(`fill`)에 그대로 남으므로 판단 요약을 사유에 포함하면 체결 기록에서도 볼 수 있다.
- 입력 `ctx`: 완성된 봉(`bars`, 마지막이 판단 대상), 현재 시각, 종목 최종거래일, 진입분별 포지션(`lots`), 미체결 주문(`open_orders`), 파라미터, 직전 호출의 상태(`state`)
- 추가 입력 `ctx`: 추가 봉 계열(`series`, 일봉은 오늘 이전 날짜만), 직전 거래일 종가 VIX(`vix`), 계약당 기준 증거금(`margin`), 보유분 전체의 평가손익(`unrealized_pnl`, 수수료 제외). 값을 알 수 없으면 `None`이다.
- 출력 `StrategyOutput`: 주문 의도(`orders`), 미체결 취소 요청(`cancels`), 매매 판단 기록(`decisions`), 다음 호출에 넘길 상태(`state`)
- 주문 의도는 방향, 수량, 진입·청산 구분, 진입분 id, 이유, 주문 유형, 유효 시한(봉 개수)으로 이루어진다.
- 전략은 시세 수신, 주문 전송, 계좌 조회, 파일 저장을 직접 호출하지 않는다.
- 아무것도 하지 않으려면 빈 `StrategyOutput()`을 돌려준다.

### VIX

- 전략에는 직전 거래일 종가 VIX를 넘긴다. 장중 VIX는 다루지 않는다.
- 출처는 FRED `VIXCLS` 일 종가이며 `data/vixcls.csv`에 저장한다. 백테스트와 모의매매가 같은 파일을 읽는다.
- 파일은 다음 명령으로 갱신한다. 받기에 실패하면 기존 파일을 그대로 둔다.

```bash
uv run python -m app.data.vix
```

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
- `run_on_bars(strategy, bars, lots=..., open_orders=..., last_trading_day=..., series=..., vix=..., margin=...)`: 봉이 하나씩 마감되는 것처럼 `on_bar`를 호출하고 호출마다 출력을 돌려준다. 체결은 흉내 내지 않는다.
- 예시는 `tests/test_template_strategy.py`를 따른다.

## NH선물 API

`app/nh/`가 NH선물 API 호출을 맡는다. 전략은 직접 부르지 않고 러너가 부른다. 종목의 `market`이 `domestic`이면 `app/nh/domestic/`을 쓴다. `overseas`는 `app/nh/overseas/`에 시세(`quotes`)·주문(`orders`)·계좌와 상품 조회(`account`)가 구현되어 있다. 러너는 해외 종목도 실행한다. 해외 종목은 전략 종목에 `exchange`가 있어야 하고(없으면 `422`) 해외 키가 없으면 `503`이다. 해외 분봉은 국내와 같이 한국 시간이며 봉이 시작한 시각이다(모의환경에서 진행 중인 봉의 거래량이 늘어나는 것으로 확인). 모의환경의 해외 분봉 조회는 조회 기간을 무시하고 최신 봉부터 한 쪽(약 495개)씩 돌려주므로, 다음 데이터 키로 과거 쪽을 이어받아 기간 밖의 봉을 거른다(2026-11-04 확인, 2026-03-30보다 오래된 봉은 없고 2026-08-10 이전은 드문드문하다). 해외 모의매매는 해외 키로 실시간 체결(`FA`)을 받고(주문/체결 알림은 구독하지 않고 계좌 조회로 맞춘다), 실시간이 끊긴 동안만 5초마다 현재가를 조회한다. 최종거래일은 알 수 없어 `None`이다. 해외 실시간의 체결시간은 거래소 시간(`exch_tm`, 미국 중부)이 아니라 한국 시간(`ko_exec_tm`)을 쓴다(2026-11-05 모의환경 확인).

| 파일 | 내용 |
| --- | --- |
| `client.py` | `NHClient.call(경로, 본문, 호출 등급)`. 접근토큰을 붙이고, 호출 제한을 지키고, 실패를 예외로 바꾼다. 주문이 아닌 조회가 `EGW036`(호출 속도 초과)으로 거절되면 1·2·3초 간격으로 최대 3번 다시 보낸다 |
| `auth.py` | 접근토큰 발급·보관. 메모리에만 두고 만료 5분 전에 다시 발급한다 |
| `rate_limit.py` | 주문 5건/초, 계좌 10건/초, 시세 10건/초 간격을 지킨다. 환경마다 따로 세고, 모든 `NHClient`가 제한기 하나(`SHARED_LIMITER`)를 함께 쓴다 |
| `errors.py` | `TransportError`, `HttpError`, `BusinessError`, `GatewayError`, `NHConfigError` |
| `domestic/quotes.py` | `fetch_minute_bars`(국내 분봉 → `Bar`), `fetch_quote`(현재가·최종거래일) |
| `domestic/account.py` | `fetch_deposit`(예탁금), `fetch_positions`(보유 포지션), `fetch_orders`(주문 내역), `fetch_orderable_quantity`(주문가능수량) |
| `domestic/orders.py` | `place_order`(신규 주문), `cancel_order`(취소 주문). 모의 환경에서만 낸다 |
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
- 거래량은 `occurs1_cum_trd_qty`를 봉 구간 거래량으로 쓴다. 이름은 누적이지만 값은 봉 구간 값이다(연속한 봉에서 오르내린다).
- 응답의 봉 시각(`occurs1_exch_tm`)은 **봉이 시작한 시각**이다. `Bar.time`에 그대로 쓴다(`time_marks="start"`가 기본). 마감 시각으로 오는 데이터를 다루게 되면 `time_marks="end"`로 부르면 봉 길이를 빼서 시작 시각으로 바꾼다.
- 봉에는 시가(`Bar.open`)도 담는다. 백테스트가 체결 가격으로 쓴다.

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
- 장중 체결·호가 데이터와 주문/체결 알림 데이터는 장 마감 후에 확인해서 아직 실제 값으로 확인하지 못했다. 아래 "모의환경 확인 결과"를 본다.

## 모의환경 확인 결과

2026-10-28 장 마감 후(16:50)에 모의환경(`apidemo.futures.co.kr`)을 읽기 전용으로 호출해 확인한 내용이다. 주문은 내지 않았다.

| 항목 | 확인한 내용 |
| --- | --- |
| 토큰 발급 | form 형식(`application/x-www-form-urlencoded`)으로 발급된다 |
| 현재가·최종거래일 | `A116B000`의 현재가 `last_pric`, 최종거래일 `lst_trd_dt`가 `YYYYMMDD`로 온다(2026-11-12) |
| 분봉 응답 순서 | 최신 봉이 먼저 온다. `fetch_minute_bars`가 오래된 순으로 정렬한다 |
| 분봉 건수 | 하루치(3분봉 138건)가 한 번에 온다. 다음 데이터 키(`nxt_key`)로 이어받지 않는다 |
| 주간 세션과 3분 격자 | 08:45에 시작하고 3분 격자도 08:45에 맞는다(08:45, 08:48, …, 15:30, 15:33). 15:36~15:42에는 봉이 없고 15:45에 종가 단일가 봉이 하나 있다(한 가격) |
| 봉 시각 | 봉 시작 시각이다. 08:45 봉은 여러 가격에 걸친 범위를 갖고, 15:45 봉은 한 가격이다 |
| 거래량 | 봉 구간 값이다. 08:45 봉은 시가 단일가 체결이 포함되어 다른 봉보다 큰 경우가 있었다 |
| 계좌 조회 | 예탁금·포지션·주문 내역·주문가능수량이 모두 조회된다. 주문 내역의 거래시간 구분 `0`(전체)을 받아 준다. 예탁금 1억원, 보유 포지션·주문 없음, 주문가능수량 105계약(매수 243,000) |
| 실시간 | 접속키 발급, 세션 초기화, 구독이 동작한다. 구독 성공 응답은 `{"code": "RT_INIT", "data": {"action", "action_code", "action_sym"}, "msg": ""}` 형식이다. 없는 종목은 `{"code": "RT_FAIL", "data": {...}, "msg": "...[종목: ...]"}`로 거절한다 |

- 주문/체결(`O1`) 구독 성공 응답의 `data`에는 계좌번호(`action_acnt`)가 실려 온다. 이 응답을 원본 그대로 기록하거나 출력하지 않는다.
- 확인하지 못한 것: 주문·취소(주문을 내지 않았다), 장중 체결·호가 수신, 주문/체결 알림 데이터. 장 시간에 확인해야 한다.

## 백테스트

`app/runners/`가 백테스트를 맡는다. 전략 코드는 모의매매와 같은 것을 쓴다.

### API

| 요청 | 내용 |
| --- | --- |
| `POST /api/backtests` | 백테스트를 시작하고 `202`와 실행 식별자(`strategy_id`, `mode`, `run_id`)를 바로 돌려준다. 요청의 `slippage_ticks`(선택, 0~20 정수)로 이번 실행의 슬리피지를 정하고, 없으면 환경변수 값을 쓴다. 범위를 벗어나면 `422`다 |
| `GET /api/backtests/current` | 실행 중인 백테스트의 식별자. 없으면 `{"run": null}` |
| `GET /api/backtests/assumptions` | 시작 전에 보여 줄 비용·체결 가정 |
| `GET /api/backtests/range?strategy_id=` | 전략의 종목으로 백테스트할 수 있는 기간(`start`, `end`, `last_trading_day`)과 봉이 적은 날(`sparse_days`) |
| `GET /api/runs/<전략 id>/backtest/<실행 일시>` | 진행 상황(`meta.progress`)과 결과 |

시작 요청 본문은 `strategy_id`, `start_date`, `end_date`, `initial_capital`이고, 전략 파라미터를 바꾸려면 `params`를 더한다.

- 종목은 전략 `manifest.json`의 첫 번째 종목이다. 종목코드와 `multiplier`(거래승수)가 있어야 하고, `market`이 `overseas`이면 `exchange`도 있어야 한다.
- 거부: 없는 전략 `404`, 잘못된 기간·초기자금·파라미터·일봉 전략·종목 정보 부족 `422`, 이미 실행 중 `409`, NH 인증 정보 없음 `503`.
- 종료일은 오늘보다 이전이어야 하고 기간은 366일 이하다. 시작일과 종료일은 아래 가능 기간 안이어야 하고 밖이면 `422`다.
- 한 번에 하나만 실행한다. 실행은 백그라운드에서 한다.
- 진행 상황은 `meta.progress`에 `{"stage": "prepare"|"compute"|"done", "done": n, "total": N}`로 갱신된다. 준비는 영업일 수, 계산은 데이터가 있는 날 수다.
- 데이터 조회가 실패하거나 기간에 분봉이 없으면 상태가 `error`로 끝나고 원인이 `event`로 남는다.

### 가능 기간

`GET /api/backtests/range?strategy_id=`는 전략의 첫 번째 종목에 대해 분봉이 있는 첫 날(`start`)과 마지막으로 마감된 거래일(`end`), 최종거래일(`last_trading_day`)을 돌려준다. 분봉이 전혀 없으면 `start`와 `end`가 `null`이다. `sparse_days`는 기간 안에서 봉이 적은 날을 `{날짜: 그날의 봉 수}`로 담는다. 하루 정상 봉 수(거래 시간 420분 ÷ 봉 크기)의 절반보다 적은 날이고 3분봉이면 70개 미만이다. 분봉이 없는 휴장일은 넣지 않는다. 처음 한 번은 기간의 날짜마다 NH를 조회해 몇 초 걸리고(2026.11월물 약 50일에 6.7초), 그날 안에는 종목별로 보관해 다시 조회하지 않는다. 없는 전략 `404`, NH 인증 정보 없음 `503`, NH 조회 실패 `502`다.

- 월물은 상장일 이전의 분봉이 없어서 조회 가능한 기간은 그 월물의 상장일부터다. NH 응답에는 상장일이 없어 날짜별 분봉 조회로 찾는다.
- `end`는 오늘 이전이고 최종거래일 이하이며, 그 이전에서 분봉이 있는 가장 최근 날이다.
- `start`는 `end`에서 주 단위로 거슬러 올라가며 분봉이 있는 주를 찾고(주마다 그 주의 한 날과 그 전 영업일을 본다), 연속 3주가 비면 멈춘다. 마지막으로 찾은 주 앞의 6일을 하루씩 확인해 가장 이른 날을 정한다. 월물 중간에 이어지는 연휴는 3주보다 짧으면 건너뛰고, 3주를 넘게 비면 그 앞의 데이터는 다른 월물로 보고 포함하지 않는다.
- 조회 호출은 20번 안팎이고, 같은 종목의 결과는 하루 동안 서버 메모리에 보관한다. 서버를 다시 시작하면 다시 조회한다.
- 모의환경 확인(2026-10-28): `A116B000`은 `2026-08-14`(1봉)부터 `2026-10-27`까지다. 20번의 호출로 찾았다.
- 모의환경 확인(2026-11-10): 해외 `ZNZ26`(5분봉)은 `2026-03-30`부터 `2026-11-09`까지다(약 7개월). `2026-08-10` 이전 72일은 하루 봉 수가 18~79개로 정상(약 276개)의 절반에 못 미치는 봉이 적은 날이고, `2026-08-11`부터 온전하다. 온전한 구간에서만 시험하려면 시작일을 `2026-08-11` 이후로 둔다.
- 모의환경 확인(2026-11-11): 해외 `ZFZ26`(5년)·`ZNZ26`(10년)의 일봉은 2026-11-10까지 받는다. 양쪽 종가가 양수이고 거래량이 0보다 큰 일봉 쌍은 126개(2026-05-05~11-10)이고 `ZFZ26`의 4월 일봉은 거래량이 0이다. 5분봉은 `ZFZ26`이 2026-05-06부터, `ZNZ26`이 2026-03-30부터이며 두 종목 모두 `2026-08-20`부터 온전하다(유효 쌍 250개 이상인 날 45일).
- 모의환경 확인(2026-11-11): 해외 1계약 주문의 예약 증거금은 `ZFZ26` 1,375 USD, `ZNZ26` 2,063 USD다(예탁 조회의 `init_mrgn` 증가분).
- 모의환경 확인(2026-11-11 한국시간 01시대): 해외 주문은 접수 응답(`confirmed`)만 오고 시장가·지정가 모두 체결되지 않았으며, 취소 요청은 주문번호를 받지만 원주문이 남았다. 취소 중인 주문에 다시 취소하면 `7047`, 매수 미체결이 있을 때 시장가·같거나 낮은 가격의 매도는 `7017`이다. 2026-11-04 한국시간 08:35~19:07에는 시장가 주문이 2~4초 안에 체결됐다.

### 스프레드 모의매매

`legs`가 있는 종목은 `app/runners/spread_broker.py`의 `SpreadBroker`가 두 종목의 `OverseasNHBroker`를 묶어 스프레드 종목 하나처럼 보이게 한다. 세션은 이를 일반 `Broker`로 쓴다.

- 주문: 스프레드 시장가 주문 하나를 두 종목의 시장가 주문으로 낸다(예 매수 1세트는 `ZFZ26` 매수 3·`ZNZ26` 매도 2). 세션에는 `S000001` 같은 스프레드 주문번호를 돌려준다.
- 체결: 두 종목이 모두 체결된 세트 수만 스프레드 체결로 센다. 체결가는 `Σ 비율 × 종목 체결가`다.
- 포지션: 두 종목 포지션에서 완성된 세트를 스프레드 포지션으로, 세트를 이루지 못한 나머지는 종목 포지션 그대로 돌려준다. 시작 전 계좌 확인은 스프레드와 두 종목의 포지션·미체결을 모두 보고 있으면 `409`로 거부한다.
- 한쪽만 체결된 진입: 진입 주문 뒤 30초(`SpreadBroker.entry_confirm_seconds`, 설정값 아님) 안에 두 종목이 모두 체결되지 않으면 미체결 주문을 취소하고, 체결된 종목을 시장가로 반대 매매해 원상복구한다. 별도 스레드가 없어 세션이 주문·포지션을 조회할 때(보통 10초 간격) 함께 진행한다. 청산 주문은 제한 시간으로 취소하지 않는다.
- 실시간: 두 종목의 체결(`FA`)을 받아 `SpreadPriceMux`가 `Σ 비율 × 종목 현재가`로 바꿔 세션에 전달한다. 두 종목의 체결이 모두 들어온 뒤부터 전달한다.
- 수수료 추정: 시작 시점 두 종목 현재가의 `Σ |비율| × 현재가`를 체결가 대신 써서 `거래승수 × 수량 × 수수료율`을 곱한다.
- 확인 상태(2026-11-11): 가짜 NH 호출로 위 동작을 시험했다. 실제 모의 서버의 해외 주문 체결·취소는 한국시간 01시대에 처리되지 않아 낮 시간에 확인해야 한다.

### 시뮬레이션 규칙

- 하루씩, 봉이 하나씩 마감되는 순서로 전략을 호출한다. 전략에는 그 시점까지 마감된 **당일 봉만** 전달한다.
- `on_bar`는 봉이 끝나는 시각에 부른다. 이 호출이 낸 시장가 주문은 **다음 봉의 시가**에 전량 체결한다. 그날 마지막 봉이면 그 봉의 종가에 체결한다.
- `on_price`는 봉마다 시가 → 불리한 극단 → 유리한 극단 → 종가 순으로 호가 단위씩 가격을 움직이며 부른다. 보유 중이면 불리한 극단이 먼저다(매수 보유는 저가, 매도 보유는 고가). 보유가 없으면 시가에서 가까운 극단이 먼저다. 이 호출이 낸 주문은 **그 가격**에 체결한다.
- `on_price`의 호출 시각은 봉 시작 시각(시가)과 봉이 끝나기 1초 전이다.
- 체결 가격에는 슬리피지를 불리한 방향으로 더한다. 수수료는 체결대금(체결가 × 거래승수 × 수량)에 수수료율을 곱한다.
- 미체결 주문은 없다(시장가는 전량 체결). 전략이 낸 취소 요청은 무시한다.
- 기간이 끝나면 남은 보유분을 마지막 봉 종가로 청산하고 `백테스트 종료 청산`으로 기록한다.
- 증거금과 주문가능수량은 제한하지 않는다.
- 결과(`result.json`)에는 자산 곡선(`equity_curve`)과 함께 기간의 일봉(`daily_bars`: `date`, `open`, `high`, `low`, `close`, `volume`)을 저장한다. 분봉을 날짜별로 합친 값이고, 이 기능 이전에 실행한 기록에는 없다.

### 비용·체결 가정

| 항목 | 값 | 바꾸는 방법 |
| --- | --- | --- |
| 수수료율 | 체결대금의 0.0085% | 환경변수 `BACKTEST_FEE_RATE`(0.000085) |
| 슬리피지 | 시장가 체결마다 불리한 방향으로 1틱 | 환경변수 `BACKTEST_SLIPPAGE_TICKS`(1), 실행마다 요청의 `slippage_ticks`(0~20) |
| 호가 단위 | 기간의 봉 가격 차이의 최대공약수 | 삼성전자선물은 500원으로 추정된다 |

수수료율은 NH선물 수수료 부과 기준(2026-09-07 개정)의 개별주식선물 온라인 매매 표준수수료다. API 주문을 온라인으로 보았고, 협의수수료와 거래소 수수료는 반영하지 않았다. 실행마다 쓴 가정은 `meta.json`의 `assumptions`에 기록한다.

## 조합 탐색

`app/sweep/`는 전략의 파라미터·기간 조합을 여러 개 백테스트하고 결과를 계속 쌓는다. 서버 없이 명령줄에서 엔진을 직접 부르며, `runs/` 기록은 남기지 않는다. 최종으로 고른 조합은 기존 백테스트 화면에서 한 번 더 실행해 전체 기록을 남긴다.

```bash
uv run python -m app.sweep run 요청.json
uv run python -m app.sweep run 요청.json --dry-run
uv run python -m app.sweep table <전략 id> --name <보고서 이름>
uv run python -m app.sweep range <전략 id>
```

| 명령 | 내용 |
| --- | --- |
| `run <요청.json>` | 요청 파일의 조합을 백테스트해 `sweeps/`에 쌓는다. 이미 있는 조합은 건너뛴다. `--dry-run`은 데이터를 받지 않고 실행·건너뛸 조합 수만 보여 준다. 조합 하나가 실패해도 나머지는 계속하고, 실패가 있으면 종료 코드가 1이다 |
| `table <전략 id>` | 쌓인 결과로 비교표를 `reports/<전략 id>/<이름>/table.csv`에 쓴다(`--name`, 기본 `default`). `--out`으로 경로를 직접 정한다 |
| `range <전략 id>` | 전략 종목의 백테스트 가능 기간과 봉이 적은 날을 조회한다. NH를 호출한다 |

### 요청 파일

```json
{
  "strategy_id": "week03_zn_treasury_futures",
  "initial_capital": 100000,
  "slippage_ticks": 1,
  "periods": [{"start": "2026-08-11", "end": "2026-09-30"}, {"start": "2026-10-01", "end": "2026-11-03"}],
  "params": [{"short_bars": 3}, {"short_bars": 8, "long_bars": 30}],
  "grid": {"profit_loss_rate": [0.1, 0.2, 0.3]}
}
```

| 필드 | 내용 |
| --- | --- |
| `strategy_id`, `initial_capital`, `periods` | 필수. `periods`는 `{start, end}` 목록이다 |
| `slippage_ticks` | 선택. 생략하면 환경변수 `BACKTEST_SLIPPAGE_TICKS` 값 |
| `params` | 선택. 기본 파라미터를 덮어쓰는 조합 목록. 적은 것만 바뀐다 |
| `grid` | 선택. 파라미터별 값 목록의 모든 곱을 조합으로 더한다 |

- 조합은 `params`(와 `grid`로 만든 조합) × `periods`다. 둘 다 없으면 기본 파라미터 하나만 실행한다.
- 파라미터는 전략 `manifest.json`의 `min`/`max` 검증을 따른다. 어긋나면 데이터를 받기 전에 멈춘다.
- 종료일은 오늘보다 이전이어야 한다. 기간 길이 상한(366일)은 적용하지 않는다.
- 같은 조합인지는 전략, 전체 파라미터(기본값 포함), 기간, 슬리피지, 초기자금, 수수료율로 정한 `id`가 같은지로 본다. 기본값과 같은 값을 적어도 같은 조합이다.

### 분봉 재사용

- 한 번 실행에서 모든 조합이 쓰는 분봉은 가장 이른 시작일부터 가장 늦은 종료일까지 한 번만 받는다.
- 받은 분봉은 `data/minute_cache/`에 저장해 다음 실행에서 쓴다. 요청한 기간 중 저장되지 않은 구간만 NH에서 받는다. 이 폴더는 Git에 올리지 않는다.
- NH가 오래된 분봉을 지워도 이미 받은 기간은 남는다. 오늘 이후 날짜는 완성되지 않아 저장하지 않는다.

### 저장 형식

```
sweeps/<전략 id>/results.jsonl       조합 하나당 한 줄
sweeps/<전략 id>/trades/<id>.jsonl   조합의 거래와 체결
```

`results.jsonl`의 한 줄:

| 필드 | 내용 |
| --- | --- |
| `id` | 조합의 정의로 만든 해시 16자 |
| `strategy_id`, `params`, `start`, `end`, `slippage_ticks`, `initial_capital`, `fee_rate` | 조합의 정의. `params`는 기본값을 포함한 전체 값이다 |
| `summary` | `net_pnl`, `gross_pnl`, `fee`, `return_rate`, `final_equity`, `max_drawdown`, `max_drawdown_rate`, `trade_count`, `win_count`, `loss_count`, `days`, `bars`. `runs/`의 `result.json`과 같은 값이다 |
| `daily_equity` | 자산 곡선 `{time, equity}` |
| `created_at`, `elapsed_seconds` | 저장 시각, 계산에 걸린 초 |

`trades/<id>.jsonl`의 한 줄(`kind`로 구분):

| `kind` | 필드 |
| --- | --- |
| `trade` | `entry_id`, `side`, `quantity`, `opened_at`, `closed_at`, `entry_price`, `exit_price`, `gross_pnl`, `fee`, `net_pnl`, `entry_reason`, `exit_reason` |
| `fill` | `time`, `side`, `quantity`, `price`(슬리피지 반영), `raw_price`(슬리피지 전), `fee`, `intent`(`entry`/`exit`), `entry_id`, `source` |

- 봉마다 남는 판단(`decision`)과 주문(`order`)은 저장하지 않는다. 백테스트 기록 용량의 대부분이 판단이고, 시장가 주문은 모두 체결되어 체결과 같은 내용이다.
- `trade`의 `entry_reason`·`exit_reason`은 같은 `entry_id`의 체결에서 읽은 이유다. 거래 수는 `summary.trade_count`와 같다.
- 용량: ZN 5분봉 73일 기준 조합 하나가 `results.jsonl` 약 5KB, 거래 파일 약 160~190KB다.

### 비교표

`table`이 만드는 `table.csv`는 조합이 행이고, 기간마다 지표 열이 붙는다.

- 앞쪽 열은 조합 사이에 값이 다른 파라미터다. 모든 조합에서 같은 값은 열로 만들지 않는다.
- `period_count`, `positive_periods`(순손익이 양수인 기간 수), `worst_net_pnl`, `total_net_pnl` 열이 있고, 합산 순손익이 큰 조합이 위에 온다.
- 기간마다 `net_pnl`, `return_rate`, `max_drawdown_rate`, `trade_count`, `win_rate`, `fee_ratio`(총손익 대비 수수료, 총손익이 0 이하면 빈칸), `sharpe`(일별 자산 변화율의 평균/표준편차 × √252, 계산할 수 없으면 빈칸) 열이 `지표[시작일~종료일]` 이름으로 붙는다.
- 승률, 수수료 비중, 샤프는 저장하지 않고 표를 만들 때 계산한다.

### 소요 시간

ZN 5분봉으로 확인했다(2026-11-10, 73일, 16,342봉). 분봉을 처음 받는 실행은 전체 약 7초였고, 조합 하나의 계산은 0.7~1.2초다. 저장된 분봉을 쓰면 조합 수에 비례해 늘어난다.

## 검증 보고서

`app/reports/`가 `reports/<전략 id>/<보고서 이름>/`의 `report.md`와 `table.csv`를 읽어 대시보드의 검증 리포트 탭에 준다. 보고서는 `sweep-report` 스킬이 파일로 쓰고, 형식은 [reports/README.md](reports/README.md)에 있다. API는 읽기만 한다.

| 요청 | 내용 |
| --- | --- |
| `GET /api/reports` | 보고서 목록. 갱신일이 최근인 순서. 항목은 `strategy_id`, `name`, `title`, `question`, `updated`, `author`, `result_count`, `recommended`(추천·대안 조합 이름), `error` |
| `GET /api/reports/<전략 id>/<이름>` | `meta`(머리말), `body`(마크다운 본문), `table`(`{columns, rows}`, 빈 칸은 `null`, 숫자는 실수. `table.csv`가 없으면 `null`) |

- 머리말이 없거나 JSON이 아니거나 필수 필드(`strategy_id`, `name`, `title`, `question`, `updated`, `author`, `result_count`, `periods`, `recommended`)가 빠진 보고서는 목록에서 `error`에 사유가 담기고 나머지 필드는 비어 있다. 상세 요청은 `422`다.
- 없는 보고서와 전략 id 형식에 맞지 않거나 `/`, `\`, 숨김(`.`으로 시작) 이름은 `404`다.
- 보고서 폴더가 없으면 목록은 빈 배열이다.

보고서의 그래프와 거래 패널은 아래 API로 조합 탐색 결과를 읽는다.

| 요청 | 내용 |
| --- | --- |
| `GET /api/sweeps/<전략 id>/results?ids=` | 쉼표로 구분한 결과 `id`(1~60개)의 조합 결과(정의, 요약, 일별 자산). 요청한 순서로 돌려주고 없는 `id`는 뺀다. `id` 형식이 틀리거나 개수가 맞지 않으면 `422` |
| `GET /api/sweeps/<전략 id>/trades/<id>` | 조합의 거래(`trades`)와 체결(`fills`). 기록이 없거나 `id` 형식이 틀리면 `404` |

- 조회는 `sweeps/<전략 id>/results.jsonl`을 매번 읽는다. 결과가 수만 줄로 늘면 색인이 필요하다.

## 모의매매

`app/runners/paper.py`가 전략 하나를 NH 모의계좌로 운용한다. 전략 코드는 백테스트와 같은 것을 쓴다. 모의 환경(`TRADING_ENV=mock`)에서만 운용한다.

### API

| 요청 | 내용 |
| --- | --- |
| `POST /api/trading/start` | 운용을 시작하고 `202`와 실행 식별자를 돌려준다. 본문은 `strategy_id`(와 선택으로 `params`) |
| `POST /api/trading/stop` | 정상 종료를 시작한다 |
| `GET /api/trading/status` | 단계, 시세 상태, 마지막 가격·봉 시각, 신규 주문 차단 사유, 손익, 보유 진입분, 진행 중인 주문, 전략이 설명한 현재 판단(`judgment`, 설명하지 않는 전략은 `null`), 전체 정리 진행과 결과(`clear`) |
| `GET /api/trading/account?market=` | NH 모의계좌의 예탁금, 보유 포지션, 미체결 주문. 운용 중이 아니어도 조회된다. `market`은 `domestic`(기본) 또는 `overseas`(해외 모의계좌, 예탁금은 USD) |
| `POST /api/trading/clear?market=` | 미체결 취소·전체 포지션 청산을 시작한다. `market`의 계좌를 정리하며 같은 시장에서 운용 중인 전략만 멈춘다 |

- 시작 거부: 없는 전략 `404`, 잘못된 파라미터·일봉 전략·종목 정보 부족·모의 환경이 아님 `422`, 이미 운용 중이거나 그 종목에 기존 포지션·미체결 주문이 있음 `409`, NH 인증 정보 없음 `503`, NH 계좌 조회 실패 `502`.
- 한 번에 전략 1개·종목 1개(전략의 첫 번째 종목)만 운용한다. 세션은 전용 스레드의 이벤트 루프에서 돈다.
- 시작할 때 예탁금·포지션·미체결 주문을 조회해 기록(`운용 전 계좌` 이벤트)한다.
- 단계는 `idle`, `running`, `stopping`, `clearing`이다. 운용이 끝나면 `idle`이 되고 `last_run`에 마지막 실행의 식별자와 상태가 남는다.
- 서버가 도중에 꺼지면 운용 중이던 기록은 다음 시작 때 `interrupted`가 된다. 보유 포지션과 미체결 주문은 자동으로 정리하지 않으므로 계좌를 확인해야 한다.

### 동작

- **분봉**: 5초마다 분봉을 조회해 마감된 봉(봉 끝 2초 뒤)을 시간순으로 한 번씩 `on_bar`에 전달한다. 운용을 시작한 뒤에 시작한 봉만 판단하며, 시작 전 봉은 `history_bars`가 있는 전략에 한해 첫 판단의 앞쪽 봉으로만 쓴다(오늘 시작 전 봉과 전일 봉을 합쳐 최근 `history_bars`개). `ctx.now`는 봉이 끝나는 시각이다.
- **가격**: 실시간 체결(국내 `KA`, 해외 `FA`)을 `on_price`에 전달한다(같은 가격이 1초 안에 반복되면 한 번만). 실시간이 연결 상태가 아니면 5초마다 현재가를 조회해 대신한다.
- **주문**: 전략의 주문 의도를 시장가 주문으로 보낸다.
  - 신규 진입은 주문 전에 주문가능수량을 조회해 가능한 수량만 주문한다. 계획 수량(`planned_quantity`)과 실제 수량(`quantity`)을 기록하고, 가능 수량이 0이면 주문하지 않는다.
  - 청산은 진입분의 보유 수량에서 이미 청산 주문이 나간 수량을 뺀 만큼만 낸다.
  - 주문 유효 시한(`valid_bars`)이 지나면 남은 수량을 취소한다. 전략의 취소 요청도 처리한다.
  - 거부된 주문은 사유를 기록하고 다시 보내지 않는다.
  - 시간 초과 등으로 처리 여부를 모르는 주문은 다시 보내지 않는다. 주문 내역에서 찾으면 이어받고, 3번 확인해도 없으면 접수되지 않은 것으로 본다. 그동안 전략의 `open_orders`에 `unknown-<번호>`로 전달돼 새 신호를 건너뛰게 한다.
- **원장**: 체결 알림(`O1`)의 누적 체결 수량으로 갱신한다. 알림을 놓치면 주문 내역 조회로 맞춘다. 손익 계산은 백테스트와 같은 `Ledger`다.
- **수수료**: NH 알림에 수수료가 없어 백테스트와 같은 요율(`BACKTEST_FEE_RATE`)로 추정하고 `fee_estimated`로 표시한다. 종료 때 계좌의 수수료·선물 확정손익 변화를 `result.json`의 `account`에 남긴다.

### 안전 규칙

신규 진입 주문은 아래 중 하나라도 해당하면 `blocked`로 기록하고 보내지 않는다. 청산 주문은 막지 않는다. 막는 이유는 `GET /api/trading/status`의 `entry_blocks`로 본다.

| 이유 | 조건 |
| --- | --- |
| 종료 중 | 종료를 시작한 뒤 |
| 주문 처리 여부를 확인하지 못함 | 처리 여부를 모르는 주문이 있음 |
| 계좌와 원장이 어긋남 | 10초 간격 대조에서 두 번 연속 계좌 포지션 수량이 원장과 다르거나, 우리가 내지 않은 미체결 주문이 계좌에 있음 |
| 분봉 조회가 계속 실패함 | 30초 넘게 분봉 조회가 성공하지 못함 |
| 시세를 받지 못함 | 실시간이 연결 상태가 아니고 30초 넘게 가격을 받지 못함 |

### 종료

`POST /api/trading/stop`은 다음 순서로 처리한다. 종료를 시작하면 전략을 더 부르지 않는다.

1. 이 운용의 미체결 주문을 취소한다.
2. 취소가 확인되면 이 운용의 보유 진입분을 시장가로 청산한다. 체결되지 않으면 5초마다 다시 시도한다.
3. 원장이 비고, 계좌의 그 종목 포지션과 미체결 주문이 0임을 확인하면 `completed`로 끝낸다.
4. 90초 안에 확인하지 못하면 `error`로 끝내고 `result.json`의 `open_lots`에 남은 진입분을 적는다.

처리 중 예외가 나면 `error`로 끝내고 보유 포지션과 미체결 주문이 남아 있을 수 있다고 `event`에 남긴다.

### 계좌 조회

`GET /api/trading/account`는 다음을 돌려준다. 계좌번호와 계좌명은 읽지 않는다.

| 필드 | 내용 |
| --- | --- |
| `deposit` | `cash`(예탁현금), `total_assets`(예탁자산), `order_available_total`·`order_available_cash`(주문가능금액), `initial_margin`·`maintenance_margin`(위탁·유지증거금), `futures_realized_pnl`(선물 확정손익) |
| `positions` | 수량이 0이 아닌 포지션. `code`, `name`, `side`, `quantity`, `closable_quantity`, `avg_price`, `last_price`(종가), `pnl`, `pnl_rate` |
| `open_orders` | 미체결 주문. `order_no`, `code`, `side`, `status`, `quantity`, `filled_quantity`, `remaining_quantity`, `price`, `received_time`(접수 시각 HHMMSS) |

모의 환경이 아니면 `422`, NH 인증 정보가 없으면 `503`, NH 조회에 실패하면 `502`다.

### 전체 정리

`POST /api/trading/clear`는 `202`와 `{"phase": "clearing"}`을 돌려주고 백그라운드에서 다음 순서로 처리한다. 이미 정리 중이면 `409`다. 모의 환경이 아니면 `422`, 인증 정보가 없으면 `503`이다(해외 계좌는 해외 키 이름을 알려 준다).

1. 운용 중인 전략의 판단을 멈춘다. 전략을 더 부르지 않고 신규 주문을 내지 않는다(`clearing`).
2. 계좌 전체의 미체결 주문을 종목과 관계없이 취소하고, 조회로 모두 사라졌는지 확인한다(30초).
3. 운용 중이면 그 운용을 종료한다. 운용이 낸 주문의 취소와 보유 진입분의 청산은 운용 종료 절차가 맡고, 이때 계좌 전체 확인은 하지 않는다(120초).
4. 운용이 끝난 뒤 계좌에 남은 포지션을 종목과 관계없이 반대 방향 시장가로 청산한다. 매수 보유는 매도로, 매도 보유는 매수로 낸다. 청산 주문이 미체결로 남아 있는 동안은 다시 내지 않고, 포지션이 남아 있고 미체결도 없으면 5초 간격으로 다시 낸다(60초).
5. 남은 미체결 주문과 보유 포지션을 조회해 결과로 돌려준다.

운용 종료와 계좌 전체 청산은 차례로 하므로 한 포지션에 청산 주문이 두 번 나가지 않는다.

진행은 `GET /api/trading/status`의 `clear`로 읽는다. `state`는 `running` 또는 `done`, `step`은 `cancel`, `stop_run`, `flatten`, `verify`, `done`이다. 끝나면 `clear.result`에 다음이 담긴다.

| 필드 | 내용 |
| --- | --- |
| `status` | `completed`(미체결·보유가 0) 또는 `incomplete` |
| `open_orders`, `positions` | 정리 뒤에 남은 미체결 주문과 보유 포지션 |
| `cancelled` | 취소를 요청한 주문 수 |
| `closed` | 낸 청산 주문(`code`, `side`, `quantity`). 다시 낸 것도 모두 담는다 |
| `problems` | 취소·청산 실패, 시간 초과 같은 문제 |

운용 중에 정리하면 단계마다 그 실행 기록에 `event`로 남기고 마지막에 결과를 남긴다. 운용이 없으면 서버 로그에만 남는다.

### 확인하지 못한 것

실제 모의계좌에 주문을 내 보지는 못했다. 위 동작은 가짜 NH(분봉·시세·주문·알림)로 확인했다. 주문/체결 알림(`O1`)의 필드가 명세와 같은지, 취소 후 주문의 상태 변화, 주문 내역의 주문번호가 주문 응답의 번호와 같은 형식인지는 장 시간에 소량 주문으로 확인해야 한다.

## 실시간 시세 웹소켓

`/ws/market?code=<종목코드>&market=<domestic|overseas>`가 한 종목의 실시간 체결·호가를 화면에 보낸다. 해외는 `legs=ZFZ26:3,ZNZ26:-2`를 함께 보내면 두 종목의 체결(`FA`)만 구독해 `Σ 비율 × 체결가`로 합성한 체결을 보낸다(호가 없음, 두 종목의 체결이 모두 들어온 뒤부터, 잘못된 구성은 `4422`). 구독 한도는 두 종목으로 세고, 같은 종목을 직접 보는 화면과 구독을 함께 쓴다. `market`을 생략하면 `domestic`이다. `app/nh/hub.py`의 `MarketHub`가 시장마다 NH 실시간 연결 하나(국내 키, 해외 키)를 여러 화면이 나눠 쓰게 한다. 모의매매 운용의 실시간 연결(체결·주문 알림)과는 별개다.

### 메시지

모두 JSON이고 `type`으로 구분한다. 연결하면 현재 연결 상태(`state`)를 먼저 한 번 보낸다.

| `type` | 내용 |
| --- | --- |
| `state` | 시세 연결 상태. `state`는 `connecting`, `live`, `reconnecting`, `stopped`, `detail`은 설명 |
| `trade` | 체결. `code`, `time`(HHMMSS), `price`, `quantity`, `cum_volume`, `open`, `high`, `low`, `best_ask`, `best_bid`, `is_trade` |
| `orderbook` | 호가. `code`, `time`, `total_ask_quantity`, `total_bid_quantity`, 10단계 `levels`(`ask_price`, `ask_quantity`, `bid_price`, `bid_quantity`) |
| `reconnected` | 시세가 끊겼다가 다시 연결됨. 끊긴 동안의 값은 오지 않으므로 **화면이 시세·차트·호가를 REST로 다시 조회해야 한다** |
| `subscription_failed` | 서버가 구독을 거절함. `code`(종목, 알 수 없으면 `null`), `reason_code`, `message` |

- `trade`의 `is_trade`가 거짓이면 체결량이 0인 기타 데이터다. 현재가·거래량 갱신에는 `is_trade`인 것만 쓴다.
- 장이 끝났거나 체결이 없으면 `trade`·`orderbook`은 오지 않고 `state`만 온다.

### 닫힘 코드

| 코드 | 뜻 |
| --- | --- |
| `4422` | 종목코드 형식이 올바르지 않음(국내 6~16자, 해외 3~16자 영문·숫자) 또는 `market` 값이 잘못됨 |
| `4503` | NH 인증 정보가 설정되지 않음. 해외는 `NH_OVERSEAS_APP_KEY`, `NH_OVERSEAS_APP_SECRET`을 사유에 알려 준다 |
| `4429` | 시장마다 서로 다른 종목을 4개까지만 볼 수 있음. 이미 보고 있는 종목에는 계속 붙을 수 있다 |

### 동작

- 종목마다 체결(국내 `KA`, 해외 `FA`)과 호가(국내 `KB`, 해외 `FB`)를 구독한다. 해외 모의환경에서 `FA`·`FB`가 오는 것을 확인했다(2026-11-05, ZNZ26). 첫 화면이 붙을 때 구독하고 마지막 화면이 떠날 때 해제한다. NH의 구독 한도(20건) 가운데 모의매매 운용이 쓸 몫을 남기려고 종목을 4개(8건)로 제한한다.
- 화면마다 대기열(256개)이 있고 가득 차면 오래된 메시지부터 버린다. 느린 화면이 다른 화면과 NH 수신을 막지 않는다.
- 서버를 끌 때 NH 실시간 연결을 정리한다.
- 모의환경 확인(2026-10-28, 장 마감 후): `/ws/market?code=A116B000`에 연결하면 `connecting`에 이어 `live`가 온다. 체결·호가 데이터는 장 시간에 확인해야 한다.

## 실행 이력 웹소켓

`/ws/runs?mode=<paper|backtest>`가 해당 모드 실행 이력의 변경을 화면에 보낸다. `app/records/events.py`의 `RunEvents`가 기록을 쓰는 러너 스레드에서 구독자의 이벤트 루프로 메시지를 넘긴다. 기록은 이 웹소켓과 상관없이 파일에 저장된다.

### 메시지

모두 JSON이고 `type`으로 구분한다. 연결하면 `ready`를 먼저 보낸다.

| `type` | 내용 |
| --- | --- |
| `ready` | 구독이 시작됨. **화면은 이 메시지를 받은 뒤 REST(`/api/runs`, 기록 조회)로 현재 상태를 조회한다.** 그 사이에 생긴 변경은 뒤이어 온다 |
| `run` | 실행의 시작·종료·상태 변경. `run`은 `/api/runs` 목록 항목과 같은 형식이고, 끝나기 전에는 `net_pnl`이 `null`이다 |
| `journal` | 기록 한 줄. `line`은 기록 조회(`/api/runs/.../journal`)의 항목과 같고, `seq`로 REST 결과와 겹침을 가린다 |
| `pnl` | 운용 중인 모의매매의 현재 순손익. `strategy_id`, `mode`, `run_id`, `net_pnl`(실현손익 − 수수료). 기록에는 남지 않는다 |
| `resync` | 화면이 느려 메시지를 버림. **화면이 REST로 다시 조회해야 한다** |

### 닫힘 코드

| 코드 | 뜻 |
| --- | --- |
| `4422` | `mode`가 `paper`나 `backtest`가 아님 |

### 동작

- 화면마다 대기열(1000개)이 있고 가득 차면 쌓인 메시지를 모두 버리고 `resync` 하나만 남긴다. 느린 화면이 러너를 막지 않는다.
- 백테스트는 봉마다 판단을 기록하므로 메시지가 많다. 백테스트 이력을 보는 화면은 이 웹소켓을 쓰지 않는다.

## 시세 조회

`app/nh/domestic/market.py`와 `app/api/market.py`가 화면에 쓸 종목 시세·차트·호가를 돌려준다. 국내 종목코드는 영문·숫자 6~16자여야 하고(`422`), 해외 종목은 `market=overseas`와 `exchange`(예: `FCME`)를 함께 보내야 한다(`exchange`가 없으면 `422`, 해외 키가 없으면 해외 변수 이름과 함께 `503`). 해외 종목은 `app/nh/overseas/quotes.py`의 시세를 쓰고 월물·만기·가격 제한·거래승수는 `null`이고 장 종류(`market_session`)는 NH 해외 장운영 조회의 거래시간(한국 시간, 예: `08:00 ~ 07:00`)으로 판정하며(`regular`·`closed`, 주말 휴장 반영, 공휴일·조기 마감 미반영, 조회에 실패하면 `unknown`, 거래시간은 1시간 보관)  호가는 5단계다. 실시간 체결·호가는 `/ws/market?market=overseas`로 받는다(아래 [실시간 시세 웹소켓](#실시간-시세-웹소켓)). NH 인증 정보가 없으면 `503`, NH가 거절하거나 조회에 실패하면 `502`다. 같은 요청이 몰려도 NH 호출 제한을 넘지 않도록 시세와 호가는 1초, 차트는 2초 동안 서버 메모리에 보관한다.

| 요청 | 내용 |
| --- | --- |
| `GET /api/market/<종목코드>/quote?market=&exchange=` | 종목명(`name`), 월물(`contract`, 최종거래일의 연·월, 예: `2026.11`), 만기(`expiry`), 현재가(`price`), 전일대비(`change`), 등락률(`change_rate`), 거래량(`volume`), 시가·고가·저가, 전일 종가(`prev_close`), 상·하한가, 거래승수(`multiplier`), 잔존일수, 장 종류(`market_session`: `before_open`·`auction`·`regular`·`closed`·`holiday`·`unknown`). 장 시간표는 `app/nh/domestic/market_hours.py`의 `SCHEDULES`에서 종목별로 정의한다 |
| `GET /api/market/<종목코드>/candles?interval=&count=&market=&exchange=` | 주간 분봉 또는 일봉을 오래된 순서로 돌려준다. `interval`은 `1`, `3`, `5`, `10`, `15`, `30`, `60`(분) 또는 `day`, `count`는 1~1000(기본 200). 항목은 `time`, `open`, `high`, `low`, `close`, `volume`이다 |
| `GET /api/market/<종목코드>/orderbook?market=&exchange=` | 호가 시각(`time`), 현재가, 등락률, 총매도·총매수 잔량, 10단계 `levels`(`ask_price`, `ask_quantity`, `bid_price`, `bid_quantity`) |

시세 세 API는 `legs=종목코드:비율,종목코드:비율`(예 `ZFZ26:3,ZNZ26:-2`)을 함께 받으면 두 종목을 합성한 스프레드를 돌려준다. 해외 종목(`market=overseas`, `exchange` 필요)에만 쓸 수 있고 종목코드는 `ZFZ26-ZNZ26`처럼 `-`를 허용한다(`422`). 현재가는 두 종목 현재가·전일 종가의 `Σ 비율 × 가격`, 거래량은 두 종목 중 작은 값이고, 월물·만기·가격 제한·거래승수는 `null`이다. 차트는 두 종목 봉을 시각별로 짝지은 스프레드 봉이며 고가·저가는 합친 시가·종가의 최댓값·최솟값이다. 호가는 `levels`가 빈 목록이다.

- 전일대비와 등락률은 NH의 부호 구분(`chg_sign`)이 `-`이면 음수로 돌려준다.
- 종목명은 NH 응답의 연속 공백을 하나로 줄인다(`삼성전자 F 202611 ( 10)`).
- 분봉의 `time`은 봉이 시작한 시각이고 날짜를 가리지 않고 최근 `count`개를 돌려준다. 일봉의 `time`은 날짜(`YYYY-MM-DD`)다. 일봉의 `volume`은 그날 거래량이다.
- 모의환경에서 확인한 값(2026-10-28): `A116B000`의 시세·호가·분봉(`1`, `5`)·일봉이 모두 조회된다. 호가는 장 마감 후에도 마지막 호가가 온다.
