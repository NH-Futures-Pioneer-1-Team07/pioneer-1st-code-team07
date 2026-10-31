import type { BacktestMeta, BacktestResult, RunSummary } from "../apis/types.ts";
import { formatMoney, formatNumber } from "./format.ts";

/** 한 번에 비교할 수 있는 이력 수 */
export const MAX_COMPARE = 4;

/** 이력마다 붙이는 이름표(기준이 A)와 색 */
export const RUN_LETTERS = ["A", "B", "C", "D"] as const;
export const RUN_COLORS = ["#ffb819", "#5795ff", "#49c99b", "#c58cff"] as const;

/**
 * 기준 이력과 비교할 수 없는 이유. 비교할 수 있으면 null.
 * 종목·초기자금·기간이 같아야 성과를 같은 조건에서 읽을 수 있다. 수수료·슬리피지는 달라도 되며 설정값 표에서 비교한다.
 */
export function compareBlocker(base: RunSummary | undefined, run: RunSummary): string | null {
  if (run.status !== "completed") return "완료된 이력이 아님";
  if (!base) return null;
  if (run.instrument.code !== base.instrument.code) return "종목이 다름";
  if (run.initial_capital === undefined || run.initial_capital !== base.initial_capital) return "초기자금이 다름";
  if (!run.period || run.period.start !== base.period?.start || run.period.end !== base.period?.end)
    return "테스트 기간이 다름";
  return null;
}

export type Unit = "money" | "rate" | "count" | "ratio";

export function formatValue(unit: Unit, value: number): string {
  if (unit === "money") return formatMoney(value);
  if (unit === "rate") return `${(value * 100).toFixed(2)}%`;
  if (unit === "count") return `${formatNumber(value)}건`;
  return value.toFixed(2);
}

/** 기준과의 차이. 비율은 %p로 쓴다. */
export function formatDelta(unit: Unit, delta: number): string {
  const sign = delta > 0 ? "+" : "";
  if (unit === "rate") return `${sign}${(delta * 100).toFixed(2)}%p`;
  return `${sign}${formatValue(unit, delta)}`;
}

export type MetricGroup = "수익성" | "위험" | "거래" | "비용" | "곡선";
export type MetricShape = "scalar" | "winloss" | "equity" | "drawdown" | "daily";

export interface MetricDef {
  id: string;
  group: MetricGroup;
  label: string;
  shape: MetricShape;
  unit: Unit;
  /** 클수록 좋으면 high, 작을수록 좋으면 low, 좋고 나쁨이 없으면 null */
  better: "high" | "low" | null;
  value?: (result: BacktestResult) => number | null;
}

const safeDivide = (top: number, bottom: number) => (bottom === 0 ? null : top / bottom);

export const METRICS: readonly MetricDef[] = [
  { id: "net_pnl", group: "수익성", label: "순손익", shape: "scalar", unit: "money", better: "high", value: (r) => r.net_pnl },
  { id: "gross_pnl", group: "수익성", label: "총손익(수수료 전)", shape: "scalar", unit: "money", better: "high", value: (r) => r.gross_pnl },
  { id: "return_rate", group: "수익성", label: "수익률", shape: "scalar", unit: "rate", better: "high", value: (r) => r.return_rate },
  { id: "final_equity", group: "수익성", label: "최종 자산", shape: "scalar", unit: "money", better: "high", value: (r) => r.final_equity },
  { id: "max_drawdown", group: "위험", label: "최대낙폭(금액)", shape: "scalar", unit: "money", better: "low", value: (r) => r.max_drawdown },
  { id: "max_drawdown_rate", group: "위험", label: "최대낙폭(비율)", shape: "scalar", unit: "rate", better: "low", value: (r) => r.max_drawdown_rate },
  { id: "return_per_mdd", group: "위험", label: "수익률 ÷ 최대낙폭", shape: "scalar", unit: "ratio", better: "high", value: (r) => safeDivide(r.return_rate, r.max_drawdown_rate) },
  { id: "trade_count", group: "거래", label: "거래 수", shape: "scalar", unit: "count", better: null, value: (r) => r.trade_count },
  { id: "win_loss", group: "거래", label: "승·패", shape: "winloss", unit: "count", better: null },
  { id: "win_rate", group: "거래", label: "승률", shape: "scalar", unit: "rate", better: "high", value: (r) => safeDivide(r.win_count, r.win_count + r.loss_count) },
  { id: "pnl_per_trade", group: "거래", label: "거래당 평균 순손익", shape: "scalar", unit: "money", better: "high", value: (r) => safeDivide(r.net_pnl, r.trade_count) },
  { id: "pnl_per_day", group: "거래", label: "일평균 순손익", shape: "scalar", unit: "money", better: "high", value: (r) => safeDivide(r.net_pnl, r.days) },
  { id: "fee", group: "비용", label: "수수료", shape: "scalar", unit: "money", better: "low", value: (r) => r.fee },
  { id: "fee_ratio", group: "비용", label: "수수료 ÷ 총손익", shape: "scalar", unit: "rate", better: "low", value: (r) => (r.gross_pnl > 0 ? r.fee / r.gross_pnl : null) },
  { id: "equity", group: "곡선", label: "수익률 곡선", shape: "equity", unit: "rate", better: null },
  { id: "drawdown", group: "곡선", label: "낙폭 곡선", shape: "drawdown", unit: "rate", better: null },
  { id: "daily", group: "곡선", label: "일별 손익", shape: "daily", unit: "money", better: null },
];

