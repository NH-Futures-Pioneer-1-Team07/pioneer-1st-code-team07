import { useEffect, useId, useMemo, useRef, useState } from "react";
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
import type { BacktestMeta, BacktestResult, DailyBar } from "../../../apis/types";
import { equityPoints, returnText } from "../../../data/backtestView";
import type { EquityPoint } from "../../../data/backtestView";
import { formatMoney, formatNumber } from "../../../data/format";
import { sideLabel, signed } from "../../../data/tradingView";
import styles from "./EquityChart.module.css";

// 체결이 이만큼을 넘으면 툴팁 목록이 스크롤된다.
const SCROLL_FROM = 5;
const dayLabel = (day: string) => day.slice(5).replace("-", ".");
const pnlClass = (value: number) => (value > 0 ? "positive" : value < 0 ? "negative" : "");

const candleColor = (bar: DailyBar) => (bar.close >= bar.open ? "var(--rise)" : "var(--fall)");

/** 저가~고가 범위 막대 위에 심지와 몸통을 그린다. 일봉이 없는 날은 그리지 않는다. */
function Candle({ x, y, width, height, payload }: { x?: number; y?: number; width?: number; height?: number; payload?: EquityPoint }) {
  const bar = payload?.bar;
  if (!bar || x === undefined || y === undefined || width === undefined || height === undefined) return null;
  const span = bar.high - bar.low;
  const at = (value: number) => (span === 0 ? y : y + ((bar.high - value) / span) * height);
  const color = candleColor(bar);
  const center = x + width / 2;
  const body = Math.min(at(bar.open), at(bar.close));
  const bodyWidth = Math.max(3, width * 0.6);
  return (
    <g opacity={0.5}>
      <line x1={center} x2={center} y1={y} y2={y + height} stroke={color} strokeWidth={1} />
      <rect x={center - bodyWidth / 2} y={body} width={bodyWidth} height={Math.max(1.5, Math.abs(at(bar.open) - at(bar.close)))} fill={color} />
    </g>
  );
}

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
      {point.bar && (
        <dl className={styles.ohlc}>
          {([["시가", point.bar.open], ["고가", point.bar.high], ["저가", point.bar.low], ["종가", point.bar.close]] as const).map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{formatNumber(value)}</dd>
            </div>
          ))}
        </dl>
      )}
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
    () => (result ? equityPoints(result.equity_curve, initial, fills, result.daily_bars) : []),
    [result, initial, fills],
  );
  const values = points.map((point) => point.equity);
  const max = Math.max(...values, initial);
  const min = Math.min(...values, initial);
  const pad = (max - min) * 0.1 || Math.abs(initial) * 0.01 || 1;
  const priced = points.flatMap((point) => (point.bar ? [point.bar.low, point.bar.high] : []));
  const priceMin = Math.min(...priced);
  const priceMax = Math.max(...priced);
  const pricePad = (priceMax - priceMin) * 0.08 || 1;
  const busiest = Math.max(1, ...points.map((point) => point.fills.length));
  const chartData = points.map((point) => ({
    ...point,
    count: point.fills.length,
    range: point.bar ? [point.bar.low, point.bar.high] : null,
  }));
  // 위 차트와 아래 거래 막대의 가로 위치가 어긋나지 않도록 같은 여백과 축 너비를 쓴다.
  const margin = { top: 16, right: 8, bottom: 0, left: priced.length > 0 ? 0 : 8 };
  const syncId = useId();
  const barColor = (change: number) => (change > 0 ? "var(--rise)" : change < 0 ? "var(--fall)" : "var(--text-tertiary)");

  return (
    <figure ref={frameRef} className={styles.equity}>
      {points.length > 0 && (
        <div className={styles.main}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart syncId={syncId} data={chartData} margin={margin}>
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
            {priced.length > 0 && (
              <YAxis
                yAxisId="price"
                orientation="left"
                width={56}
                domain={[priceMin - pricePad, priceMax + pricePad]}
                tickFormatter={(value: number) => formatNumber(Math.round(value))}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              />
            )}
            <ReferenceLine
              yAxisId="equity"
              y={initial}
              stroke="var(--text-tertiary)"
              strokeOpacity={0.5}
              strokeDasharray="2 5"
            />
            <Tooltip
              content={EquityTooltip}
              cursor={{ stroke: "var(--text-tertiary)", strokeOpacity: 0.4 }}
              isAnimationActive={false}
              wrapperStyle={{ zIndex: 10 }}
            />
            {priced.length > 0 && (
              <Bar yAxisId="price" dataKey="range" shape={Candle} maxBarSize={9} isAnimationActive={false} />
            )}
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
        </div>
      )}
      {points.length > 0 && (
        <div className={styles.strip}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart syncId={syncId} data={chartData} margin={{ ...margin, top: 4 }}>
              <XAxis dataKey="day" hide />
              {priced.length > 0 && <YAxis yAxisId="pad" orientation="left" width={56} tick={false} tickLine={false} axisLine={false} />}
              <YAxis
                yAxisId="count"
                orientation="right"
                width={64}
                domain={[0, busiest]}
                ticks={[busiest]}
                interval={0}
                tickFormatter={(value: number) => `${value}건`}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              />
              <Tooltip content={() => null} cursor={{ stroke: "var(--text-tertiary)", strokeOpacity: 0.4 }} isAnimationActive={false} />
              <Bar yAxisId="count" dataKey="count" maxBarSize={5} radius={[2, 2, 0, 0]} isAnimationActive={false}>
                {points.map((point) => (
                  <Cell key={point.day} fill={barColor(point.change)} fillOpacity={0.75} />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
      <figcaption className={styles.screenReader}>
        {result
          ? `자산 변화: ${formatMoney(result.initial_capital)}에서 ${formatMoney(result.final_equity)}로 변함. 하루마다 한 점이고 거래가 있던 날은 아래쪽 막대로 거래 건수를 표시합니다.`
          : "자산 변화 자료 없음"}
      </figcaption>
    </figure>
  );
}
