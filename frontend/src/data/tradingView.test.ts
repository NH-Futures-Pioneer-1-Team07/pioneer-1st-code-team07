import test from "node:test";
import assert from "node:assert/strict";
import {
  chartLayout,
  formatClock,
  formatDateTime,
  instrumentLabel,
  mapDecisions,
  mapFills,
  marketSessionLabel,
  phaseLabel,
  sideLabel,
  statusMessage,
  streamLabel,
  timeTicks,
} from "./tradingView.ts";
import type { Candle, JournalLine, TradingStatus } from "../apis/types.ts";

const line = (fields: Record<string, unknown>): JournalLine => ({ seq: 1, time: "2026-10-28T10:03:00+09:00", kind: "decision", ...fields });

test("서버의 한국 시간 문자열을 날짜와 시각이 있는 형식으로 바꾼다", () => {
  assert.equal(formatDateTime("2026-10-28T10:03:00+09:00"), "2026.10.28 10:03:00");
  assert.equal(formatDateTime("이상한 값"), "이상한 값");
  assert.equal(formatClock("100301"), "10:03:01");
  assert.equal(formatClock(""), "");
  assert.equal(formatClock(undefined), "");
});

test("매매구분과 단계 이름", () => {
  assert.equal(sideLabel("buy"), "매수");
  assert.equal(sideLabel("sell"), "매도");
  assert.equal(sideLabel(null), "");
  assert.equal(phaseLabel("running"), "운용 중");
  assert.equal(phaseLabel("stopping"), "정리 중");
  assert.equal(phaseLabel("clearing"), "정리 중");
  assert.equal(phaseLabel("idle"), "대기");
});

test("매매 판단 기록을 화면 행으로 바꾼다", () => {
  const rows = mapDecisions([
    line({ seq: 1, result: "buy", reason: "상승 추세에서 기준 고점 돌파", orders: [{ side: "buy", quantity: 12, entry_id: "a" }] }),
    line({ seq: 2, result: "hold", reason: "돌파 없음", score: null, orders: [] }),
    line({ seq: 3, result: "skip", reason: "평균 거래량이 0", score: 0.5 }),
  ]);
  assert.deepEqual(rows[0], {
    key: "1", at: "2026.10.28 10:03:00", action: "매수", reason: "상승 추세에서 기준 고점 돌파",
    price: null, quantity: 12, score: null,
  });
  assert.equal(rows[1].action, "진입 보류");
  assert.equal(rows[1].quantity, null);
  assert.equal(rows[2].action, "건너뜀");
  assert.equal(rows[2].score, 0.5);
});

test("체결 기록을 화면 행으로 바꾼다", () => {
  const [row] = mapFills([line({ seq: 7, kind: "fill", side: "sell", quantity: 3, price: 243500, fee: 62, score: null })]);
  assert.deepEqual(row, { key: "7", at: "2026.10.28 10:03:00", side: "매도", quantity: 3, price: 243500, fee: 62, score: null });
});

const status = (fields: Partial<TradingStatus>): TradingStatus => ({ phase: "idle", run: null, ...fields });

test("상태 줄은 방금 한 동작의 오류를 먼저 보여 준다", () => {
  assert.equal(statusMessage(status({}), "이미 운용 중인 전략이 있습니다"), "이미 운용 중인 전략이 있습니다");
  assert.equal(statusMessage(null, null), "");
  assert.equal(statusMessage(status({}), null), "");
});

test("상태 줄은 단계와 차단 사유와 정리 결과를 알려 준다", () => {
  assert.match(statusMessage(status({ phase: "running", entry_blocks: [] }), null), /운용 중/);
  assert.match(statusMessage(status({ phase: "running", entry_blocks: ["분봉 조회가 계속 실패함"] }), null), /분봉 조회가 계속 실패함/);
  assert.match(statusMessage(status({ phase: "stopping" }), null), /종료하는 중/);
  const running = { state: "running" as const, step: "cancel", detail: "미체결을 취소합니다", result: null };
  assert.match(statusMessage(status({ phase: "clearing", clear: running }), null), /계좌 전체 정리 중: 미체결을 취소합니다/);
  const done = (result: NonNullable<TradingStatus["clear"]>["result"]) =>
    statusMessage(status({ clear: { state: "done", step: "done", detail: "", result } }), null);
  assert.match(done({ status: "completed", open_orders: [], positions: [], cancelled: 2, problems: [] }), /마쳤습니다.*2건/);
  const left = done({ status: "incomplete", open_orders: [], positions: [{} as never], cancelled: 0, problems: ["시간 초과"] });
  assert.match(left, /끝나지 않았습니다.*보유 1건.*시간 초과/);
  assert.match(statusMessage(status({ last_run: { strategy_id: "a", mode: "paper", run_id: "r", status: "error" } }), null), /오류로 끝났습니다/);
});

