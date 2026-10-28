import test from "node:test";
import assert from "node:assert/strict";
import {
  defaultPeriod,
  equityPoints,
  koreanAmount,
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
  assert.equal(validateInput("2026-10-01", "2026-10-27", "50000000", range, "0"), "");
  assert.equal(validateInput("2026-10-01", "2026-10-27", "50000000", range, "20"), "");
  assert.match(validateInput("2026-10-01", "2026-10-27", "50000000", range, "21"), /슬리피지/);
  assert.match(validateInput("2026-10-01", "2026-10-27", "50000000", range, ""), /슬리피지/);
});

test("수수료율과 수익률 표기", () => {
  assert.equal(percentText(0.000085), "0.0085%");
  assert.equal(returnText(0.0123), "+1.23%");
  assert.equal(returnText(-0.05), "-5.00%");
});

test("자산 곡선의 날짜마다 그날의 체결과 전날 대비 손익을 붙인다", () => {
  const curve = [
    { time: "2026-08-14T15:03:00", equity: 1000 },
    { time: "2026-08-18T15:03:00", equity: 1300 },
    { time: "2026-08-19T15:03:00", equity: 1100 },
  ];
  const fill = (time: string, side: string) => ({
    seq: 1,
    kind: "fill",
    time,
    side,
    quantity: 2,
    price: 250,
    reason: "당일 청산",
  });
  const points = equityPoints(curve, 1000, [
    fill("2026-08-18T10:15:00+09:00", "buy"),
    fill("2026-08-18T15:30:00+09:00", "sell"),
    fill("2026-08-20T10:00:00+09:00", "buy"),
  ]);
  assert.deepEqual(
    points.map((point) => [point.day, point.change, point.fills.length]),
    [
      ["2026-08-14", 0, 0],
      ["2026-08-18", 300, 2],
      ["2026-08-19", -200, 0],
    ],
  );
  assert.deepEqual(points[1].fills[0], { time: "10:15", side: "buy", quantity: 2, price: 250, reason: "당일 청산" });
  assert.equal(points[1].bar, null);
  const bar = { date: "2026-08-18", open: 250, high: 260, low: 240, close: 255, volume: 10 };
  const withBars = equityPoints(curve, 1000, [], [bar]);
  assert.deepEqual(withBars.map((point) => point.bar), [null, bar, null]);
  assert.deepEqual(equityPoints([], 1000, []), []);
});

test("처음 기간은 가능 기간의 마지막 7일이고 시작보다 앞서지 않는다", () => {
  assert.deepEqual(defaultPeriod(range), { start: "2026-10-21", end: "2026-10-27" });
  assert.deepEqual(defaultPeriod({ ...range, start: "2026-10-25" }), { start: "2026-10-25", end: "2026-10-27" });
  assert.equal(defaultPeriod(null), null);
});

test("초기자금을 한글 금액으로 읽어 준다", () => {
  assert.equal(koreanAmount(50_000_000), "5천만 원");
  assert.equal(koreanAmount(1_000_000), "100만 원");
  assert.equal(koreanAmount(150_000_000), "1억 5천만 원");
  assert.equal(koreanAmount(10_000_000_000), "100억 원");
  assert.equal(koreanAmount(12_345_678), "1천234만 5천678 원");
  assert.equal(koreanAmount(0), "0 원");
});