export const METRIC_GROUPS: readonly MetricGroup[] = ["수익성", "위험", "거래", "비용", "곡선"];

/** 처음에 보여 주는 핵심 수치 */
export const CORE_METRICS = ["net_pnl", "return_rate", "max_drawdown_rate", "win_rate", "equity"];

export interface CompareEntry {
  key: string;
  strategyId: string;
  strategyName: string;
  meta: BacktestMeta;
  result: BacktestResult;
}

/** 비교 대상 중 가장 좋은 값을 가진 위치. 좋고 나쁨이 없거나 값이 모두 같으면 null. */
export function bestIndex(values: (number | null)[], better: "high" | "low" | null): number | null {
  if (!better) return null;
  const present = values.filter((value): value is number => value !== null);
  if (present.length < 2 || new Set(present).size === 1) return null;
  const target = better === "high" ? Math.max(...present) : Math.min(...present);
  return values.indexOf(target);
}

export interface CurveRow {
  day: string;
  [key: string]: number | string;
}

/** 이력마다 날짜별 값을 한 줄로 합친다. equity는 수익률, drawdown은 고점 대비 낙폭, daily는 전날 대비 손익. */
export function curveRows(entries: CompareEntry[], shape: "equity" | "drawdown" | "daily"): CurveRow[] {
  const rows = new Map<string, CurveRow>();
  for (const entry of entries) {
    const { initial_capital: initial, equity_curve: curve } = entry.result;
    let previous = initial;
    let peak = initial;
    for (const point of curve) {
      const day = point.time.slice(0, 10);
      const row = rows.get(day) ?? { day };
      peak = Math.max(peak, point.equity);
      row[entry.key] =
        shape === "equity"
          ? point.equity / initial - 1
          : shape === "drawdown"
            ? point.equity / peak - 1
            : point.equity - previous;
      previous = point.equity;
      rows.set(day, row);
    }
  }
  return [...rows.values()].sort((a, b) => a.day.localeCompare(b.day));
}

export interface ParamRow {
  name: string;
  /** 이력 순서대로의 값. 그 이력의 전략에 없는 파라미터는 null */
  values: (string | null)[];
  differs: boolean;
}

const paramText = (value: unknown) => (typeof value === "object" ? JSON.stringify(value) : String(value));

/** 전략 파라미터에 실행 때의 비용 가정(슬리피지·수수료율)을 더한 설정값 */
function settings(meta: BacktestMeta): Record<string, unknown> {
  const { slippage, fee } = meta.assumptions ?? {};
  return {
    ...(slippage ? { 슬리피지_틱: slippage.ticks } : {}),
    ...(fee ? { 수수료율: fee.rate } : {}),
    ...meta.params,
  };
}

/** 모든 이력의 파라미터 이름을 합쳐, 값이 다른 파라미터를 앞에 둔다. */
export function paramRows(entries: CompareEntry[]): ParamRow[] {
  const names: string[] = [];
  for (const entry of entries)
    for (const name of Object.keys(settings(entry.meta))) if (!names.includes(name)) names.push(name);
  const rows = names.map((name) => {
    const values = entries.map((entry) => {
      const params = settings(entry.meta);
      return name in params ? paramText(params[name]) : null;
    });
    return { name, values, differs: new Set(values).size > 1 };
  });
  return [...rows.filter((row) => row.differs), ...rows.filter((row) => !row.differs)];
}