const candle = (time: string, open: number, high: number, low: number, close: number, volume: number): Candle => ({
  time, open, high, low, close, volume,
});

test("캔들 배치는 오른쪽 눈금 자리를 남기고 가격이 높을수록 위에 놓는다", () => {
  const layout = chartLayout(
    [candle("2026-10-28T09:00:00", 100, 110, 95, 105, 10), candle("2026-10-28T09:03:00", 105, 108, 90, 92, 40)],
    476, 270, 76,
  );
  assert.equal(layout.shapes.length, 2);
  const [first, second] = layout.shapes;
  assert.ok(first.x >= 0 && second.x + second.width <= 400);
  assert.ok(first.wickTop < first.wickBottom);
  assert.equal(first.rising, true);
  assert.equal(second.rising, false);
  assert.ok(first.wickTop < second.wickBottom && layout.min === 90 && layout.max === 110);
  assert.ok(second.volumeHeight > first.volumeHeight);
  assert.equal(layout.ticks.length, 4);
  assert.ok(layout.ticks[0].y < layout.ticks[3].y && layout.ticks[0].value === 110);
  assert.equal(layout.lastY! > 0, true);
});

test("시가가 없는 봉은 앞 봉 종가를 시가로 보고 값이 모두 같아도 그려진다", () => {
  const flat = chartLayout([candle("2026-10-28T09:00:00", 100, 100, 100, 100, 5)], 300, 200, 76);
  assert.equal(flat.shapes.length, 1);
  assert.ok(Number.isFinite(flat.shapes[0].bodyTop) && flat.shapes[0].bodyHeight >= 1.5);
  const noOpen = chartLayout(
    [candle("a", 100, 101, 99, 100, 1), { time: "b", open: null, high: 103, low: 100, close: 102, volume: 1 }], 300, 200, 76);
  assert.equal(noOpen.shapes[1].rising, true);
  assert.deepEqual(chartLayout([], 300, 200, 76).shapes, []);
});

test("시각 눈금은 분봉이면 시:분, 일봉이면 월.일이다", () => {
  const minutes = ["09:00", "09:30", "10:00", "10:30"].map((t) => candle(`2026-10-28T${t}:00`, 1, 1, 1, 1, 1));
  assert.deepEqual(timeTicks(minutes, false).map((t) => t.label), ["09:00", "09:30", "10:00", "10:30"]);
  const days = [candle("2026-10-26", 1, 1, 1, 1, 1), candle("2026-10-27", 1, 1, 1, 1, 1)];
  assert.deepEqual(timeTicks(days, true).map((t) => t.label), ["10.26", "10.27"]);
  assert.deepEqual(timeTicks([], false), []);
});

test("종목 이름을 이름 · 월물 형식으로 맞춘다", () => {
  assert.equal(instrumentLabel("삼성전자 F 202611 ( 10)"), "삼성전자 선물 · 2026.11");
  assert.equal(instrumentLabel("삼성전자선물 2026년 11월물"), "삼성전자 선물 · 2026.11");
  assert.equal(instrumentLabel("삼성전자선물 2026년 9월물"), "삼성전자 선물 · 2026.09");
  assert.equal(instrumentLabel("A116B000"), "A116B000");
});

test("장 종류를 한글로 보여 주고 모르는 값은 장 정보 없음으로 둔다", () => {
  assert.equal(marketSessionLabel("regular"), "정규장");
  assert.equal(marketSessionLabel("auction"), "동시호가");
  assert.equal(marketSessionLabel("holiday"), "휴장");
  assert.equal(marketSessionLabel(undefined), "장 정보 없음");
});

test("시세 연결 문구는 연결 여부만 말한다", () => {
  assert.equal(streamLabel("live", null), "시세 연결됨");
  assert.equal(streamLabel("connecting", null), "시세 연결 중");
  assert.equal(streamLabel("disconnected", "연결이 거부되었습니다 (1006)"), "시세 연결 끊김: 연결이 거부되었습니다 (1006)");
});
