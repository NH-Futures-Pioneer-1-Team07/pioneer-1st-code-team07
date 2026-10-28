import { useEffect, useRef, useState } from "react";
import { formatMoney, formatNumber } from "../../../data/format";
import { equityLayout } from "../../../data/backtestView";
import type { BacktestResult } from "../../../apis/types";
import styles from "./EquityChart.module.css";

export default function EquityChart({
  id,
  result,
}: {
  id: string;
  result: BacktestResult | null;
}) {
  const frameRef = useRef<HTMLElement>(null);
  const [size, setSize] = useState({ w: 800, h: 280 });
  const curve = result?.equity_curve ?? [];

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const fit = () => {
      if (frame.clientWidth)
        setSize({ w: frame.clientWidth, h: frame.clientHeight });
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(frame);
    return () => observer.disconnect();
  }, []);

  const left = 4;
  const right = size.w - 76;
  const top = 16;
  const bottom = size.h - 44;
  const baseline = size.h - 26;
  const layout = equityLayout(curve, { left, right, top, bottom, baseline });
  const dayLabel = (time: string) => time.slice(5, 10).replace("-", ".");
  return (
    <figure ref={frameRef} className={styles.equity}>
      <svg
        viewBox={`0 0 ${size.w} ${size.h}`}
        role="img"
        aria-label={
          result
            ? `자산 변화: ${formatMoney(result.initial_capital)}에서 ${formatMoney(result.final_equity)}로 변함`
            : "자산 변화 자료 없음"
        }
      >
        <defs>
          <linearGradient id={`equity-fill-${id}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#FFB819" stopOpacity=".20" />
            <stop offset="100%" stopColor="#FFB819" stopOpacity="0" />
          </linearGradient>
        </defs>
        {layout.ticks.map((tick) => (
          <g key={tick.y}>
            <line
              x1={left}
              y1={tick.y}
              x2={right + 8}
              y2={tick.y}
              stroke="#20242c"
              strokeDasharray="3 7"
            />
            <text x={right + 20} y={tick.y + 4} fill="#9299a4" fontSize="11">
              {formatNumber(Math.round(tick.value / 10000))}만
            </text>
          </g>
        ))}
        {layout.line && (
          <>
            <polygon points={layout.area} fill={`url(#equity-fill-${id})`} />
            <polyline
              points={layout.line}
              fill="none"
              stroke="#FFB819"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </>
        )}
        {layout.last && (
          <circle cx={layout.last.x} cy={layout.last.y} r="4" fill="#FFB819" />
        )}
        {curve.length > 0 && (
          <>
            <text x={left} y={size.h - 6} fill="#9299a4" fontSize="11">
              {dayLabel(curve[0].time)}
            </text>
            <text
              x={right}
              y={size.h - 6}
              textAnchor="end"
              fill="#9299a4"
              fontSize="11"
            >
              {dayLabel(curve[curve.length - 1].time)}
            </text>
          </>
        )}
      </svg>
      <figcaption className={styles.screenReader}>
        하루마다 한 점씩 그린 자산 곡선입니다.
      </figcaption>
    </figure>
  );
}
