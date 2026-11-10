import type { ReportPeriod, TableCell } from "../apis/types.ts";

export const METRIC_LABEL: Record<string, string> = {
  net_pnl: "순손익",
  return_rate: "수익률",
  max_drawdown_rate: "최대 낙폭",
  trade_count: "거래 수",
  win_rate: "승률",
  fee_ratio: "수수료 비중",
  sharpe: "샤프",
};

export const SUMMARY_LABEL: Record<string, string> = {
  period_count: "기간 수",
  positive_periods: "양수 기간",
  worst_net_pnl: "최저 순손익",
  total_net_pnl: "합산 순손익",
};

const PERCENT = new Set(["return_rate", "max_drawdown_rate", "win_rate", "fee_ratio"]);
const MONEY = new Set(["net_pnl", "worst_net_pnl", "total_net_pnl"]);
const INTEGER = new Set(["trade_count", "period_count", "positive_periods"]);
const SIGNED = new Set(["net_pnl", "return_rate", "worst_net_pnl", "total_net_pnl", "sharpe"]);
const METRIC_COLUMN = /^([a-z_]+)\[(.+)\]$/;

export type ColumnKind =
  | { kind: "metric"; metric: string; period: string }
  | { kind: "summary"; name: string }
  | { kind: "param"; name: string };

export function parseColumn(name: string): ColumnKind {
  const match = METRIC_COLUMN.exec(name);
  if (match && match[1] in METRIC_LABEL) return { kind: "metric", metric: match[1], period: match[2] };
  if (name in SUMMARY_LABEL) return { kind: "summary", name };
  return { kind: "param", name };
}

/** `2026-08-11~2026-09-15` 같은 기간 표시를 머리말의 기간 이름으로 바꾼다. 모르는 기간은 그대로 둔다. */
export function periodName(range: string, periods: ReportPeriod[]): string {
  const found = periods.find((period) => `${period.start}~${period.end}` === range);
  return found ? found.label : range;
}

export function columnLabel(name: string, periods: ReportPeriod[]): string {
  const column = parseColumn(name);
  if (column.kind === "metric") return `${METRIC_LABEL[column.metric]} · ${periodName(column.period, periods)}`;
  if (column.kind === "summary") return SUMMARY_LABEL[column.name];
  return name;
}

/** 손익 부호에 따라 색을 입힐 열인지. */
export function isSigned(name: string): boolean {
  const column = parseColumn(name);
  const key = column.kind === "metric" ? column.metric : column.kind === "summary" ? column.name : "";
  return SIGNED.has(key);
}

export function formatCell(name: string, value: TableCell): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  const column = parseColumn(name);
  const key = column.kind === "metric" ? column.metric : column.kind === "summary" ? column.name : "";
  if (PERCENT.has(key)) return `${(value * 100).toFixed(1)}%`;
  if (MONEY.has(key)) return Math.round(value).toLocaleString("ko-KR");
  if (INTEGER.has(key)) return String(Math.round(value));
  if (key === "sharpe") return value.toFixed(2);
  return String(value);
}

/** 표에 나온 지표 이름들을 `METRIC_LABEL` 순서로. */
export function metricsIn(columns: string[]): string[] {
  const found = new Set<string>();
  for (const name of columns) {
    const column = parseColumn(name);
    if (column.kind === "metric") found.add(column.metric);
  }
  return Object.keys(METRIC_LABEL).filter((metric) => found.has(metric));
}

/** 파라미터·요약 열은 항상, 기간별 지표 열은 고른 지표만 보인다. 보일 열의 위치를 돌려준다. */
export function visibleColumns(columns: string[], metrics: ReadonlySet<string>): number[] {
  const shown: number[] = [];
  columns.forEach((name, index) => {
    const column = parseColumn(name);
    if (column.kind !== "metric" || metrics.has(column.metric)) shown.push(index);
  });
  return shown;
}

/** 열 하나로 정렬한 새 배열. 빈 칸은 방향과 관계없이 맨 아래에 둔다. */
export function sortRows(rows: TableCell[][], index: number, direction: "asc" | "desc"): TableCell[][] {
  const sign = direction === "asc" ? 1 : -1;
  return rows
    .map((row, order) => ({ row, order }))
    .sort((a, b) => {
      const left = a.row[index];
      const right = b.row[index];
      if (left === null && right === null) return a.order - b.order;
      if (left === null) return 1;
      if (right === null) return -1;
      const result =
        typeof left === "number" && typeof right === "number"
          ? left - right
          : String(left).localeCompare(String(right), "ko");
      return result === 0 ? a.order - b.order : sign * result;
    })
    .map((item) => item.row);
}

export const roleLabel = (role: string) => (role === "recommended" ? "추천" : "대안");

/** 파라미터 값을 칩에 넣을 글로. */
export function paramText(name: string, value: unknown): string {
  const text = Array.isArray(value) || (typeof value === "object" && value !== null) ? JSON.stringify(value) : String(value);
  return `${name} ${text}`;
}
