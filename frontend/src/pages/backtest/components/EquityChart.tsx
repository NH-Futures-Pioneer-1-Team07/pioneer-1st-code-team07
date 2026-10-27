import { useEffect, useRef, useState } from "react";
import { formatMoney, formatNumber } from "../../../data/fixtures";
import type { TestRecord } from "../../../data/backtest";
import styles from "./EquityChart.module.css";

export default function EquityChart({ record }: { record: TestRecord }) {
  const frameRef = useRef<HTMLElement>(null);
  const [size, setSize] = useState({ w: 800, h: 280 });
  const curve = [
    220, 230, 239, 217, 220, 201, 213, 192, 203, 185, 187, 160, 169, 154, 162,
    138, 149, 132, 111, 119, 102, 113, 91, 82, 91, 72, 85, 60, 64, 48, 58, 40,
  ];

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
  const gridBottom = size.h - 44;
  const baseline = size.h - 26;
  const x = (index: number) =>
    left + (index * (right - left)) / (curve.length - 1);
  const y = (value: number) =>
    top + Math.min((value - 40) / 180, 1) * (gridBottom - top);
  const line = curve.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  return (
    <figure ref={frameRef} className={styles.equity}>
      <svg
        viewBox={`0 0 ${size.w} ${size.h}`}
        role="img"
        aria-label={`${record.title} 샘플 자산 변화: ${formatMoney(record.capital)}에서 ${formatMoney(record.capital + record.profit)}로 증가`}
      >
        <defs>
          <linearGradient
            id={`equity-fill-${record.id}`}
            x1="0"
            x2="0"
            y1="0"
            y2="1"
          >
            <stop offset="0%" stopColor="#FFB819" stopOpacity=".20" />
            <stop offset="100%" stopColor="#FFB819" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3].map((row) => {
          const gy = top + (row * (gridBottom - top)) / 3;
          return (
            <g key={row}>
              <line
                x1={left}
                y1={gy}
                x2={right + 8}
                y2={gy}
                stroke="#20242c"
                strokeDasharray="3 7"
              />
              <text x={right + 20} y={gy + 4} fill="#9299a4" fontSize="11">
                {formatNumber(
                  Math.round(
                    (record.capital + record.profit * (1 - row / 3)) / 10000,
                  ),
                )}
                만
              </text>
            </g>
          );
        })}
        <polygon
          points={`${left},${baseline} ${line} ${right},${baseline}`}
          fill={`url(#equity-fill-${record.id})`}
        />
        <polyline
          points={line}
          fill="none"
          stroke="#FFB819"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <circle cx={right} cy={top} r="4" fill="#FFB819" />
        <text x={left} y={size.h - 6} fill="#9299a4" fontSize="11">
          {record.startDate.slice(5).replace("-", ".")}
        </text>
        <text
          x={right}
          y={size.h - 6}
          textAnchor="end"
          fill="#9299a4"
          fontSize="11"
        >
          {record.endDate.slice(5).replace("-", ".")}
        </text>
      </svg>
      <figcaption className={styles.screenReader}>
        실제 전략 계산이 아닌 화면 확인용 자산 곡선입니다.
      </figcaption>
    </figure>
  );
}
