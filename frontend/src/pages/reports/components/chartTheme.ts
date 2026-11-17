export const SERIES_COLORS = ["#ffb819", "#5795ff", "#49c99b", "#ff6675", "#b78cff", "#7fd1e8"];

export const axisProps = {
  stroke: "#20242c",
  tick: { fill: "#9299a4", fontSize: 11 },
  tickLine: false,
} as const;

export const tooltipStyle = {
  contentStyle: { background: "#171a20", border: "1px solid #20242c", borderRadius: 8, fontSize: 12 },
  labelStyle: { color: "#f5f6f7", marginBottom: 4 },
  itemStyle: { color: "#afb4bd" },
  cursor: { stroke: "#ffffff30" },
} as const;

export const CHART_HEIGHT = 280;
