import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Instrument } from "../../../data/fixtures";
import { formatNumber } from "../../../data/fixtures";
import styles from "./PriceChart.module.css";

const pattern = [
  0, 3, 1, 6, 5, 9, 6, 3, 8, 11, 7, 12, 14, 10, 13, 17, 15, 20, 18, 15, 19, 23,
  21, 25, 22, 26, 28, 25, 30, 32, 27, 31, 35, 33, 36, 39, 35, 38, 41, 39,
];

const BASE_WIDTH = 760;
const BASE_HEIGHT = 270;
const AXIS_WIDTH = 76;

export default function PriceChart({ instrument }: { instrument: Instrument }) {
  const [interval, setInterval] = useState("5분");
  const frameRef = useRef<HTMLDivElement>(null);
  const groupRef = useRef<HTMLDivElement>(null);
  const pillRef = useRef<HTMLSpanElement>(null);
  const [size, setSize] = useState({ w: BASE_WIDTH, h: BASE_HEIGHT });
  const down = instrument.change < 0;
  const values = pattern.map(
    (v, i) =>
      (down ? 42 - v : v) +
      (interval === "1분"
        ? (i % 3) * 2
        : interval === "일봉"
          ? -(i % 5) * 1.5
          : 0),
  );
  const unit = instrument.id === "samsung" ? 40 : 0.04;
  const base = instrument.price - values.at(-1)! * unit;
  const lastY = 180 - values.at(-1)! * 3;
  useEffect(() => {
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
  const sx = (size.w - AXIS_WIDTH) / (BASE_WIDTH - AXIS_WIDTH);
  const sy = size.h / BASE_HEIGHT;
  const axisX = size.w - AXIS_WIDTH + 16;
  return (
    <div className={styles.chart}>
      <div className={styles.toolbar}>
        <div ref={groupRef} role="group" aria-label="차트 주기">
          <span ref={pillRef} className={styles.pill} aria-hidden="true" />
          {["1분", "5분", "일봉"].map((item) => (
            <button
              key={item}
              aria-pressed={interval === item}
              className={interval === item ? styles.active : ""}
              onClick={() => setInterval(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <span>캔들 · 거래량</span>
      </div>
      <div ref={frameRef} className={styles.frame}>
        <svg
          viewBox={`0 0 ${size.w} ${size.h}`}
          role="img"
          aria-label={`${instrument.name} ${interval} 가격 캔들 및 거래량 샘플 차트`}
          className={styles.svg}
        >
          <g>
            <g transform={`scale(${sx} ${sy})`}>
              {[0, 1, 2, 3].map((row) => (
                <line
                  key={row}
                  x1="0"
                  y1={30 + row * 50}
                  x2="684"
                  y2={30 + row * 50}
                  stroke="var(--data-line)"
                  strokeDasharray="3 5"
                  vectorEffect="non-scaling-stroke"
                />
              ))}
              {values.map((value, index) => {
                const previous = values[Math.max(0, index - 1)];
                const rising = value >= previous;
                const color = rising ? "var(--rise)" : "var(--fall)";
                const x = 8 + index * 17;
                return (
                  <g key={index}>
                    <line
                      x1={x + 4}
                      x2={x + 4}
                      y1={180 - Math.max(value, previous) * 3 - 7}
                      y2={180 - Math.min(value, previous) * 3 + 8}
                      stroke={color}
                      vectorEffect="non-scaling-stroke"
                    />
                    <rect
                      x={x}
                      y={180 - Math.max(value, previous) * 3}
                      width="8"
                      height={Math.max(2, Math.abs(value - previous) * 3)}
                      fill={color}
                      rx="1"
                    />
                    <rect
                      x={x}
                      y={237 - (12 + ((index * 13) % 31))}
                      width="8"
                      height={12 + ((index * 13) % 31)}
                      fill={color}
                      opacity=".24"
                      rx="1"
                    />
                  </g>
                );
              })}
              <line
                x1="0"
                y1={lastY}
                x2="684"
                y2={lastY}
                stroke="var(--accent)"
                strokeDasharray="4 4"
                opacity=".65"
                vectorEffect="non-scaling-stroke"
              />
            </g>
            {[0, 1, 2, 3].map((row) => (
              <text
                key={row}
                x={axisX}
                y={(34 + row * 50) * sy}
                fill="var(--text-tertiary)"
                fontSize="11"
              >
                {formatNumber(base + (50 - row * 16.6) * unit)}
              </text>
            ))}
            <rect
              x={size.w - 67}
              y={lastY * sy - 11}
              width="67"
              height="22"
              rx="3"
              fill="var(--accent)"
            />
            <text
              x={size.w - 33.5}
              y={lastY * sy + 4}
              textAnchor="middle"
              fill="#1b1402"
              fontSize="11"
              fontWeight="600"
            >
              {formatNumber(instrument.price)}
            </text>
            {(interval === "일봉"
              ? ["09.01", "09.18", "10.08", "10.27"]
              : ["09:00", "09:30", "10:00", "10:30"]
            ).map((time, index) => (
              <text
                key={time}
                x={index * 213 * sx + 5}
                y={size.h - 7}
                fill="var(--text-tertiary)"
                fontSize="11"
              >
                {time}
              </text>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}
