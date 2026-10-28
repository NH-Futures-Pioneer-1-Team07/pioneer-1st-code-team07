# 삼성전자선물 역매매 전략

- 판단 규칙: [week02_samsung_futures_reversal.md](../../../docs/strategies/week02_samsung_futures_reversal.md)
- 구현: [strategy.py](strategy.py)
- 파라미터: [manifest.json](manifest.json). 이름과 기본값은 전략 문서 10절과 같다.
- 백테스트 설정: `manifest.json`의 `backtest`. 신호 봉은 3분봉, 가격 재현은 1분봉이다.
- 테스트: `tests/test_reversal_strategy.py`, `tests/test_minute_backtest.py`, `tests/test_reversal_service.py`

## 호출 방식

- `on_bar`: 3분봉이 마감될 때마다 호출한다. 후보·회복 확인, 목표 갱신, 시각 규칙을 처리한다. 진입 주문은 내지 않고 진입 의도를 상태에 남긴다.
- `on_price`: 가격이 갱신될 때마다 호출한다. 진입 의도의 첫 가격 검사, 손절·목표 확인, 시각 규칙을 처리한다.
- 같은 봉에는 `on_bar`를 한 번만 호출해야 한다.
- 백테스트와 모의매매는 같은 `Strategy` 클래스를 쓴다.
- `on_price`를 호출하지 않는 일반 백테스트 엔진에서는 진입하지 않는다. `backtest` 설정이 있어야 1분봉 가격 경로로 `on_price`를 호출한다.

## 구현 해석

전략 문서에 없는 부분을 다음과 같이 정했다.

| 항목 | 해석 |
| --- | --- |
| 진입 의도 | 확인 봉이 마감되면 상태의 `pending_entry`에 남긴다. 다음 `on_price`에서 한 번 검사하고 지운다. |
| 첫 가격 시한 | 확인 봉 마감 시각부터 1분 안의 첫 `on_price`만 검사한다. 조회 지연이 있어도 그 안이면 검사하고, 1분이 지나면 폐기한다. |
| 체결가 | 시장가 체결가는 검사한 가격과 다를 수 있다. 체결 뒤에도 최소 목표거리를 보장하지 않는다. |
| 봉 범위 | `ctx.bars` 중 `ctx.now`와 같은 날짜이고 `signal_start_time` 이후인 봉만 쓴다. 연속하지 않는 봉이 있으면 마지막 연속 구간만 쓴다. |
| 목표 갱신 | 갱신된 목표를 이미 지났으면 해당 봉 종가 기준으로 청산 주문을 내고, 청산은 다음 관측 가격에서 체결된다. |
| 청산 완료 | 15:30 청산과 최종거래일 청산은 잔여 수량이 없어져야 완료로 본다. |
| 청산 재시도 | 미체결·상태 불확실 청산 주문이 보호하는 수량은 다시 주문하지 않는다. 보호되지 않은 잔여 수량은 `on_price`에서 5초 간격으로 다시 청산한다. |
| 신규 진입 제한 시각 | 처음 호출될 때 `open_orders`를 모두 취소하고, 취소한 청산 주문의 남은 수량을 청산 주문으로 다시 낸다. 후보와 진입 의도를 지운다. |
| 판단 기록 | 호출마다 결과를 남긴다. 신호가 있으면 매수·매도, 신호가 없으면 보류, 신호를 건너뛰면 건너뜀과 이유를 남긴다. |

## 백테스트 가격 재현

- 신호는 3분봉으로 받고, 손절·목표·마감 감시와 평가액은 관측 1분봉으로 재현한다.
- 1분봉을 합친 값이 3분봉 OHLCV와 다르면 오류로 종료한다. 3분봉만으로 대체하지 않는다.
- 없는 분의 가격은 만들지 않고 다음 관측 가격에서 처리한다.
- 1분봉 안의 가격 순서는 시가, 보유 방향에 불리한 극단, 유리한 극단, 종가이다.
- 봉 마감 청산 주문은 다음 관측 1분봉 시가에 체결한다.
- 관측 가격 안에서 당일 청산을 끝내지 못하면 오류로 종료한다.

## 상태

`ctx.state`와 `StrategyOutput.state`로 다음을 주고받는다. 날짜가 바뀌면 초기화한다.

- `day`: 상태가 속한 날짜
- `entry_count`: 오늘 낸 진입 주문 수. 진입분 id(`<날짜>-<번호>`)에 쓴다.
- `candidate`: 확인을 기다리는 후보 봉(방향, 시각, 기준값, 목표)
- `pending_entry`: 첫 가격 검사를 기다리는 진입 의도
- `positions`: 진입분별 방향, 손절 기준, 이익 청산 목표, 정보 만료 시각
- `cutoff_done`, `flatten_started`, `flatten_done`, `final_exit_done`: 시각·날짜 규칙을 오늘 이미 처리했는지
- `flatten_retry_at`, `final_exit_retry_at`: 청산 재시도를 다시 할 수 있는 시각

## 테스트 실행

```bash
cd backend
uv run pytest tests/test_reversal_strategy.py tests/test_minute_backtest.py tests/test_reversal_service.py
```

- 테스트는 합성 봉과 임시 기록 디렉터리를 쓴다.
- 외부 API 호출이 필요 없다.
