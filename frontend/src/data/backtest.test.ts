import test from "node:test";
import assert from "node:assert/strict";
import {
  instruments,
  strategies,
  strategyById,
  supportedInstruments,
} from "./fixtures.ts";
import { sampleRecord } from "./backtest.ts";

test("전략이 지원하는 종목만 돌려주고 알 수 없는 전략은 첫 전략으로 대체한다", () => {
  const samsungOnly = strategies.find((item) => item.symbols.length === 1)!;
  assert.deepEqual(
    supportedInstruments(samsungOnly).map((item) => item.id),
    samsungOnly.symbols,
  );
  assert.equal(strategyById("없는-전략"), strategies[0]);
});

test("백테스트 샘플 기록의 손익은 체결가 차이·승수·수량에서 비용을 뺀 값이다", () => {
  const record = sampleRecord(
    "test",
    "2026.10.27 09:50",
    strategies[0],
    instruments[0],
    "2026-10-01",
    "2026-10-27",
    50_000_000,
  );
  const gross =
    (record.exitPrice - record.entryPrice) *
    record.multiplier *
    record.quantity;
  assert.equal(record.profit, Math.round(gross - record.cost));
  assert.equal(record.cost, record.quantity * record.feePerContract * 2);
  assert.equal(record.strategyName, strategies[0].name);
});
