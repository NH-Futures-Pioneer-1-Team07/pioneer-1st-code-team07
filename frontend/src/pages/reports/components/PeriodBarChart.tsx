import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReportMeta, SweepResult } from "../../../apis/types";
import { periodComparison } from "../../../data/reportCharts";
import { moneyText } from "../../../data/reportView";
import { CHART_HEIGHT, SERIES_COLORS, axisProps, tooltipStyle } from "./chartTheme";

export default function PeriodBarChart({ meta, results }: { meta: ReportMeta; results: SweepResult[] }) {
  const rows = useMemo(() => periodComparison(meta.periods, meta.recommended, results), [meta, results]);
  const show = (value: unknown) => (typeof value === "number" ? moneyText(value) : "—");
  return (
    <div role="img" aria-label="기간별 추천·대안 조합의 순손익">
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="#20242c" vertical={false} />
          <XAxis dataKey="period" {...axisProps} />
          <YAxis width={64} tickFormatter={show} {...axisProps} />
          <ReferenceLine y={0} stroke="#ffffff40" />
          <Tooltip {...tooltipStyle} formatter={(value) => show(value)} cursor={{ fill: "#ffffff10" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {meta.recommended.map((item, index) => (
            <Bar key={item.label} dataKey={item.label} fill={SERIES_COLORS[index % SERIES_COLORS.length]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
