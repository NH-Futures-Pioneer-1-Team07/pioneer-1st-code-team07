import test from "node:test";
import assert from "node:assert/strict";
import {
  bestIndex,
  compareBlocker,
  curveRows,
  formatDelta,
  METRICS,
  paramRows,
} from "./compareView.ts";
import type { CompareEntry } from "./compareView.ts";
import type { BacktestMeta, BacktestResult, RunSummary } from "../apis/types.ts";

const run = (patch: Partial<RunSummary> = {}): RunSummary => ({
  strategy_id: "s1",
  mode: "backtest",
  run_id: "r1",
  strategy_name: "전략",
  instrument: { name: "삼성전자선물", code: "A1" },
  started_at: "2026-10-29T05:07:01+09:00",
  ended_at: "2026-10-29T05:07:10+09:00",
  status: "completed",
  period: { start: "2026-10-01", end: "2026-10-28" },
  initial_capital: 50_000_000,
  assumptions: {
    fee: { rate: 0.000085, basis: "", source: "" },
    slippage: { ticks: 1, tick_size: 500, direction: "" },
    fill: { on_bar: "", on_price: "", intrabar_path: "" },
    margin: "",
  },
  net_pnl: 0,
  ...patch,
});

test("기준이 없으면 완료된 이력만 선택할 수 있다", () => {
  assert.equal(compareBlocker(undefined, run()), null);
  assert.equal(compareBlocker(undefined, run({ status: "running" })), "완료된 이력이 아님");
});

test("종목·초기자금·기간이 기준과 같아야 선택할 수 있다", () => {
  const base = run();
  assert.equal(compareBlocker(base, run({ strategy_id: "s2", strategy_name: "다른 전략" })), null);
  assert.equal(compareBlocker(base, run({ instrument: { name: "x", code: "A2" } })), "종목이 다름");
  assert.equal(compareBlocker(base, run({ initial_capital: 1 })), "초기자금이 다름");
  assert.equal(compareBlocker(base, run({ period: { start: "2026-10-01", end: "2026-10-27" } })), "테스트 기간이 다름");
  const other = run();
  other.assumptions = { ...base.assumptions!, slippage: { ticks: 2, tick_size: 500, direction: "" } };
  assert.equal(compareBlocker(base, other), null);
  assert.equal(compareBlocker(base, run({ assumptions: undefined })), null);
});

const result = (patch: Partial<BacktestResult> = {}): BacktestResult => ({
  initial_capital: 1000,
  final_equity: 1100,
  gross_pnl: 120,
  fee: 20,
  net_pnl: 100,
  return_rate: 0.1,
  trade_count: 4,
  win_count: 3,
  loss_count: 1,
  max_drawdown: 50,
  max_drawdown_rate: 0.05,
  days: 2,
  bars: 10,
  equity_curve: [
    { time: "2026-10-01T15:48:00", equity: 1050 },
    { time: "2026-10-02T15:48:00", equity: 1100 },
  ],
  ...patch,
});

const entry = (key: string, params: Record<string, unknown>, patch: Partial<BacktestResult> = {}, strategyId = "s1"): CompareEntry => ({
  key,
  strategyId,
  strategyName: strategyId,
  meta: { params } as unknown as BacktestMeta,
  result: result(patch),
});

test("지표 값은 result에서 계산한다", () => {
  const value = (id: string, r = result()) => METRICS.find((m) => m.id === id)!.value!(r);
  assert.equal(value("win_rate"), 0.75);
  assert.equal(value("pnl_per_trade"), 25);
  assert.equal(value("pnl_per_day"), 50);
  assert.equal(value("return_per_mdd"), 2);
  assert.equal(value("fee_ratio"), 20 / 120);
  assert.equal(value("fee_ratio", result({ gross_pnl: -5 })), null);
  assert.equal(value("return_per_mdd", result({ max_drawdown_rate: 0 })), null);
  assert.equal(value("pnl_per_trade", result({ trade_count: 0 })), null);
});

test("가장 좋은 값은 지표의 방향을 따르고 같은 값이면 없다", () => {
  assert.equal(bestIndex([1, 3, 2], "high"), 1);
  assert.equal(bestIndex([1, 3, 2], "low"), 0);
  assert.equal(bestIndex([2, 2], "high"), null);
  assert.equal(bestIndex([1, 3], null), null);
  assert.equal(bestIndex([null, 3], "high"), null);
});

test("기준과의 차이는 부호를 붙이고 비율은 %p로 쓴다", () => {
  assert.equal(formatDelta("rate", 0.0123), "+1.23%p");
  assert.equal(formatDelta("rate", -0.01), "-1.00%p");
  assert.equal(formatDelta("money", 1500), "+1,500원");
});

test("곡선은 날짜별로 이력을 합친다", () => {
  const a = entry("a", {});
  const b = entry("b", {}, {
    equity_curve: [
      { time: "2026-10-01T15:48:00", equity: 900 },
      { time: "2026-10-02T15:48:00", equity: 950 },
    ],
  });
  const equity = curveRows([a, b], "equity");
  assert.deepEqual(equity.map((row) => row.day), ["2026-10-01", "2026-10-02"]);
  assert.ok(Math.abs((equity[0].a as number) - 0.05) < 1e-9);
  assert.ok(Math.abs((equity[0].b as number) + 0.1) < 1e-9);
  const drawdown = curveRows([b], "drawdown");
  assert.equal(drawdown[0].b, 900 / 1000 - 1);
  assert.equal(drawdown[1].b, 950 / 1000 - 1);
  const daily = curveRows([a], "daily");
  assert.equal(daily[0].a, 50);
  assert.equal(daily[1].a, 50);
});

test("설정 표는 다른 값을 앞에 두고 없는 파라미터는 null이다", () => {
  const rows = paramRows([
    entry("a", { stop: 1500, tick: 500 }),
    entry("b", { stop: 2000, tick: 500, extra: true }, {}, "s2"),
  ]);
  assert.deepEqual(rows.map((row) => row.name), ["stop", "extra", "tick"]);
  assert.deepEqual(rows[0].values, ["1500", "2000"]);
  assert.deepEqual(rows[1].values, [null, "true"]);
  assert.equal(rows[2].differs, false);
});

test("설정 표에는 슬리피지와 수수료율이 들어간다", () => {
  const withCost = (ticks: number): CompareEntry => {
    const e = entry("a", { stop: 1 });
    (e.meta as { assumptions?: unknown }).assumptions = {
      slippage: { ticks, tick_size: 500, direction: "" },
      fee: { rate: 0.000085, basis: "", source: "" },
    };
    return e;
  };
  const rows = paramRows([withCost(0), withCost(1)]);
  assert.equal(rows[0].name, "슬리피지_틱");
  assert.deepEqual(rows[0].values, ["0", "1"]);
  assert.equal(rows.find((row) => row.name === "수수료율")?.differs, false);
});
