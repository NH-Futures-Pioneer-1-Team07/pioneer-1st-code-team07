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
| `progress` | 백테스트만. 진행 상황 `{"stage": "prepare"\|"compute"\|"done", "done": n, "total": N}` |

`assumptions` 항목은 다음과 같다. 백테스트는 실행을 시작할 때 채우고, 호가 단위를 알게 되면 `slippage.tick_size`를 갱신한다.

| 항목 | 내용 |
| --- | --- |
| `fee` | `rate`(체결대금 대비 수수료율), `basis`(계산 기준), `source`(근거) |
| `slippage` | `ticks`(체결마다 더하는 틱 수), `tick_size`(호가 단위), `direction`(방향) |
| `fill` | 체결 시점·가격 기준. `on_bar`, `on_price`, `intrabar_path` |
| `margin` | 증거금 처리 |

## result.json

실행이 끝나면 쓴다. 이력 목록의 순손익은 `net_pnl`을 읽는다. 오류로 끝난 실행에는 없다.

백테스트의 `result.json` 필드는 다음과 같다.

| 필드 | 내용 |
| --- | --- |
| `initial_capital`, `final_equity` | 초기자금, 최종자산(`initial_capital + net_pnl`) |
| `gross_pnl`, `fee`, `net_pnl` | 총손익, 수수료 합계, 순손익(`gross_pnl - fee`) |
| `return_rate` | 순손익 / 초기자금 |
| `trade_count`, `win_count`, `loss_count` | 진입분 단위 거래 수, 순손익이 양수·음수인 거래 수 |
| `max_drawdown`, `max_drawdown_rate` | 봉 종가 기준 자산의 고점에서 저점까지의 최대 낙폭(금액, 고점 대비 비율) |
| `days`, `bars` | 계산한 날 수, 전략을 호출한 봉 수 |
| `equity_curve` | 하루마다 한 점 `{time, equity}`. 마지막 점은 기간 종료 청산까지 반영한 최종자산이다 |

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
| `decision` | 매매 판단 | `result`(buy, sell, hold, skip), `reason`, `quantity`, `price`, `score`, `detail`. 백테스트는 이 판단이 낸 주문을 `orders`(`side`, `quantity`, `entry_id`)로 함께 담는다 |
| `order` | 주문·취소 요청과 응답 | `side`, `quantity`, `order_type`, `entry_id`, `order_id`, `status`, `request`, `response` |
| `fill` | 체결 | `side`, `quantity`, `price`, `fee`, `order_id`, `entry_id`, `score`. 백테스트는 `raw_price`(슬리피지 전 가격), `intent`(entry·exit), `reason`, `source`를 더한다 |
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

### 백테스트가 남기는 기록

| `kind` | 필드 |
| --- | --- |
| `decision` | 전략이 돌려준 판단 그대로. `score`는 전략이 쓰지 않으면 `null` |
| `order` | `status`(`submitted`), `side`, `quantity`, `order_type`, `intent`, `entry_id`, `reason`. 시장가 주문은 모두 체결되므로 상태는 바뀌지 않는다 |
| `fill` | `source`는 체결 시점이다. `next_open`(봉 마감 판단을 다음 봉 시가에), `intrabar`(장중 가격 판단을 그 가격에), `day_end`(그날 마지막 봉 종가에), `backtest_end`(기간 종료 청산). `price`는 슬리피지를 반영한 값이다 |
| `trade` | 진입분 하나의 진입부터 청산까지. `entry_id`, `side`, `quantity`, `entry_price`(평균), `exit_price`(평균), `gross_pnl`, `fee`, `net_pnl`, `opened_at` |
| `event` | `일별 요약`(`day`, `equity`, `net_pnl`, `trades`), `백테스트 시작`, `백테스트 완료`, 경고·오류(`level`) |
