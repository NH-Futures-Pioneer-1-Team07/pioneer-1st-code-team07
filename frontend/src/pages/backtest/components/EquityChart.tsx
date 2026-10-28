import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipContentProps } from "recharts";
import { fetchJournal } from "../../../apis/trading";
import type { BacktestMeta, BacktestResult } from "../../../apis/types";
import { equityPoints, returnText } from "../../../data/backtestView";
import type { EquityPoint } from "../../../data/backtestView";
import { formatMoney, formatNumber } from "../../../data/format";
import { sideLabel, signed } from "../../../data/tradingView";
import styles from "./EquityChart.module.css";

// 체결이 이만큼을 넘으면 툴팁 목록이 스크롤된다.
const SCROLL_FROM = 5;
const dayLabel = (day: string) => day.slice(5).replace("-", ".");
const pnlClass = (value: number) => (value > 0 ? "positive" : value < 0 ? "negative" : "");

function EquityTooltip({ active, payload }: TooltipContentProps) {
  const point = payload?.[0]?.payload as EquityPoint | undefined;
  if (!active || !point) return null;
  const scrolls = point.fills.length > SCROLL_FROM;
  const before = point.equity - point.change;
  const rate = before ? point.change / before : 0;
  return (
    <div className={styles.tooltip}>
      <header>
        <strong>{point.day.replaceAll("-", ".")}</strong>
        {point.fills.length > 0 && <span>거래 {point.fills.length}건</span>}
      </header>
      <div className={styles.equityValue}>{formatMoney(point.equity)}</div>
      <div className={`${styles.change} ${pnlClass(point.change)}`}>
        {signed(point.change, formatMoney)} <small>({returnText(rate)})</small>
      </div>
      {point.fills.length > 0 && (
        <ul data-fills className={scrolls ? styles.scroll : undefined}>
          {point.fills.map((fill, index) => (
            <li key={index}>
              <time>{fill.time}</time>
              <div>
                <p>
                  <b className={fill.side === "buy" ? styles.buy : styles.sell}>{sideLabel(fill.side)}</b>
                  <span>
                    {formatNumber(fill.quantity)}계약 · {formatNumber(fill.price)}
                  </span>
                </p>
                {fill.reason && <small>{fill.reason}</small>}
              </div>
            </li>
          ))}
        </ul>
      )}
      {scrolls && <p className={styles.hint}>마우스 휠로 {point.fills.length}건 모두 보기</p>}
    </div>
  );
}

export default function EquityChart({
  meta,
  result,
}: {
  meta: BacktestMeta;
  result: BacktestResult | null;
}) {
  const frameRef = useRef<HTMLElement>(null);
  const [fills, setFills] = useState<Awaited<ReturnType<typeof fetchJournal>>>([]);

  // 체결을 못 불러와도 자산 곡선은 그대로 보여 준다.
  useEffect(() => {
    let cancelled = false;
    setFills([]);
    if (result) {
      fetchJournal(meta, "fill")
        .then((lines) => !cancelled && setFills(lines))
        .catch(() => undefined);
    }
    return () => {
      cancelled = true;
    };
  }, [meta.strategy_id, meta.run_id, result]);

  // 체결이 많은 날의 툴팁은 마우스가 차트 위에 있어도 휠로 목록을 넘긴다.
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const onWheel = (event: WheelEvent) => {
      const list = frame.querySelector<HTMLElement>("[data-fills]");
      if (!list || list.scrollHeight <= list.clientHeight) return;
      list.scrollTop += event.deltaY;
      event.preventDefault();
    };
    frame.addEventListener("wheel", onWheel, { passive: false });
    return () => frame.removeEventListener("wheel", onWheel);
  }, []);

  const initial = result?.initial_capital ?? 0;
  const points = useMemo(
    () => (result ? equityPoints(result.equity_curve, initial, fills) : []),
    [result, initial, fills],
  );
  const values = points.map((point) => point.equity);
  const max = Math.max(...values, initial);
  const min = Math.min(...values, initial);
  const pad = (max - min) * 0.1 || Math.abs(initial) * 0.01 || 1;
  // 거래 건수 막대가 차트 아래쪽 1/5 안에 들어오도록 축 범위를 넓혀 둔다.
  const busiest = Math.max(1, ...points.map((point) => point.fills.length));
  const barColor = (change: number) => (change > 0 ? "var(--rise)" : change < 0 ? "var(--fall)" : "var(--text-tertiary)");

  return (
    <figure ref={frameRef} className={styles.equity}>
      {points.length > 0 && (
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={points.map((point) => ({ ...point, count: point.fills.length }))} margin={{ top: 16, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--data-line)" strokeOpacity={0.6} />
            <XAxis
              dataKey="day"
              tickFormatter={dayLabel}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              minTickGap={32}
            />
            <YAxis
              yAxisId="equity"
              orientation="right"
              width={64}
              domain={[min - pad, max + pad]}
              tickFormatter={(value: number) => `${formatNumber(Math.round(value / 10000))}만`}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
            />
            <YAxis yAxisId="count" hide domain={[0, busiest * 5]} />
            <ReferenceLine
              yAxisId="equity"
              y={initial}
              stroke="var(--text-tertiary)"
              strokeOpacity={0.5}
              strokeDasharray="2 5"
              label={{ value: "초기자금", position: "insideTopLeft", fill: "var(--text-tertiary)", fontSize: 11 }}
            />
            <Tooltip
              content={EquityTooltip}
              cursor={{ stroke: "var(--text-tertiary)", strokeOpacity: 0.4 }}
              isAnimationActive={false}
              wrapperStyle={{ zIndex: 10 }}
            />
            <Bar yAxisId="count" dataKey="count" maxBarSize={5} radius={[2, 2, 0, 0]} isAnimationActive={false}>
              {points.map((point) => (
                <Cell key={point.day} fill={barColor(point.change)} fillOpacity={0.75} />
              ))}
            </Bar>
            <Line
              yAxisId="equity"
              type="monotone"
              dataKey="equity"
              stroke="#FFB819"
              strokeWidth={1.75}
              dot={false}
              activeDot={{ r: 4, fill: "#FFB819", stroke: "#090B0E", strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}
      <figcaption className={styles.screenReader}>
        {result
          ? `자산 변화: ${formatMoney(result.initial_capital)}에서 ${formatMoney(result.final_equity)}로 변함. 하루마다 한 점이고 거래가 있던 날은 아래쪽 막대로 거래 건수를 표시합니다.`
          : "자산 변화 자료 없음"}
      </figcaption>
    </figure>
  );
}
