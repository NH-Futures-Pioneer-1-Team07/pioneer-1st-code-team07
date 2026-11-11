# Z3N·ZN 미국 국채선물 스프레드 전략

- 전략 문서: [week04_z3n_zn_spread.md](../../../docs/strategies/week04_z3n_zn_spread.md)
- [ZF·ZN 스프레드 전략](../week04_zf_zn_spread/README.md)에서 5년물을 3년물로 바꾼 전략이다. `strategy.py`의 판단 규칙과 파라미터는 같고, 기록이 남은 기존 전략은 고치지 않고 폴더를 복사해 만들었다.

## 구현 메모

- 종목은 `Z3NZ26`(ratio 1, weight 2)과 `ZNZ26`(ratio -1)로 이루어진 스프레드 한 개다(`instruments[0].legs`). 계약은 1:1이다.
- `ratio`는 계약 수와 주문 방향, `weight`는 스프레드 가격 합성에 쓴다. Z3N은 1포인트 2,000 USD, ZN은 1,000 USD라 스프레드 승수 1,000 기준으로 `weight = ratio × 종목 승수 ÷ 1,000`이다. 스프레드 가격은 `2 × Z3NZ26 − 1 × ZNZ26`이다.
- 거래승수 1,000, 증거금 4,063 USD(Z3N 약 2,000 추정 + ZN 2,063), `tick_size` 0.0234375(`2 × 0.00390625 + 0.015625`, 두 종목이 1호가씩 불리하게 체결되는 폭)는 한 세트 기준이다.
- 백테스트 수수료는 두 종목 체결대금의 합(`2 × Z3N + 1 × ZN`의 기간 평균 가격)으로 계산한다.
- **데이터 제약**: NH 모의 서버에서 `Z3NZ26`은 일봉이 없고 5분봉이 듬성하다. 일봉이 비면 `app/runners/series.py`의 `daily_from_minutes`로 두 종목 모두 5분봉에서 일봉을 합성한다(`nh_daily_fetcher(...).from_minutes`, `spread_daily_fetcher`가 선택). 합성 일봉 쌍은 61개(2026-08-18부터)라 `window_days`를 40 이하로 둔다. 일봉 쌍이 `window_days`개 모이기 전에는 판단을 보류한다.
