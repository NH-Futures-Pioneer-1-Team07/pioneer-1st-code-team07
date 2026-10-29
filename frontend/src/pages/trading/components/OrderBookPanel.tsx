import type { TradingController } from "../useTradingPage";
import { won } from "../../../data/format";
import styles from "./OrderBookPanel.module.css";

export default function OrderBookPanel({ ctl }: { ctl: TradingController }) {
  const {
    book,
    livePrice,
    levels,
    maxQuantity,
  } = ctl;
  return (
    <section className={`panel ${styles.orderbook}`} aria-label="호가">
      <div className="section-head">
        <h2>호가</h2>
        <span className="badge">5호가</span>
      </div>
      {levels.length === 0 ? (
        <p className="empty">{book.error ? "호가를 불러오지 못했습니다." : "호가를 불러오는 중…"}</p>
      ) : (
        <>
          <div className={styles.bookLabels}>
            <span>매도</span>
            <span>가격</span>
            <span>매수</span>
          </div>
          {[...levels].reverse().map((level, i) => (
            <div key={`ask${i}`} className={styles.bookRow}>
              <span
                className="negative"
                style={{
                  background: `linear-gradient(to left, #5795ff14 ${((level.ask_quantity ?? 0) / maxQuantity) * 100}%, transparent 0)`,
                }}
              >
                {won(level.ask_quantity)}
              </span>
              <strong className="negative">{won(level.ask_price)}</strong>
              <span />
            </div>
          ))}
          <div className={styles.bookCurrent}>
            {won(livePrice)}
            <span>현재가</span>
          </div>
          {levels.map((level, i) => (
            <div key={`bid${i}`} className={styles.bookRow}>
              <span />
              <strong className="positive">{won(level.bid_price)}</strong>
              <span
                className="positive"
                style={{
                  background: `linear-gradient(to right, #ff667514 ${((level.bid_quantity ?? 0) / maxQuantity) * 100}%, transparent 0)`,
                }}
              >
                {won(level.bid_quantity)}
              </span>
            </div>
          ))}
        </>
      )}
    </section>
  );
}
