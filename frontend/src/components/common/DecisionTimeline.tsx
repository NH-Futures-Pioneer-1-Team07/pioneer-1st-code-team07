import type { UIEventHandler } from "react";
import { formatNumber } from "../../data/format";
import styles from "./DecisionTimeline.module.css";

export interface DecisionRow {
  key?: string;
  reason?: string;
  at: string;
  action: string;
  price: number | null;
  quantity: number | null;
  score: number | null;
}

export const sideClass = (side: string) =>
  side === "매수" ? "positive" : side === "매도" ? "negative" : "";

export default function DecisionTimeline({
  rows,
  onScroll,
}: {
  rows: DecisionRow[];
  onScroll?: UIEventHandler<HTMLElement>;
}) {
  return (
    <div className={`table-wrap ${styles.decisions}`} onScroll={onScroll}>
      <div className={`${styles.decision} ${styles.decisionHead}`}>
        <span className={styles.index}>번호</span>
        <span>시각</span>
        <span />
        <span>판단</span>
        <span>가격</span>
        <span>수량</span>
        <span>점수</span>
      </div>
      {rows.map((row, index) => (
        <div key={row.key ?? `${row.at}-${index}`} className={styles.decision}>
          <span className={styles.index}>{index + 1}</span>
          <time>{row.at}</time>
          <span className={styles.timelineDot} />
          <span className={styles.action}>
            <strong className={sideClass(row.action)}>{row.action}</strong>
            {row.reason && <small title={row.reason}>{row.reason}</small>}
          </span>
          <span>{row.price === null ? "—" : formatNumber(row.price)}</span>
          <span>{row.quantity === null ? "—" : `${row.quantity}계약`}</span>
          <span className={row.score === null ? styles.noScore : styles.score}>
            {row.score === null ? (
              "—"
            ) : (
              <>
                {row.score}
                <small>점</small>
              </>
            )}
          </span>
        </div>
      ))}
    </div>
  );
}
