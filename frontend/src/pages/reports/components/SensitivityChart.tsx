import { useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReportPeriod, ReportTable } from "../../../apis/types";
import { numericParams, sensitivityData } from "../../../data/reportCharts";
import { METRIC_LABEL, type ParamSpecs, columnLabel, formatCell, metricsIn, paramText } from "../../../data/reportView";
import { CHART_HEIGHT, SERIES_COLORS, axisProps, tooltipStyle } from "./chartTheme";
import styles from "./ReportCharts.module.css";

export default function SensitivityChart({ table, periods, specs }: { table: ReportTable; periods: ReportPeriod[]; specs?: ParamSpecs }) {
  const params = useMemo(() => numericParams(table), [table]);
  const metrics = useMemo(() => metricsIn(table.columns), [table.columns]);
  const [xParam, setXParam] = useState(params[0]);
  const [metric, setMetric] = useState(metrics.includes("net_pnl") ? "net_pnl" : metrics[0]);
  const x = params.includes(xParam) ? xParam : params[0];
  const data = useMemo(
    () => (x && metric ? sensitivityData(table, periods, x, metric) : null),
    [table, periods, x, metric],
  );

  if (!x || !metric || data === null) {
    return <p className={styles.note}>바꾼 숫자 파라미터가 없어 파라미터별 그래프를 그릴 수 없습니다.</p>;
  }
  const show = (value: unknown) => formatCell(`${metric}[·]`, typeof value === "number" ? value : null);
  return (
    <div className={styles.chart}>
      <div className={styles.controls}>
        <label>
          가로축
          <select value={x} onChange={(event) => setXParam(event.target.value)}>
            {params.map((name) => (
              <option key={name} value={name}>
                {columnLabel(name, periods, specs)}
              </option>
            ))}
          </select>
        </label>
        <div className={styles.toggle} role="group" aria-label="세로축 지표">
          {metrics.map((name) => (
            <button key={name} type="button" className={name === metric ? styles.on : ""} aria-pressed={name === metric} onClick={() => setMetric(name)}>
              {METRIC_LABEL[name]}
            </button>
          ))}
        </div>
      </div>
      <div role="img" aria-label={`${columnLabel(x, periods, specs)}에 따른 기간별 ${METRIC_LABEL[metric]}`}>
        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <LineChart data={data.points} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid stroke="#20242c" vertical={false} />
            <XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]} ticks={data.points.map((p) => p.x as number)} tickFormatter={(value) => formatCell(x, value as number, specs)} {...axisProps} />
            <YAxis width={64} tickFormatter={show} {...axisProps} />
            {metric === "net_pnl" && <ReferenceLine y={0} stroke="#ffffff40" />}
            <Tooltip {...tooltipStyle} formatter={(value) => show(value)} labelFormatter={(label) => `${columnLabel(x, periods, specs)} ${formatCell(x, typeof label === "number" ? label : String(label), specs)}`} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {data.series.map((name, index) => (
              <Line
                key={name}
                dataKey={name}
                stroke={SERIES_COLORS[index % SERIES_COLORS.length]}
                strokeWidth={index === 0 ? 2.5 : 1.5}
                dot={{ r: 3 }}
                connectNulls
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {data.fixed.length > 0 && (
        <p className={styles.note}>고정한 파라미터: {data.fixed.map((item) => paramText(item.name, item.value, specs)).join(" · ")} (가장 많이 시험한 값)</p>
      )}
    </div>
  );
}
