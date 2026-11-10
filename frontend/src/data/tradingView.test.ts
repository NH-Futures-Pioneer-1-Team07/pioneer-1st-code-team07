import test from "node:test";
import assert from "node:assert/strict";
import {
  chartLayout,
  formatClock,
  flattenDetail,
  linesForInterval,
  lineValues,
  movingAverage,
  levelLines,
  resolveLines,
  showsLevels,
  formatDateTime,
  instrumentLabel,
  mapDecisions,
  mapFills,
  marketSessionLabel,
  phaseLabel,
  sideLabel,
  statusMessage,
  runKey,
  runStatusLabel,
  runStreamLabel,
  marketNameLabel,
  streamLabel,
  timeTicks,
  upsertRun,
} from "./tradingView.ts";
import type { Candle, JournalLine, RunSummary, TradingStatus } from "../apis/types.ts";

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
    line({ seq: 2, result: "hold", reason: "돌파 없음", orders: [] }),
    line({ seq: 3, result: "skip", reason: "평균 거래량이 0" }),
  ]);
  assert.deepEqual(rows[0], {
    key: "1", at: "2026.10.28 10:03:00", action: "매수", reason: "상승 추세에서 기준 고점 돌파",
    detail: [], price: null, quantity: 12,
  });
  assert.equal(rows[1].action, "진입 보류");
  assert.equal(rows[1].quantity, null);
  assert.equal(rows[2].action, "건너뜀");
});

test("체결 기록을 화면 행으로 바꾼다", () => {
  const [row] = mapFills([line({ seq: 7, kind: "fill", side: "sell", quantity: 3, price: 243500, fee: 62 })]);
  assert.deepEqual(row, { key: "7", at: "2026.10.28 10:03:00", side: "매도", quantity: 3, price: 243500, fee: 62, reason: "" });
});

test("판단 기록은 근거 수치를 줄로 펼치고 체결 기록은 사유를 담는다", () => {
  const [row] = mapDecisions([
    line({
      seq: 1,
      result: "hold",
      reason: "교차 없음",
      detail: { mid: { signal: "buy", close: 106.640625, short_ma: null }, intraday: { cross: null, position: "above" }, today: { entered: 0, rates: [1, 2] } },
    }),
  ]);
  assert.deepEqual(row.detail, [
    "mid.signal: buy",
    "mid.close: 106.640625",
    "intraday.position: above",
    "today.entered: 0",
    "today.rates: 1, 2",
  ]);
  const [fill] = mapFills([line({ seq: 2, kind: "fill", side: "buy", quantity: 1, price: 106.5, reason: "장중 이동평균 교차 (중기 매수 허용)" })]);
  assert.equal(fill.reason, "장중 이동평균 교차 (중기 매수 허용)");
  assert.deepEqual(flattenDetail(undefined), []);
  assert.deepEqual(flattenDetail({ a: 1.23456789 }), ["a: 1.234568"]);
});

const status = (fields: Partial<TradingStatus>): TradingStatus => ({ phase: "idle", run: null, ...fields });

test("상태 줄은 방금 한 동작의 오류를 먼저 보여 준다", () => {
  assert.equal(statusMessage(status({}), "이미 운용 중인 전략이 있습니다"), "이미 운용 중인 전략이 있습니다");
  assert.equal(statusMessage(null, null), "");
  assert.equal(statusMessage(status({}), null), "");
});

