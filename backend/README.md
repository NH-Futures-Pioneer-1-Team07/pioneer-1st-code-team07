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
