import assert from "node:assert/strict";
import test from "node:test";
import type { ReportPeriod, ReportRecommendation, ReportTable, SweepResult, SweepTrade } from "../apis/types.ts";
import {
  equityRows,
  modeValue,
  normalizeReason,
  numericParams,
  periodComparison,
  reasonSummary,
  sensitivityData,
  varyingParams,
} from "./reportCharts.ts";

const periods: ReportPeriod[] = [
  { label: "전체", start: "2026-10-01", end: "2026-10-31", kind: "full" },
  { label: "구간1", start: "2026-10-01", end: "2026-10-15", kind: "split" },
];
const table: ReportTable = {
  columns: ["rate", "bars", "mode", "net_pnl[2026-10-01~2026-10-31]", "net_pnl[2026-10-01~2026-10-15]", "sharpe[2026-10-01~2026-10-31]"],
  rows: [
    [0.3, 5, "a", 30, 10, 1],
    [0.1, 5, "a", 10, 5, 2],
    [0.2, 5, "a", 20, null, 3],
    [0.2, 8, "a", 99, 99, 9], // bars가 흔한 값(5)이 아니라 제외된다
    [0.2, 5, "b", 77, 77, 7], // mode가 흔한 값(a)이 아니라 제외된다
    [0.4, 5, "a", 40, 20, 4],
  ],
};

test("가장 많이 나온 값을 고르고 같은 횟수면 먼저 나온 값을 고른다", () => {
  assert.equal(modeValue([5, 8, 5, 8, 5]), 5);
  assert.equal(modeValue(["x", "y"]), "x");
  assert.equal(modeValue([]), null);
});

test("조합 사이에 값이 다른 파라미터와 그중 숫자 파라미터를 찾는다", () => {
  assert.deepEqual(varyingParams(table), ["rate", "bars", "mode"]);
  assert.deepEqual(numericParams(table), ["rate", "bars"]);
});

test("숫자 파라미터는 시험한 값이 많은 것부터 돌려준다", () => {
  const wide: ReportTable = {
    columns: ["bars", "rate", "net_pnl[a~b]"],
    rows: [[5, 0.1, 1], [8, 0.2, 2], [5, 0.3, 3], [5, 0.4, 4]],
  };
  assert.deepEqual(numericParams(wide), ["rate", "bars"]);
});

test("가로축 외의 파라미터를 흔한 값으로 고정하고 기간별 값을 가로축 순서로 모은다", () => {
  const data = sensitivityData(table, periods, "rate", "net_pnl");
  assert.deepEqual(data.series, ["전체", "구간1"]);
  assert.deepEqual(data.fixed, [
    { name: "bars", value: 5 },
    { name: "mode", value: "a" },
  ]);
  assert.deepEqual(data.points, [
    { x: 0.1, 전체: 10, 구간1: 5 },
    { x: 0.2, 전체: 20, 구간1: null },
    { x: 0.3, 전체: 30, 구간1: 10 },
    { x: 0.4, 전체: 40, 구간1: 20 },
  ]);
});

test("선 순서는 표의 열 순서가 아니라 머리말의 기간 순서를 따른다", () => {
  const reversed: ReportTable = {
    columns: ["rate", "net_pnl[2026-10-01~2026-10-15]", "net_pnl[2026-10-01~2026-10-31]"],
    rows: [[0.1, 5, 10], [0.2, 6, 11]],
  };
  assert.deepEqual(sensitivityData(reversed, periods, "rate", "net_pnl").series, ["전체", "구간1"]);
});

test("다른 지표를 고르면 그 지표의 열만 쓴다", () => {
  const data = sensitivityData(table, periods, "rate", "sharpe");
  assert.deepEqual(data.series, ["전체"]);
  assert.deepEqual(data.points.map((p) => p.전체), [2, 3, 1, 4]);
});