test("상태 줄은 단계와 차단 사유와 정리 결과를 알려 준다", () => {
  assert.equal(statusMessage(status({ phase: "running", entry_blocks: [] }), null), "");
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

test("상단바는 종목의 시장에 따라 국내장·해외장을 구분한다", () => {
  assert.equal(marketNameLabel("overseas"), "해외장");
  assert.equal(marketNameLabel("domestic"), "국내장");
  assert.equal(marketNameLabel(null), "국내장");
});

test("시세 연결 문구는 연결 여부만 말한다", () => {
  assert.equal(streamLabel("live", null), "시세 연결됨");
  assert.equal(streamLabel("connecting", null), "시세 연결 중");
  assert.equal(streamLabel("disconnected", "연결이 거부되었습니다 (1006)"), "시세 연결 끊김: 연결이 거부되었습니다 (1006)");
});

test("이력 연결 문구는 웹소켓 연결 여부를 말한다", () => {
  assert.equal(runStreamLabel("live"), "이력 실시간 연결됨");
  assert.equal(runStreamLabel("connecting"), "이력 연결 중");
  assert.equal(runStreamLabel("disconnected"), "이력 연결 끊김");
});

const summary = (run_id: string, started_at: string, fields: Partial<RunSummary> = {}): RunSummary => ({
  strategy_id: "s", mode: "paper", run_id, strategy_name: "전략", instrument: { name: "선물", code: "A1" },
  started_at, ended_at: null, status: "running", net_pnl: null, ...fields,
});

test("운용 상태 문구는 끝났는지와 종료 사유로 정한다", () => {
  assert.equal(runStatusLabel({ ended_at: null, status: "running" }), "운용 중");
  assert.equal(runStatusLabel({ ended_at: "2026-10-29T15:00:00", status: "completed" }), "종료");
  assert.equal(runStatusLabel({ ended_at: "2026-10-29T15:00:00", status: "error" }), "오류");
  assert.equal(runStatusLabel({ ended_at: "2026-10-29T15:00:00", status: "interrupted" }), "중단");
  assert.equal(runStatusLabel({ ended_at: null, status: "interrupted" }), "중단");
});

test("실행 목록에 넣으면 같은 실행은 바꾸고 최근에 시작한 것이 앞에 온다", () => {
  const first = summary("a", "2026-10-29T09:00:00");
  const second = summary("b", "2026-10-29T10:00:00");
  assert.equal(runKey(first), "s/a");
  assert.deepEqual(upsertRun([first], second).map((run) => run.run_id), ["b", "a"]);
  const finished = summary("a", "2026-10-29T09:00:00", { status: "completed", net_pnl: 5 });
  const merged = upsertRun([second, first], finished);
  assert.deepEqual(merged.map((run) => run.run_id), ["b", "a"]);
  assert.equal(merged[1].net_pnl, 5);
});


const closes = (values: number[], day = "2026-11-0") =>
  values.map((close, index): Candle => ({ time: `${day}${index + 1}`, open: close, high: close, low: close, close, volume: 1 }));

test("이동평균은 기간이 모이기 전 자리를 비워 둔다", () => {
  assert.deepEqual(movingAverage(closes([1, 2, 3, 4]), 3), [null, null, 2, 3]);
  assert.deepEqual(movingAverage(closes([5]), 1), [5]);
  assert.deepEqual(movingAverage([], 3), []);
});

test("직전 거래일 종가선은 오늘보다 앞선 마지막 일봉의 종가다", () => {
  const candles = closes([10, 11, 12]); // 2026-11-01, 02, 03
  const line = { series: "daily", kind: "previous_close", period: null, label: "직전 거래일 종가", description: "" } as const;
  assert.deepEqual(lineValues(line, candles, "2026-11-04"), [12, 12, 12]); // 오늘(4일) 일봉이 아직 없으면 마지막 일봉
  assert.deepEqual(lineValues(line, candles, "2026-11-03"), [11, 11, 11]); // 오늘 일봉은 제외
  assert.deepEqual(lineValues(line, candles, "2026-11-01"), [null, null, null]);
});

test("차트 주기에 맞는 선만 고르고 이동평균 선에는 색을 돌려가며 준다", () => {
  const specs = [
    { series: "daily", kind: "previous_close", period: null, label: "직전", description: "d" },
    { series: "daily", kind: "sma", period: 2, label: "2일선", description: "d" },
    { series: "bar", kind: "sma", period: 2, label: "단기선", description: "d" },
    { series: "bar", kind: "sma", period: 3, label: "장기선", description: "d" },
  ] as const;

  assert.deepEqual(linesForInterval([...specs], "day", 5).map((l) => l.label), ["직전", "2일선"]);
  assert.deepEqual(linesForInterval([...specs], "5", 5).map((l) => l.label), ["단기선", "장기선"]);
  assert.deepEqual(linesForInterval([...specs], "1", 5), []);
  assert.deepEqual(linesForInterval([...specs], "5", null), []);

  const resolved = resolveLines(linesForInterval([...specs], "5", 5), closes([1, 2, 3, 4]), "2026-11-04");
  assert.equal(resolved[0].latest, 3.5);
  assert.equal(resolved[1].latest, 3);
  assert.notEqual(resolved[0].color, resolved[1].color);
});

test("전략이 내려준 경계는 차트 전체에 걸친 수평선이 된다", () => {
  const candles = [1, 2, 3].map((close, index) => ({
    time: `2026-11-11T09:0${index}:00`,
    open: close,
    high: close,
    low: close,
    close,
    volume: 1,
  }));
  const lines = levelLines(
    [
      { label: "진입 상단", value: 103.9, description: "상단" },
      { label: "진입 하단", value: 100, description: "하단" },
    ],
    candles,
  );
  assert.deepEqual(lines.map((line) => line.spec.label), ["진입 상단", "진입 하단"]);
  assert.deepEqual(lines[0].values, [103.9, 103.9, 103.9]);
  assert.equal(lines[0].latest, 103.9);
  assert.equal(lines[0].spec.kind, "level");
  assert.notEqual(lines[0].color, lines[1].color);
});

test("경계선은 판단 기준 봉과 일봉 차트에만 그린다", () => {
  assert.equal(showsLevels("5", 5), true);
  assert.equal(showsLevels("day", 5), true);
  assert.equal(showsLevels("1", 5), false);
  assert.equal(showsLevels("5", null), false);
});

test("종목코드의 월물을 읽어 만기 안내 문구를 만든다", async () => {
  const { contractMonth, expiryNote } = await import("./tradingView.ts");
  assert.equal(contractMonth("ZFZ26"), "2026년 12월물");
  assert.equal(contractMonth("ZNH27"), "2027년 3월물");
  assert.equal(contractMonth("A116B000"), null);
  assert.equal(expiryNote(["ZFZ26", "ZNZ26"]), "ZFZ26·ZNZ26은 2026년 12월물입니다. 만기 전에 직접 운용을 종료하세요.");
  assert.equal(expiryNote(["ZFZ26", "ZNH27"]), "ZFZ26 2026년 12월물, ZNH27 2027년 3월물입니다. 만기 전에 직접 운용을 종료하세요.");
  assert.equal(expiryNote(["A116B000"]), null);
});
