# 실행 기록

백테스트와 모의매매를 실행할 때마다 이 폴더에 기록이 한 묶음씩 남는다.
이 폴더는 그대로 커밋한다. 제출 저장소로 옮길 때는 필요한 실행 폴더만 가져간다.

## 폴더 구조

```
runs/<전략 id>/<backtest|paper>/<실행 일시>/
├─ meta.json              실행 정보
├─ result.json            실행이 끝나면 쓰는 최종 요약
└─ journal/<날짜>.jsonl   날짜별 기록. 한 줄이 한 사건
```

| 경로 | 뜻 |
| --- | --- |
| `<전략 id>` | `backend/strategies/` 아래 전략 폴더 이름 |
| `backtest` / `paper` | 백테스트 / 모의매매 |
| `<실행 일시>` | 실행을 시작한 한국 시간. `20261028_093012` 형식. 같은 초에 시작하면 `-1`, `-2`가 붙는다 |
| `<날짜>` | 기록 시각의 한국 시간 날짜. `2026-10-27` 형식 |

## 전략 버전 규칙

- 기록이 남은 전략은 고치지 않는다.
- 전략을 바꿀 때는 전략 폴더를 복사해 새 이름으로 만든다. 예: `week02_samsung_futures_intraday` → `week02_samsung_futures_intraday_v2`
- 옛 전략 폴더와 그 전략의 기록은 그대로 둔다.
- 기록 경로의 전략 id가 그 기록을 만든 전략 코드를 가리킨다.

## meta.json

| 필드 | 내용 |
| --- | --- |
| `run_id` | 실행 일시 폴더 이름 |
| `strategy_id`, `strategy_name` | 전략 폴더 이름, 화면에 표시하는 이름 |
| `mode` | `backtest` 또는 `paper` |
| `instrument` | 종목(`name`, `code`) |
| `params` | 실행에 쓴 파라미터 값 |
| `started_at`, `ended_at` | 시작·종료 시각. 종료 전에는 `ended_at`이 `null` |
| `status` | `running`(실행 중), `completed`(완료), `interrupted`(서버가 멈춰 중단), `error`(오류로 끝남) |
| `period` | 백테스트만. 테스트 대상 `start`, `end` 날짜 |
| `initial_capital` | 백테스트만. 초기자금 |
| `assumptions` | 백테스트만. 비용·체결 가정 |

`assumptions` 항목은 다음과 같다. 값은 백테스트 실행 기능이 채우며, 채우지 않으면 `null`이다.

| 항목 | 내용 |
| --- | --- |
| `fee` | 수수료율 |
| `slippage` | 슬리피지 |
| `fill` | 체결 시점·가격 기준 |

## result.json

실행이 끝나면 쓴다. 필드는 실행 기능이 정한다. 이력 목록의 순손익은 `net_pnl`을 읽는다.

## journal

한 줄이 한 사건이고, 시간순으로 덧붙는다. 모든 줄에 다음 필드가 있다.

| 필드 | 내용 |
| --- | --- |
| `run_id` | 실행 일시 |
| `strategy_id` | 전략 id |
| `mode` | `backtest` 또는 `paper` |
| `seq` | 실행 안에서 1부터 늘어나는 순번 |
| `time` | 사건 시각. 한국 시간 ISO 형식 |
| `kind` | 기록 종류 |

### 기록 종류

종류마다 나머지 필드가 다르다. 아래는 쓰기로 한 필드이고, 실행 기능이 필요한 필드를 더할 수 있다.

| `kind` | 뜻 | 주요 필드 |
| --- | --- | --- |
| `decision` | 매매 판단 | `result`(buy, sell, hold, skip), `reason`, `quantity`, `price`, `score`, `detail` |
| `order` | 주문·취소 요청과 응답 | `side`, `quantity`, `order_type`, `entry_id`, `order_id`, `status`, `request`, `response` |
| `fill` | 체결 | `side`, `quantity`, `price`, `fee`, `order_id`, `entry_id`, `score` |
| `trade` | 진입부터 청산까지 한 건 | `entry_id`, `side`, `quantity`, `entry_price`, `exit_price`, `gross_pnl`, `fee`, `net_pnl` |
| `event` | 시작·종료, 오류, 상태 변화 | `text`, `level` |

## 비밀정보

- 키, 토큰, 비밀번호, 계좌번호 필드는 기록기가 쓰기 전에 지운다. 키 이름에 `appkey`, `secret`, `token`, `password`, `authorization`, `accountno`, `계좌` 등이 들어 있으면 지운다.
- 값만 보고 거르지는 않는다. 비밀정보를 키 이름 없이 문자열 안에 넣어 기록하지 않는다.
- 커밋하기 전에 기록에 비밀정보가 없는지 확인한다.

## 조회 API

| 요청 | 내용 |
| --- | --- |
| `GET /api/runs?mode=&strategy_id=` | 실행 목록. 최근에 시작한 순서 |
| `GET /api/runs/<전략 id>/<모드>/<실행 일시>` | 실행 정보(`meta`)와 결과(`result`) |
| `GET /api/runs/<전략 id>/<모드>/<실행 일시>/journal?kind=&start=&end=&offset=&limit=` | 기록. `end`는 포함하지 않는다 |
