import test from "node:test";
import assert from "node:assert/strict";
import {
  defaultPeriod,
  equityLayout,
  percentText,
  progressLabel,
  progressPercent,
  returnText,
  validateInput,
} from "./backtestView.ts";

const range = {
  strategy_id: "s",
  instrument: { name: "x", code: "A" },
  start: "2026-08-14",
  end: "2026-10-27",
  last_trading_day: "2026-11-12",
};

test("진행률은 데이터 준비가 앞 절반, 계산이 뒤 절반이다", () => {
  assert.equal(progressPercent(undefined, "running"), 0);
  assert.equal(progressPercent({ stage: "prepare", done: 5, total: 10 }, "running"), 25);
  assert.equal(progressPercent({ stage: "compute", done: 5, total: 10 }, "running"), 75);
  assert.equal(progressPercent({ stage: "done", done: 10, total: 10 }, "running"), 100);
  assert.equal(progressPercent({ stage: "prepare", done: 0, total: 0 }, "completed"), 100);
});

test("진행 문구는 단계와 일 수를 보여 준다", () => {
  assert.match(progressLabel({ stage: "prepare", done: 3, total: 9 }), /3\/9일/);
  assert.match(progressLabel({ stage: "compute", done: 4, total: 9 }), /계산/);
  assert.match(progressLabel(undefined), /시작/);
});

test("입력 검증은 기간·가능 범위·초기자금을 확인한다", () => {
  assert.equal(validateInput("2026-10-01", "2026-10-27", "50000000", range), "");
  assert.match(validateInput("2026-10-10", "2026-10-01", "50000000", range), /시작일/);
  assert.match(validateInput("2026-08-01", "2026-10-01", "50000000", range), /2026-08-14/);
  assert.match(validateInput("2026-10-01", "2026-10-28", "50000000", range), /2026-10-27/);
  assert.match(validateInput("2026-10-01", "2026-10-27", "500", range), /초기자금/);
  assert.match(validateInput("2026-10-01", "2026-10-27", "1000000.5", range), /초기자금/);
  assert.match(validateInput("2026-10-01", "2026-10-27", "50000000", null), /가능 기간/);
});

test("수수료율과 수익률 표기", () => {
  assert.equal(percentText(0.000085), "0.0085%");
  assert.equal(returnText(0.0123), "+1.23%");
  assert.equal(returnText(-0.05), "-5.00%");
});

test("자산 곡선은 높은 값이 위에 오고 값이 같으면 가운데에 그린다", () => {
  const box = { left: 0, right: 100, top: 0, bottom: 60, baseline: 80 };
  const layout = equityLayout([{ equity: 100 }, { equity: 200 }], box);
  assert.equal(layout.line, "0,60 100,0");
  assert.deepEqual(layout.last, { x: 100, y: 0 });
  assert.equal(layout.ticks[0].value, 200);
  assert.equal(layout.ticks[3].value, 100);
  const flat = equityLayout([{ equity: 5 }, { equity: 5 }], box);
  assert.equal(flat.line, "0,30 100,30");
  assert.equal(equityLayout([], box).last, null);
});

test("처음 기간은 가능 기간의 마지막 7일이고 시작보다 앞서지 않는다", () => {
  assert.deepEqual(defaultPeriod(range), { start: "2026-10-21", end: "2026-10-27" });
  assert.deepEqual(defaultPeriod({ ...range, start: "2026-10-25" }), { start: "2026-10-25", end: "2026-10-27" });
  assert.equal(defaultPeriod(null), null);
});
