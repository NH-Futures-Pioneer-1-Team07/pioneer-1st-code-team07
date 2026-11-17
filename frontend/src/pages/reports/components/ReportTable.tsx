import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import type { ReportPeriod, ReportTable as Table } from "../../../apis/types";
import { pnlClass } from "../../../data/format";
import {
  METRIC_LABEL,
  type ParamSpecs,
  columnLabel,
  formatCell,
  isSigned,
  metricsIn,
  sortRows,
  visibleColumns,
} from "../../../data/reportView";
import styles from "./ReportTable.module.css";

const DEFAULT_METRICS = ["net_pnl", "max_drawdown_rate"];

export default function ReportTable({ table, periods, specs }: { table: Table; periods: ReportPeriod[]; specs?: ParamSpecs }) {
  const available = useMemo(() => metricsIn(table.columns), [table.columns]);
  const [metrics, setMetrics] = useState<Set<string>>(
    () => new Set(DEFAULT_METRICS.filter((metric) => available.includes(metric))),
  );
  const [sort, setSort] = useState<{ index: number; direction: "asc" | "desc" } | null>(null);

  const shown = visibleColumns(table.columns, metrics, periods);
  const rows = useMemo(
    () => (sort ? sortRows(table.rows, sort.index, sort.direction) : table.rows),
    [table.rows, sort],
  );

  const toggle = (metric: string) =>
    setMetrics((current) => {
      const next = new Set(current);
      if (next.has(metric)) next.delete(metric);
      else next.add(metric);
      return next;
    });
  const sortBy = (index: number) =>
    setSort((current) =>
      current?.index === index
        ? { index, direction: current.direction === "desc" ? "asc" : "desc" }
        : { index, direction: "desc" },
    );

  if (table.rows.length === 0) return <p className={styles.note}>비교표에 조합이 없습니다.</p>;
  return (
    <div className={styles.wrap}>
      {available.length > 0 && (
        <div className={styles.metrics} role="group" aria-label="비교할 지표">
          {available.map((metric) => (
            <button
              key={metric}
              type="button"
              className={metrics.has(metric) ? styles.on : ""}
              aria-pressed={metrics.has(metric)}
              onClick={() => toggle(metric)}
            >
              {METRIC_LABEL[metric]}
            </button>
          ))}
        </div>
      )}
      <div className="table-wrap" style={{ "--table-height": "auto" } as CSSProperties}>
        <table className={`data-table ${styles.table}`}>
          <thead>
            <tr>
              {shown.map((index) => {
                const name = table.columns[index];
                const active = sort?.index === index;
                return (
                  <th key={name} aria-sort={active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}>
                    <button type="button" className={styles.head} onClick={() => sortBy(index)}>
                      {columnLabel(name, periods, specs)}
                      <span aria-hidden="true">{active ? (sort.direction === "asc" ? " ▲" : " ▼") : ""}</span>
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {shown.map((index) => {
                  const name = table.columns[index];
                  const value = row[index];
                  const tone = isSigned(name) && typeof value === "number" ? pnlClass(value) : "";
                  return (
                    <td key={name} className={tone}>
                      {formatCell(name, value, specs)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={styles.note}>열 제목을 누르면 정렬합니다. 기간별 지표는 위에서 고른 것만 보입니다.</p>
    </div>
  );
}
