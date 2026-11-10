import { useLayoutEffect, useRef, useState } from "react";
import type { Candle } from "../../../apis/types";
import { formatNumber } from "../../../data/format";
import { chartLayout, timeTicks } from "../../../data/tradingView";
import type { ResolvedLine } from "../../../data/tradingView";
import styles from "./PriceChart.module.css";

export const intervals = [
  { label: "1분", value: "1" },
  { label: "5분", value: "5" },
  { label: "일봉", value: "day" },
] as const;

const BASE_WIDTH = 760;
const BASE_HEIGHT = 270;
const AXIS_WIDTH = 76;

export default function PriceChart({
  name,
  candles,
  interval,
  onIntervalChange,
  error,
  lines = [],
}: {
  name: string;
  candles: Candle[] | null;
  interval: string;
  onIntervalChange: (value: string) => void;
  error: string | null;
  /** 전략이 판단에 쓰는 선. 선택한 주기에 맞는 것만 넘어온다 */
  lines?: ResolvedLine[];
}) {
  const frameRef = useRef<HTMLDivElement>(null);
  const groupRef = useRef<HTMLDivElement>(null);
  const pillRef = useRef<HTMLSpanElement>(null);
  const [size, setSize] = useState({ w: BASE_WIDTH, h: BASE_HEIGHT });
  const daily = interval === "day";
  const lineValues = lines.flatMap((line) => line.values.filter((value): value is number => value !== null));
  const layout = chartLayout(candles ?? [], size.w, size.h, AXIS_WIDTH, lineValues);
  const ticks = timeTicks(candles ?? [], daily);
  const slot = candles?.length ? (size.w - AXIS_WIDTH) / candles.length : 0;
  const lastPrice = candles?.length ? candles[candles.length - 1].close : null;
  const label = intervals.find((item) => item.value === interval)?.label ?? interval;

  useLayoutEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const fit = () => {
      if (!frame.clientWidth) return;
      setSize({
        w: Math.round(frame.clientWidth),
        h: Math.round(Math.max(frame.clientHeight, 180)),
      });
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(frame);
    return () => observer.disconnect();
  }, []);
  useLayoutEffect(() => {
    const selected = groupRef.current?.querySelector<HTMLButtonElement>(
      '[aria-pressed="true"]',
    );
    const pill = pillRef.current;
    if (!selected || !pill) return;
    pill.style.width = `${selected.offsetWidth}px`;
    pill.style.transform = `translateX(${selected.offsetLeft}px)`;
  }, [interval]);

  const axisX = size.w - AXIS_WIDTH + 16;
  // 가격 폭이 좁은 종목(스프레드 등)은 눈금에 소수를 보여 준다.
  const tickStep = layout.ticks.length > 1 ? Math.abs(layout.ticks[0].value - layout.ticks[1].value) : 1;
  const tickDigits = tickStep >= 1 ? 0 : tickStep >= 0.1 ? 1 : tickStep >= 0.01 ? 2 : 3;
  return (
    <div className={styles.chart}>
      <div className={styles.toolbar}>
        <div ref={groupRef} role="group" aria-label="차트 주기">
          <span ref={pillRef} className={styles.pill} aria-hidden="true" />
          {intervals.map((item) => (
            <button
              key={item.value}
              aria-pressed={interval === item.value}
              className={interval === item.value ? styles.active : ""}
              onClick={() => onIntervalChange(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <span>
          {error
            ? "차트를 불러오지 못했습니다"
            : candles === null
              ? "불러오는 중…"
              : "캔들 · 거래량"}
        </span>
      </div>
      {lines.length > 0 && (
        <ul className={styles.legend} aria-label="전략 판단 선">
          {lines.map((line) => (
            <li key={line.spec.label} tabIndex={0} aria-describedby={`line-tip-${line.spec.label}`}>
              <i
                style={{ background: line.color }}
                className={line.spec.kind !== "sma" ? styles.dashed : undefined}
              />
              {line.spec.label}
              <strong>{line.latest === null ? "—" : formatNumber(Number(line.latest.toFixed(4)))}</strong>
              <span role="tooltip" id={`line-tip-${line.spec.label}`} className={styles.lineTip}>
                {line.spec.description}
              </span>
            </li>
          ))}
        </ul>
      )}
      <div ref={frameRef} className={styles.frame}>
        <svg
          viewBox={`0 0 ${size.w} ${size.h}`}
          role="img"
          aria-label={`${name} ${label} 가격 캔들 및 거래량 차트`}
          className={styles.svg}
        >
          {layout.ticks.map((tick) => (
            <g key={tick.y}>
              <line
                x1="0"
                y1={tick.y}
                x2={size.w - AXIS_WIDTH}
                y2={tick.y}
                stroke="var(--data-line)"
                strokeDasharray="3 5"
              />
              <text x={axisX} y={tick.y + 4} fill="var(--text-tertiary)" fontSize="11">
                {formatNumber(Number(tick.value.toFixed(tickDigits)))}
              </text>
            </g>
          ))}
          {layout.shapes.map((shape, index) => {
            const color = shape.rising ? "var(--rise)" : "var(--fall)";
            const center = shape.x + shape.width / 2;
            return (
              <g key={candles?.[index].time ?? index}>
                <line x1={center} x2={center} y1={shape.wickTop} y2={shape.wickBottom} stroke={color} />
                <rect x={shape.x} y={shape.bodyTop} width={shape.width} height={shape.bodyHeight} fill={color} rx="1" />
                <rect x={shape.x} y={shape.volumeTop} width={shape.width} height={shape.volumeHeight} fill={color} opacity=".24" rx="1" />
              </g>
            );
          })}
          {lines.map((line) => {
            const points = line.values.flatMap((value, index) =>
              value === null ? [] : [`${(index * slot + slot / 2).toFixed(1)},${layout.y(value).toFixed(1)}`],
            );
            return points.length > 1 ? (
              <polyline
                key={line.spec.label}
                points={points.join(" ")}
                fill="none"
                stroke={line.color}
                strokeWidth="1.5"
                strokeDasharray={line.spec.kind !== "sma" ? "5 4" : undefined}
                opacity=".9"
              />
            ) : null;
          })}
          {layout.lastY !== null && lastPrice !== null && (
            <>
              <line
                x1="0"
                y1={layout.lastY}
                x2={size.w - AXIS_WIDTH}
                y2={layout.lastY}
                stroke="var(--accent)"
                strokeDasharray="4 4"
                opacity=".65"
              />
              <rect x={size.w - 67} y={layout.lastY - 11} width="67" height="22" rx="3" fill="var(--accent)" />
              <text x={size.w - 33.5} y={layout.lastY + 4} textAnchor="middle" fill="#1b1402" fontSize="11" fontWeight="600">
                {formatNumber(lastPrice)}
              </text>
            </>
          )}
          {ticks.map((tick) => (
            <text
              key={tick.index}
              x={Math.min(tick.index * slot + 5, size.w - AXIS_WIDTH - 36)}
              y={size.h - 7}
              fill="var(--text-tertiary)"
              fontSize="11"
            >
              {tick.label}
            </text>
          ))}
        </svg>
      </div>
    </div>
  );
}
