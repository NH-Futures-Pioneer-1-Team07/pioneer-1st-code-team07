import { formatNumber } from "../../data/fixtures";
import styles from "./DecisionTimeline.module.css";

export interface DecisionRow {
  at: string;
  action: string;
  price: number | null;
  quantity: number | null;
  score: number | null;
}

export const sideClass = (side: string) =>
  side === "매수" ? "positive" : side === "매도" ? "negative" : "";

export default function DecisionTimeline({ rows }: { rows: DecisionRow[] }) {
  return (
    <div className={`table-wrap ${styles.decisions}`}>
      <div className={`${styles.decision} ${styles.decisionHead}`}>
        <span>시각</span>
        <span />
        <span>판단</span>
        <span>가격</span>
        <span>수량</span>
        <span>점수</span>
      </div>
      {rows.map((row) => (
        <div key={row.at} className={styles.decision}>
          <time>{row.at}</time>
          <span className={styles.timelineDot} />
          <strong className={sideClass(row.action)}>{row.action}</strong>
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