const recommended: ReportRecommendation[] = [
  { label: "추천", role: "recommended", params: {}, ids: { 전체: "a", 구간1: "b" } },
  { label: "대안", role: "alternative", params: {}, ids: { 전체: "c" } },
];
const result = (id: string, net: number, equity: [string, number][]): SweepResult => ({
  id,
  strategy_id: "s",
  params: {},
  start: "2026-10-01",
  end: "2026-10-31",
  slippage_ticks: 1,
  initial_capital: 1000,
  summary: { net_pnl: net, gross_pnl: 0, fee: 0, return_rate: 0, max_drawdown_rate: 0, trade_count: 0, win_count: 0, loss_count: 0 },
  daily_equity: equity.map(([time, value]) => ({ time, equity: value })),
});
const results = [
  result("a", 50, [["2026-10-02T00:00:00", 1010], ["2026-10-03T00:00:00", 1050]]),
  result("b", 20, []),
  result("c", -10, [["2026-10-03T00:00:00", 990], ["2026-10-04T00:00:00", 990]]),
];

test("기간별 순손익을 조합마다 모으고 결과가 없는 칸은 비운다", () => {
  assert.deepEqual(periodComparison(periods, recommended, results), [
    { period: "전체", 추천: 50, 대안: -10 },
    { period: "구간1", 추천: 20, 대안: null },
  ]);
});

test("자산 곡선은 날짜 합집합에 수익률로 담고 같은 날 점은 마지막 값을 쓴다", () => {
  const rows = equityRows("전체", recommended, [
    ...results,
    result("a", 50, [["2026-10-02T00:00:00", 1010], ["2026-10-02T06:00:00", 1020], ["2026-10-03T00:00:00", 1050]]),
  ]);
  assert.deepEqual(rows.map((r) => r.day), ["2026-10-02", "2026-10-03", "2026-10-04"]);
  assert.ok(Math.abs((rows[0].추천 as number) - 0.02) < 1e-9);
  assert.ok(Math.abs((rows[1].추천 as number) - 0.05) < 1e-9);
  assert.ok(Math.abs((rows[1].대안 as number) + 0.01) < 1e-9);
  assert.equal(rows[2].추천, undefined);
});

test("청산 이유에서 숫자와 끝 괄호 설명을 걷어 같은 종류로 묶는다", () => {
  assert.equal(
    normalizeReason("증거금 대비 평가손익 40.3%가 익절 기준 40%에 도달 (중기 매도 허용 · 장중 단기선이 장기선 아래)"),
    "증거금 대비 평가손익 #가 익절 기준 #에 도달",
  );
  assert.equal(
    normalizeReason("증거금 대비 평가손익 -21.3%가 손절 기준 -20%에 도달 (중기 중립)"),
    "증거금 대비 평가손익 #가 손절 기준 #에 도달",
  );
  assert.equal(normalizeReason("백테스트 종료 청산"), "백테스트 종료 청산");
  assert.equal(normalizeReason(null), "이유 없음");
});

test("청산 이유별 건수와 순손익을 손익 크기순으로 요약한다", () => {
  const trade = (reason: string | null, net: number): SweepTrade => ({
    kind: "trade", entry_id: "e", side: "buy", quantity: 1, opened_at: null, closed_at: null,
    entry_price: 1, exit_price: 1, gross_pnl: net, fee: 0, net_pnl: net, entry_reason: null, exit_reason: reason,
  });
  const summary = reasonSummary([
    trade("익절 20%에 도달 (a)", 100),
    trade("익절 40%에 도달 (b)", 50),
    trade("손절 20%에 도달", -30),
    trade(null, 1),
  ]);
  assert.deepEqual(summary.map((s) => [s.reason, s.count, s.netPnl, s.average]), [
    ["익절 #에 도달", 2, 150, 75],
    ["손절 #에 도달", 1, -30, -30],
    ["이유 없음", 1, 1, 1],
  ]);
});
