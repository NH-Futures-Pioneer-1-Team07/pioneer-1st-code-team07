# week2 전략 코드 보관

`week3` 작업에서 `backend/strategies/`에서 삭제한 week2 전략 코드를 `dev`의 삭제 전 내용 그대로 보관한다.

| 전략 | 폴더 | 전략 문서 |
|---|---|---|
| 삼성전자선물 장중 전략 | [week02_samsung_futures_intraday](strategies/week02_samsung_futures_intraday) | [week02_samsung_futures_intraday.md](../../week02_samsung_futures_intraday.md) |
| 삼성전자선물 역매매 전략 | [week02_samsung_futures_reversal](strategies/week02_samsung_futures_reversal) | [week02_samsung_futures_reversal.md](../../week02_samsung_futures_reversal.md) |

## 구성

| 경로 | 내용 |
|---|---|
| `strategies/<전략 id>/` | 전략 폴더(`manifest.json`, `strategy.py`, `README.md`). 폴더 이름이 전략 id다 |
| `tests/` | 두 전략 전용 테스트 4개(`test_intraday_strategy.py`, `test_reversal_strategy.py`, `test_reversal_service.py`, `test_backtest_strategies.py`) |

## 다시 쓰는 방법

저장소 루트에서 실행한다.

```bash
cp -R docs/strategies/archive/week02/strategies/week02_* backend/strategies/
```

```bash
cp docs/strategies/archive/week02/tests/*.py backend/tests/
```

```bash
cd backend && uv run pytest
```

- 서버를 다시 시작하면 `GET /api/strategies`에 나타난다.
- 전략 id를 바꾸지 않고 옮기면 `backend/runs/`에 남아 있는 week2 실행 기록과 이어진다.
- 기록이 남은 전략은 고치지 않는다. 바꾸려면 폴더를 복사해 새 이름으로 만든다.
- 전략 폴더는 `backend/strategies/`에서 지우고, 테스트는 `backend/tests/`에서 지우면 다시 보관 상태가 된다.

## 확인한 내용

- 2026-11-04 `week3` 브랜치에서 위 방법으로 복사했을 때 서버 레지스트리가 두 전략을 오류 없이 등록했고 보관한 테스트와 관련 테스트 66개가 통과했다.
- 이후 `strategy_base`(`Context`, 매니페스트 형식)나 러너가 바뀌면 복원할 때 수정이 필요할 수 있다. 복원 후 위 테스트로 확인한다.
