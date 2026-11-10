import type { ReportPeriod, ReportRecommendation, ReportTable, SweepResult, SweepTrade, TableCell } from "../apis/types.ts";
import { parseColumn, periodName } from "./reportView.ts";

const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

/** 가장 많이 나온 값. 같은 횟수면 먼저 나온 값. */
export function modeValue(values: TableCell[]): TableCell {
  const counts: { value: TableCell; count: number }[] = [];
  for (const value of values) {
    const found = counts.find((item) => same(item.value, value));
    if (found) found.count += 1;
    else counts.push({ value, count: 1 });
  }
  let best: { value: TableCell; count: number } | undefined;
  for (const item of counts) if (!best || item.count > best.count) best = item;
  return best ? best.value : null;
}

/** 조합 사이에 값이 다른 파라미터 열 이름. */
export function varyingParams(table: ReportTable): string[] {
  const names: string[] = [];
  table.columns.forEach((name, index) => {
    if (parseColumn(name).kind !== "param") return;
    const distinct = new Set(table.rows.map((row) => JSON.stringify(row[index])));
    if (distinct.size > 1) names.push(name);
  });
  return names;
}

/** 가로축으로 쓸 수 있는, 값이 모두 숫자인 파라미터 열 이름. 시험한 값이 많은 것부터(같으면 표의 열 순서). */
export function numericParams(table: ReportTable): string[] {
  const distinct = (name: string) => new Set(table.rows.map((row) => row[table.columns.indexOf(name)])).size;
  return varyingParams(table)
    .filter((name) => {
      const index = table.columns.indexOf(name);
      return table.rows.every((row) => typeof row[index] === "number");
    })
    .map((name, order) => ({ name, order, count: distinct(name) }))
    .sort((a, b) => b.count - a.count || a.order - b.order)
    .map((item) => item.name);
}

export interface SensitivityData {
  /** 선 이름(기간 이름)들. 표의 열 순서를 따른다. */
  series: string[];
  points: Record<string, number | null>[];
  /** 가로축이 아닌 파라미터를 고정한 값. */
  fixed: { name: string; value: TableCell }[];
}

/**
 * 한 파라미터(`xParam`)를 가로축으로 놓고 지표 하나의 기간별 값을 모은다.
 * 가로축이 아닌 파라미터는 조합에서 가장 흔한 값으로 고정하고, 그 값을 가진 조합만 쓴다.
 */
export function sensitivityData(
  table: ReportTable,
  periods: ReportPeriod[],
  xParam: string,
  metric: string,
): SensitivityData {
  const xIndex = table.columns.indexOf(xParam);
  const others = varyingParams(table).filter((name) => name !== xParam);
  const fixed = others.map((name) => ({
    name,
    value: modeValue(table.rows.map((row) => row[table.columns.indexOf(name)])),
  }));
  const rows = table.rows.filter((row) =>
    fixed.every((item) => same(row[table.columns.indexOf(item.name)], item.value)),
  );
  const rank = (label: string) => {
    const found = periods.findIndex((period) => period.label === label);
    return found < 0 ? periods.length : found;
  };
  const columns = table.columns
    .map((name, index) => ({ column: parseColumn(name), index }))
    .filter((item) => item.column.kind === "metric" && item.column.metric === metric)
    .map((item) => ({
      index: item.index,
      label: periodName((item.column as { period: string }).period, periods),
    }))
    // 선 순서는 보고서 머리말의 기간 순서를 따른다(전체가 맨 앞). 머리말에 없는 기간은 뒤로.
    .sort((a, b) => rank(a.label) - rank(b.label));
  const points = rows
    .filter((row) => typeof row[xIndex] === "number")
    .map((row) => {
      const point: Record<string, number | null> = { x: row[xIndex] as number };
      for (const column of columns) {
        const value = row[column.index];
        point[column.label] = typeof value === "number" ? value : null;
      }
      return point;
    })
    .sort((a, b) => (a.x as number) - (b.x as number));
  return { series: columns.map((column) => column.label), points, fixed };
}

/** 기간별로 추천·대안 조합의 순손익을 묶음 막대용으로 모은다. 결과가 없는 칸은 `null`이다. */
export function periodComparison(
  periods: ReportPeriod[],
  recommended: ReportRecommendation[],
  results: SweepResult[],
): Record<string, string | number | null>[] {
  const byId = new Map(results.map((result) => [result.id, result]));
  return periods.map((period) => {
    const row: Record<string, string | number | null> = { period: period.label };
    for (const item of recommended) {
      const result = byId.get(item.ids[period.label]);
      row[item.label] = result ? result.summary.net_pnl : null;
    }
    return row;
  });
}

/** 날짜별 수익률(자산 / 초기자금 − 1). 같은 날 점이 여럿이면 마지막 값을 쓴다. */
export function equityRows(
  period: string,
  recommended: ReportRecommendation[],
  results: SweepResult[],
): Record<string, string | number | null>[] {
  const byId = new Map(results.map((result) => [result.id, result]));
  const days = new Map<string, Record<string, string | number | null>>();
  for (const item of recommended) {
    const result = byId.get(item.ids[period]);
    if (!result) continue;
    for (const point of result.daily_equity) {
      const day = point.time.slice(0, 10);
      const row = days.get(day) ?? { day };
      row[item.label] = point.equity / result.initial_capital - 1;
      days.set(day, row);
    }
  }
  return [...days.values()].sort((a, b) => String(a.day).localeCompare(String(b.day)));
}

/** 사유 문장에서 숫자와 끝의 괄호 설명을 걷어 같은 종류의 청산 이유를 한 묶음으로 만든다. */
export function normalizeReason(reason: string | null): string {
  if (!reason) return "이유 없음";
  const text = reason.replace(/\s*\([^()]*\)\s*$/, "").replace(/-?\d+(\.\d+)?%?/g, "#").trim();
  return text || "이유 없음";
}

export interface ReasonSummary {
  reason: string;
  count: number;
  netPnl: number;
  average: number;
}

/** 청산 이유별 거래 수와 순손익. 손익 크기가 큰 이유부터. */
export function reasonSummary(trades: SweepTrade[]): ReasonSummary[] {
  const groups = new Map<string, { count: number; netPnl: number }>();
  for (const trade of trades) {
    const key = normalizeReason(trade.exit_reason);
    const group = groups.get(key) ?? { count: 0, netPnl: 0 };
    group.count += 1;
    group.netPnl += trade.net_pnl;
    groups.set(key, group);
  }
  return [...groups.entries()]
    .map(([reason, group]) => ({ reason, count: group.count, netPnl: group.netPnl, average: group.netPnl / group.count }))
    .sort((a, b) => Math.abs(b.netPnl) - Math.abs(a.netPnl));
}
