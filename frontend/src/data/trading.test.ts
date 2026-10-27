import test from "node:test";
import assert from "node:assert/strict";
import { instruments, strategies } from "./fixtures.ts";
import {
  accountSummary,
  beginStop,
  createTradingState,
  finishStop,
  remaining,
  startRun,
} from "./trading.ts";

test("운용은 한 번에 하나이며 지원하지 않는 종목으로 시작할 수 없다", () => {
  const initial = createTradingState();
  assert.equal(startRun(initial, strategies[0], instruments[1]), initial);
  const running = startRun(initial, strategies[0], instruments[0]);
  assert.equal(running.phase, "running");
  assert.equal(startRun(running, strategies[1], instruments[0]), running);
  assert.equal(initial.positions.length, 1);
});

test("운용 종료는 해당 운용만 정리하고 기존 계좌 주문과 포지션을 유지한다", () => {
  const running = startRun(createTradingState(), strategies[0], instruments[0]);
  const stopping = beginStop(running, false);
  assert.equal(stopping.phase, "stopping");
  assert.equal(startRun(stopping, strategies[0], instruments[0]), stopping);
  const done = finishStop(stopping);
  assert.equal(done.phase, "idle");
  assert.equal(done.positions.length, 1);
  assert.equal(done.positions[0].runId, null);
  assert.equal(
    done.orders
      .filter((order) => order.runId === running.activeRunId)
      .reduce((sum, order) => sum + remaining(order), 0),
    0,
  );
  assert.equal(
    done.orders.find((order) => order.id === "EXISTING-01")?.status,
    "미체결",
  );
  assert.ok(done.runs[0].endedAt);
  assert.ok(done.runs[0].fills.some((fill) => fill.orderId.endsWith("CLOSE")));
});

test("계좌 전체 정리는 운용 전후 모두 계좌 전체 잔량을 없앤다", () => {
  for (const state of [
    createTradingState(),
    startRun(createTradingState(), strategies[1], instruments[1]),
  ]) {
    const done = finishStop(beginStop(state, true));
    assert.equal(done.positions.length, 0);
    assert.equal(
      done.orders.reduce((sum, order) => sum + remaining(order), 0),
      0,
    );
    assert.equal(done.activeRunId, null);
    assert.equal(done.externalRealized, 8000);
  }
});

test("기존 포지션 청산은 평가손익을 현금으로 옮기며 반복 실행해도 중복 반영하지 않는다", () => {
  const initial = createTradingState();
  const beforeEquity =
    initial.externalRealized +
    initial.positions.reduce((sum, row) => sum + row.pnl, 0);
  const done = finishStop(beginStop(initial, true));
  assert.equal(
    done.externalRealized +
      done.positions.reduce((sum, row) => sum + row.pnl, 0),
    beforeEquity,
  );
  const twice = finishStop(beginStop(done, true));
  assert.equal(twice.externalRealized, done.externalRealized);
});

test("원주문 연결·체결 가격·판단 점수는 샘플 기록에서도 일치한다", () => {
  const state = startRun(createTradingState(), strategies[0], instruments[0]);
  const run = state.runs[0];
  for (const fill of run.fills) {
    const order = run.orders.find((row) => row.id === fill.orderId)!;
    assert.equal(fill.score, order.score);
    assert.equal(fill.price, order.price);
    assert.ok(fill.at >= order.at);
  }
  for (const order of run.orders.filter((row) => row.originalId)) {
    const original = run.orders.find((row) => row.id === order.originalId)!;
    assert.ok(order.at >= original.at);
    assert.equal(remaining(original), 0);
  }
  const position = state.positions.find((row) => row.runId === run.id)!;
  assert.equal(
    (position.price - position.average) * position.quantity * 10,
    position.pnl,
  );
});

test("운용 기록은 선택 전략과 구분되는 독립 스냅샷을 보관한다", () => {
  const strategy = {
    ...strategies[0],
    indicators: [...strategies[0].indicators],
  };
  const state = startRun(createTradingState(), strategy, instruments[0]);
  strategy.name = "다른 선택";
  strategy.indicators[0] = "변경";
  assert.equal(state.runs[0].strategy.name, strategies[0].name);
  assert.equal(
    state.runs[0].strategy.indicators[0],
    strategies[0].indicators[0],
  );
  assert.ok(state.runs[0].decisions.some((row) => row.action === "진입 보류"));
});

test("계좌 요약은 예탁현금·증거금·평가손익에서 자산과 주문 가능 금액을 계산한다", () => {
  const summary = accountSummary(createTradingState());
  assert.equal(summary.cash, 50_045_600);
  assert.equal(summary.margin, 1_200_000);
  assert.equal(summary.evaluation, 8_000);
  assert.equal(summary.assets, summary.cash + summary.evaluation);
  assert.equal(summary.orderable, summary.cash - summary.margin);
});
