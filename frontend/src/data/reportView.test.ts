import assert from "node:assert/strict";
import test from "node:test";
import type { ReportPeriod } from "../apis/types.ts";
import {
  columnLabel,
  formatCell,
  isSigned,
  metricsIn,
  paramText,
  parseColumn,
  sortRows,
  visibleColumns,
} from "./reportView.ts";

const periods: ReportPeriod[] = [
  { label: "전체", start: "2026-08-11", end: "2026-11-09", kind: "full" },
  { label: "구간1", start: "2026-08-11", end: "2026-09-15", kind: "split" },
];
const columns = [
  "profit_loss_rate",
  "positive_periods",
  "net_pnl[2026-08-11~2026-11-09]",
  "max_drawdown_rate[2026-08-11~2026-11-09]",
  "net_pnl[2026-08-11~2026-09-15]",
];

test("열 이름을 파라미터와 요약과 기간별 지표로 구분한다", () => {
  assert.deepEqual(parseColumn("profit_loss_rate"), { kind: "param", name: "profit_loss_rate" });
  assert.deepEqual(parseColumn("worst_net_pnl"), { kind: "summary", name: "worst_net_pnl" });
  assert.deepEqual(parseColumn("net_pnl[2026-08-11~2026-11-09]"), {
    kind: "metric",
    metric: "net_pnl",
    period: "2026-08-11~2026-11-09",
  });
});

test("지표 열 제목은 한글 지표 이름과 기간 이름으로 쓴다", () => {
  assert.equal(columnLabel("net_pnl[2026-08-11~2026-11-09]", periods), "순손익 · 전체");
  assert.equal(columnLabel("sharpe[2026-01-01~2026-01-31]", periods), "샤프 · 2026-01-01~2026-01-31");
  assert.equal(columnLabel("positive_periods", periods), "양수 기간");
  assert.equal(columnLabel("short_bars", periods), "short_bars");
});

test("값을 지표에 맞는 서식으로 보여 준다", () => {
  assert.equal(formatCell("net_pnl[a~b]", 63224.4), "63,224");
  assert.equal(formatCell("total_net_pnl", -3148.6), "-3,149");
  assert.equal(formatCell("max_drawdown_rate[a~b]", 0.25012), "25.0%");
  assert.equal(formatCell("win_rate[a~b]", 0.757), "75.7%");
  assert.equal(formatCell("trade_count[a~b]", 149), "149");
  assert.equal(formatCell("sharpe[a~b]", 2.5902), "2.59");
  assert.equal(formatCell("profit_loss_rate", 0.4), "0.4");
  assert.equal(formatCell("fee_ratio[a~b]", null), "—");
  assert.equal(formatCell("note", "문자"), "문자");
});

test("손익 부호로 색을 입힐 열만 가려낸다", () => {
  assert.equal(isSigned("net_pnl[a~b]"), true);
  assert.equal(isSigned("worst_net_pnl"), true);
  assert.equal(isSigned("max_drawdown_rate[a~b]"), false);
  assert.equal(isSigned("profit_loss_rate"), false);
});

test("표에 나온 지표를 정해진 순서로 돌려준다", () => {
  assert.deepEqual(metricsIn(columns), ["net_pnl", "max_drawdown_rate"]);
});

test("고른 지표의 기간 열과 파라미터·요약 열만 보인다", () => {
  assert.deepEqual(visibleColumns(columns, new Set(["net_pnl"])), [0, 1, 2, 4]);
  assert.deepEqual(visibleColumns(columns, new Set()), [0, 1]);
});

test("숫자는 크기순, 글자는 가나다순으로 정렬하고 빈 칸은 항상 아래에 둔다", () => {
  const rows = [[2, "b"], [null, "a"], [10, "c"], [1, null]];
  assert.deepEqual(sortRows(rows, 0, "asc").map((r) => r[0]), [1, 2, 10, null]);
  assert.deepEqual(sortRows(rows, 0, "desc").map((r) => r[0]), [10, 2, 1, null]);
  assert.deepEqual(sortRows(rows, 1, "asc").map((r) => r[1]), ["a", "b", "c", null]);
});

test("정렬은 원본 배열을 바꾸지 않고 같은 값은 원래 순서를 지킨다", () => {
  const rows = [[1, "x"], [1, "y"], [0, "z"]];
  const sorted = sortRows(rows, 0, "asc");
  assert.deepEqual(sorted.map((r) => r[1]), ["z", "x", "y"]);
  assert.deepEqual(rows.map((r) => r[1]), ["x", "y", "z"]);
});

test("파라미터 값을 이름과 함께 글로 만든다", () => {
  assert.equal(paramText("profit_loss_rate", 0.4), "profit_loss_rate 0.4");
  assert.equal(paramText("vix_thresholds", [15, 20]), "vix_thresholds [15,20]");
});

import { moneyText, shortTime } from "./reportView.ts";

test("금액은 반올림해 천 단위 쉼표로 보여 준다", () => {
  assert.equal(moneyText(63224.4), "63,224");
  assert.equal(moneyText(-989.6), "-990");
});

test("시각은 월.일 시:분으로 줄여 보여 준다", () => {
  assert.equal(shortTime("2026-08-13T23:05:00+09:00"), "08.13 23:05");
  assert.equal(shortTime("2026-08-13T23:05:00"), "08.13 23:05");
  assert.equal(shortTime(null), "—");
});

test("전략 명세가 있으면 파라미터를 한글 이름과 단위로 보여 준다", () => {
  const specs = {
    window_days: { default: 40, description: "", editable: true, label: "일봉 쌍 개수", unit: null, min: 5, max: 120 },
    entry_pct: { default: 0, description: "", editable: true, label: "진입 백분위", unit: "percent" as const, min: 0, max: 0.49 },
  };
  assert.equal(paramText("window_days", 60, specs), "일봉 쌍 개수 60");
  assert.equal(paramText("entry_pct", 0.1, specs), "진입 백분위 10%");
  assert.equal(paramText("unknown", 3, specs), "unknown 3");
  assert.equal(columnLabel("entry_pct", [], specs), "진입 백분위");
  assert.equal(formatCell("entry_pct", 0.02, specs), "2%");
  assert.equal(formatCell("window_days", 60, specs), "60");
  assert.equal(formatCell("entry_pct", 0.02), "0.02");
});

test("기간별 열은 머리말의 기간 순서로 놓고 파라미터·요약 열은 앞에 둔다", () => {
  const columns = ["a", "net_pnl[2026-08-11~2026-09-15]", "net_pnl[2026-08-11~2026-11-10]", "positive_periods", "net_pnl[2026-09-16~2026-10-13]", "net_pnl[x~y]"];
  const periods = [
    { label: "전체", start: "2026-08-11", end: "2026-11-10", kind: "full" as const },
    { label: "구간1", start: "2026-08-11", end: "2026-09-15", kind: "split" as const },
    { label: "구간2", start: "2026-09-16", end: "2026-10-13", kind: "split" as const },
  ];
  assert.deepEqual(visibleColumns(columns, new Set(["net_pnl"]), periods), [0, 3, 2, 1, 4, 5]);
  assert.deepEqual(visibleColumns(columns, new Set(["net_pnl"])), [0, 3, 1, 2, 4, 5]);
});
