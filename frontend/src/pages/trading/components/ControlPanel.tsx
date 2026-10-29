import type { TradingController } from "../useTradingPage";
import Icon from "../../../components/common/Icon";
import StrategySelect from "../../../components/common/StrategySelect";
import { dash, formatMoney, formatNumber, pnlClass } from "../../../data/format";
import { instrumentLabel, phaseLabel, signed } from "../../../data/tradingView";
import { startTrading } from "../../../apis/trading";
import styles from "./ControlPanel.module.css";

export default function ControlPanel({ ctl }: { ctl: TradingController }) {
  const {
    setSelected,
    setConfirm,
    busy,
    strategies,
    status,
    phase,
    items,
    activeId,
    strategyId,
    running,
    pending,
    clearing,
    instrument,
    quote,
    pnl,
    act,
  } = ctl;
  return (
    <section className={`panel ${styles.control}`} aria-labelledby="run-title">
      <div className="section-head">
        <h2 id="run-title">전략 운용</h2>
        <span
          className={`badge state ${phase === "running" ? "running" : ""}`}
        >
          <i />
          {phaseLabel(phase)}
        </span>
      </div>
      <div className={styles.strategyField}>
        {strategies.error && (
          <p className="empty">전략을 불러오지 못했습니다. {strategies.error}</p>
        )}
        {strategyId && (
          <StrategySelect
            id="trading-strategy"
            items={items}
            selectedId={strategyId}
            disabled={running}
            onChange={setSelected}
          />
        )}
      </div>
      <div className={styles.instrument}>
        <span className={styles.instrumentLabel}>운용 종목</span>
        <div className={styles.instrumentCard}>
          <div>
            <strong>
              {instrument ? instrumentLabel(instrument.name) : dash}
            </strong>
          </div>
          <small>
            {instrument?.code ?? dash}
            {quote.data?.expiry ? ` · 만기 ${quote.data.expiry}` : ""}
          </small>
        </div>
      </div>
      <div className={styles.activeRun}>
        <span>운용 중인 전략</span>
        <strong>
          {running
            ? (items.find((item) => item.id === activeId)?.name ??
              status.data?.strategy ??
              activeId)
            : "현재 운용 없음"}
        </strong>
        <p>
          {running && status.data?.instrument
            ? instrumentLabel(status.data.instrument)
            : "전략을 선택해 시작하세요."}
        </p>
      </div>
      <div className={styles.performance}>
        <div>
          <span>현재 운용 평가손익</span>
          <strong className={pnlClass(pnl?.unrealized_pnl)}>
            {signed(pnl?.unrealized_pnl ?? 0, formatNumber)}
            <small>원</small>
          </strong>
        </div>
        <p>
          <span>실현손익</span>
          <span>{formatMoney(pnl?.realized_pnl ?? 0)}</span>
        </p>
        <p>
          <span>비용{pnl?.fee_estimated ? " (추정)" : ""}</span>
          <span>{formatMoney(pnl?.fee ?? 0)}</span>
        </p>
      </div>
      {!running ? (
        <button
          className={`button primary ${styles.fullButton}`}
          disabled={busy || !strategyId || clearing}
          onClick={() => void act(() => startTrading(strategyId as string))}
        >
          <Icon name="play" size={15} />
          운용 시작
        </button>
      ) : (
        <button
          className={`button danger ${styles.fullButton} ${styles.stopButton}`}
          disabled={busy || pending}
          onClick={() => setConfirm("stop")}
        >
          <Icon name="stop" size={14} />
          {pending ? "미체결 취소·청산 중…" : "운용 종료"}
        </button>
      )}
    </section>
  );
}
