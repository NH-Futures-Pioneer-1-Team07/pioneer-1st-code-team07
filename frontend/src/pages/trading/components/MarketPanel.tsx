import type { TradingController } from "../useTradingPage";
import PriceChart from "./PriceChart";
import { dash, pnlClass, won } from "../../../data/format";
import { instrumentLabel } from "../../../data/tradingView";
import styles from "./MarketPanel.module.css";

export default function MarketPanel({ ctl }: { ctl: TradingController }) {
  const {
    interval,
    setInterval,
    instrument,
    quote,
    candles,
    stream,
    livePrice,
    changeRate,
    totalAsk,
    totalBid,
    askShare,
    receivedAt,
  } = ctl;
  return (
    <section className={`panel ${styles.market}`} aria-labelledby="market-title">
      <div className={styles.marketHeader}>
        <div>
          <div className={styles.marketName}>
            <span className={styles.symbolAvatar}>
              {(quote.data?.name ?? "").slice(0, 1) || dash}
            </span>
            <h2 id="market-title">
              {instrument ? instrumentLabel(instrument.name) : dash}
            </h2>
          </div>
          <p className={styles.instrumentMeta}>
            {instrument?.code ?? dash}
            {quote.data?.expiry ? ` · 만기 ${quote.data.expiry}` : ""}
          </p>
        </div>
        <div className={styles.quoteBlock}>
          <div className={styles.quote}>
            <strong>{won(livePrice)}</strong>
            <span className={pnlClass(changeRate)}>
              {changeRate === null
                ? dash
                : `${changeRate > 0 ? "+" : ""}${changeRate.toFixed(2)}%`}
            </span>
          </div>
          <div className={styles.connection}>
            <span>거래량 {won(stream.lastTrade?.cum_volume ?? quote.data?.volume)}계약</span>
            <span>수신 {receivedAt || dash}</span>
          </div>
        </div>
      </div>
      {quote.error && <p className="empty">시세를 불러오지 못했습니다. {quote.error}</p>}
      <PriceChart
        name={instrument?.name ?? ""}
        candles={candles.data}
        interval={interval}
        onIntervalChange={setInterval}
        error={candles.error}
      />
      <div className={styles.bookSummary}>
        <div className={styles.bookLegend}>
          <span>
            매도 잔량 <strong>{won(totalAsk)}</strong>
          </span>
          <span>
            매수 잔량 <strong>{won(totalBid)}</strong>
          </span>
        </div>
        <div className={styles.bookBar}>
          <i style={{ flexBasis: `${askShare}%` }} />
          <b />
        </div>
      </div>
    </section>
  );
}
