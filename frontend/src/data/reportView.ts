import type { ParameterSpec, ReportPeriod, TableCell } from "../apis/types.ts";

/** 전략 매니페스트의 파라미터 명세. 이름을 한글로, 값을 단위에 맞게 보여 줄 때 쓴다. */
export type ParamSpecs = Record<string, ParameterSpec>;

const paramLabel = (name: string, specs?: ParamSpecs) => specs?.[name]?.label ?? name;

/** 퍼센트 단위 파라미터는 비율을 퍼센트로 바꾼다(0.1 → `10%`). 그 밖의 값은 글자 그대로. */
function paramValue(name: string, value: unknown, specs?: ParamSpecs): string {
  if (typeof value === "number" && specs?.[name]?.unit === "percent") return `${Number((value * 100).toFixed(6))}%`;
  return Array.isArray(value) || (typeof value === "object" && value !== null) ? JSON.stringify(value) : String(value);
}

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

export function columnLabel(name: string, periods: ReportPeriod[], specs?: ParamSpecs): string {
  const column = parseColumn(name);
  if (column.kind === "metric") return `${METRIC_LABEL[column.metric]} · ${periodName(column.period, periods)}`;
  if (column.kind === "summary") return SUMMARY_LABEL[column.name];
  return paramLabel(name, specs);
}

/** 손익 부호에 따라 색을 입힐 열인지. */
export function isSigned(name: string): boolean {
  const column = parseColumn(name);
  const key = column.kind === "metric" ? column.metric : column.kind === "summary" ? column.name : "";
  return SIGNED.has(key);
}

export function formatCell(name: string, value: TableCell, specs?: ParamSpecs): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  const column = parseColumn(name);
  if (column.kind === "param") return paramValue(name, value, specs);
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
export function visibleColumns(columns: string[], metrics: ReadonlySet<string>, periods: ReportPeriod[] = []): number[] {
  const shown: number[] = [];
  columns.forEach((name, index) => {
    const column = parseColumn(name);
    if (column.kind !== "metric" || metrics.has(column.metric)) shown.push(index);
  });
  // 기간별 열은 머리말의 기간 순서(전체, 구간1, …)로 놓는다. 파라미터·요약 열이 앞이고, 모르는 기간은 뒤다.
  const rank = (index: number) => {
    const column = parseColumn(columns[index]);
    if (column.kind !== "metric") return -1;
    const found = periods.findIndex((period) => `${period.start}~${period.end}` === column.period);
    return found < 0 ? periods.length : found;
  };
  return shown
    .map((index, order) => ({ index, order }))
    .sort((a, b) => rank(a.index) - rank(b.index) || a.order - b.order)
    .map((item) => item.index);
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
export function paramText(name: string, value: unknown, specs?: ParamSpecs): string {
  return `${paramLabel(name, specs)} ${paramValue(name, value, specs)}`;
}

/** 금액을 통화 표시 없이 천 단위 쉼표로. 전략 문서의 단위(계약, 달러)는 보고서 본문이 설명한다. */
export const moneyText = (value: number) => Math.round(value).toLocaleString("ko-KR");

/** `2026-08-13T23:05:00+09:00` → `08.13 23:05`. 없으면 `—`. */
export function shortTime(time: string | null | undefined): string {
  if (!time) return "—";
  return `${time.slice(5, 10).replace("-", ".")} ${time.slice(11, 16)}`;
}
