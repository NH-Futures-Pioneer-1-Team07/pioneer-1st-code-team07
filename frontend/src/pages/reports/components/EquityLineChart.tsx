import { useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReportMeta, SweepResult } from "../../../apis/types";
import { equityRows } from "../../../data/reportCharts";
import { CHART_HEIGHT, SERIES_COLORS, axisProps, tooltipStyle } from "./chartTheme";
import styles from "./ReportCharts.module.css";

const percent = (value: unknown) => (typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—");

export default function EquityLineChart({ meta, results }: { meta: ReportMeta; results: SweepResult[] }) {
  const [period, setPeriod] = useState(meta.periods[0]?.label ?? "");
  const rows = useMemo(() => equityRows(period, meta.recommended, results), [period, meta, results]);
  return (
    <div className={styles.chart}>
      <div className={styles.toggle} role="group" aria-label="기간">
        {meta.periods.map((item) => (
          <button key={item.label} type="button" className={item.label === period ? styles.on : ""} aria-pressed={item.label === period} onClick={() => setPeriod(item.label)}>
            {item.label} <small>{item.start.slice(5).replace("-", ".")}~{item.end.slice(5).replace("-", ".")}</small>
          </button>
        ))}
      </div>
      {rows.length === 0 ? (
        <p className={styles.note}>이 기간의 자산 곡선 결과가 없습니다.</p>
      ) : (
        <div role="img" aria-label="추천·대안 조합의 수익률 곡선">
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid stroke="#20242c" vertical={false} />
              <XAxis dataKey="day" tickFormatter={(day: string) => day.slice(5).replace("-", ".")} minTickGap={24} {...axisProps} />
              <YAxis width={56} tickFormatter={percent} {...axisProps} />
              <ReferenceLine y={0} stroke="#ffffff40" />
              <Tooltip {...tooltipStyle} formatter={(value) => percent(value)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {meta.recommended.map((item, index) => (
                <Line key={item.label} dataKey={item.label} stroke={SERIES_COLORS[index % SERIES_COLORS.length]} strokeWidth={index === 0 ? 2.5 : 1.5} dot={false} connectNulls isAnimationActive={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
