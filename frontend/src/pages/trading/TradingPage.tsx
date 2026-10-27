import { useEffect, useState } from "react";
import {
  formatMoney,
  formatNumber,
  instruments,
  instrumentTitle,
  sampleTime,
  strategies,
  strategyById,
  supportedInstruments,
} from "../../data/fixtures";
import {
  accountSummary,
  beginStop,
  createTradingState,
  finishStop,
  remaining,
  startRun,
} from "../../data/trading";
import Icon from "../../components/common/Icon";
import ConfirmDialog from "../../components/common/ConfirmDialog";
import StrategySelect from "../../components/common/StrategySelect";
import PriceChart from "./components/PriceChart";
import RunHistory from "./components/RunHistory";
import styles from "./TradingPage.module.css";

const instrumentLabel = (id: string) => {
  const item = instruments.find((candidate) => candidate.id === id);
  return item ? instrumentTitle(item) : "";
};

export default function TradingPage() {
  const [strategyId, setStrategyId] = useState(strategies[0].id);
  const strategy = strategyById(strategyId);
  const [state, setState] = useState(createTradingState);
  const [confirm, setConfirm] = useState<"stop" | "all" | null>(null);
  const instrument = supportedInstruments(strategy)[0];
  const active = state.runs.find((run) => run.id === state.activeRunId);
  const pending = state.phase === "stopping" || state.phase === "clearing";
  const openOrders = state.orders.filter((order) => remaining(order) > 0);
  const account = accountSummary(state);
  useEffect(() => {
    if (!pending) return;
    const timeout = window.setTimeout(
      () => setState((current) => finishStop(current)),
      1400,
    );
    return () => window.clearTimeout(timeout);
  }, [pending]);

  return (
    <>
      <div className={styles.pageHeading}>
        <div>
          <h1>모의매매</h1>
        </div>
        <span className={styles.accountLabel}>
          <Icon name="shield" size={15} />
          NH 모의계좌 <strong>DEMO-0001</strong>
        </span>
      </div>
      <div className={styles.summaryHeading}>
        <span>기준 {sampleTime} · 샘플</span>
      </div>
      <div className={styles.metrics} role="group" aria-label="계좌 전체 자산">
        <div className={styles.metric}>
          <span>예탁자산</span>
          <strong>
            {formatNumber(account.assets)}
            <small>원</small>
          </strong>
          <p>계좌에 맡긴 현금에 평가손익을 더한 전체 자산</p>
        </div>
        <div className={styles.metric}>
          <span>예탁현금</span>
          <strong>
            {formatNumber(account.cash)}
            <small>원</small>
          </strong>
          <p>계좌에 맡겨 둔 현금</p>
        </div>
        <div className={styles.metric}>
          <span>주문 가능 금액</span>
          <strong>
            {formatNumber(account.orderable)}
            <small>원</small>
          </strong>
          <p>새 주문에 쓸 수 있는 금액 (예탁현금 − 사용 증거금)</p>
        </div>
        <div className={styles.metric}>
          <span>사용 증거금</span>
          <strong>
            {formatNumber(account.margin)}
            <small>원</small>
          </strong>
          <p>보유 포지션과 미체결 주문에 묶인 금액</p>
        </div>
      </div>
      <div className={styles.tradingGrid}>
        <section
          className={`panel ${styles.control}`}
          aria-labelledby="run-title"
        >
          <div className="section-head">
            <h2 id="run-title">전략 운용</h2>
            <span
              className={`${styles.stateBadge} ${active ? styles.running : ""}`}
            >
              <i />
              {state.phase === "running"
                ? "운용 중"
                : pending
                  ? "정리 중"
                  : "대기"}
            </span>
          </div>
          <div className={styles.strategyField}>
            <StrategySelect
              id="trading-strategy"
              strategy={strategy}
              onChange={setStrategyId}
            />
          </div>
          <div className={styles.instrument}>
            <span className={styles.instrumentLabel}>운용 종목</span>
            <div className={styles.instrumentCard}>
              <div>
                <strong>{instrument.name}</strong>
                <span className="badge">{instrument.contract}</span>
              </div>
              <small>
                {instrument.code} · 만기 {instrument.expiry}
              </small>
            </div>
          </div>
          <div className={styles.activeRun}>
            <span>운용 중인 전략</span>
            <strong>{active?.strategy.name ?? "현재 운용 없음"}</strong>
            <p>
              {active
                ? instrumentTitle(active.instrument)
                : "전략과 종목을 선택해 시작하세요."}
            </p>
          </div>
          <div className={styles.performance}>
            <div>
              <span>현재 운용 평가손익</span>
              <strong className={active ? "positive" : ""}>
                {active ? `+${formatNumber(active.pnl)}` : "0"}
                <small>원</small>
              </strong>
            </div>
            <p>
              <span>실현손익</span>
              <span>0원</span>
            </p>
            <p>
              <span>비용</span>
              <span>{formatNumber(active?.cost ?? 0)}원</span>
            </p>
          </div>
          {state.phase === "idle" ? (
            <button
              className={`button primary ${styles.fullButton}`}
              onClick={() =>
                setState((current) => startRun(current, strategy, instrument))
              }
            >
              <Icon name="play" size={15} />
              운용 시작
            </button>
          ) : (
            <button
              className={`button danger ${styles.fullButton} ${styles.stopButton}`}
              disabled={pending}
              onClick={() => setConfirm("stop")}
            >
              <Icon name="stop" size={14} />
              {pending ? "미체결 취소·청산 중…" : "운용 종료"}
            </button>
          )}
        </section>
        <section
          className={`panel ${styles.market}`}
          aria-labelledby="market-title"
        >
          <div className={styles.marketHeader}>
            <div>
              <div className={styles.marketName}>
                <span className={styles.symbolAvatar}>
                  {instrument.id === "samsung" ? "S" : "K"}
                </span>
                <h2 id="market-title">{instrument.name}</h2>
              </div>
              <p className={styles.instrumentMeta}>
                {instrument.code} · 만기 {instrument.expiry}
              </p>
            </div>
          </div>
          <div className={styles.quote}>
            <strong>{formatNumber(instrument.price)}</strong>
            <span className={instrument.change >= 0 ? "positive" : "negative"}>
              {instrument.change >= 0 ? "+" : ""}
              {instrument.change}%
            </span>
          </div>
          <div className={styles.connection}>
            <span>
              <i />
              시세 연결 예시
            </span>
            <span>거래량 {formatNumber(instrument.volume)}계약</span>
            <span>수신 {sampleTime.slice(-8)} (고정 샘플)</span>
          </div>
          <PriceChart instrument={instrument} />
          <div className={styles.bookSummary}>
            <span>
              매도 잔량 <strong>1,284</strong>
            </span>
            <div>
              <i />
              <b />
            </div>
            <span>
              매수 잔량 <strong>1,652</strong>
            </span>
          </div>
        </section>
        <section className={`panel ${styles.orderbook}`} aria-label="호가 샘플">
          <div className="section-head">
            <h2>호가</h2>
            <span className="badge">5호가</span>
          </div>
          <div className={styles.bookLabels}>
            <span>매도</span>
            <span>가격</span>
            <span>매수</span>
          </div>
          {Array.from({ length: 5 }, (_, i) => 5 - i).map((n, i) => (
            <div key={`ask${n}`} className={styles.bookRow}>
              <span
                className="negative"
                style={{
                  background: `linear-gradient(to left, #5795ff14 ${30 + i * 12}%, transparent ${30 + i * 12}%)`,
                }}
              >
                {[186, 248, 329, 215, 306][i]}
              </span>
              <strong className="negative">
                {formatNumber(
                  instrument.price +
                    n * (instrument.id === "samsung" ? 100 : 0.05),
                )}
              </strong>
              <span />
            </div>
          ))}
          <div className={styles.bookCurrent}>
            {formatNumber(instrument.price)}
            <span>현재가</span>
          </div>
          {[1, 2, 3, 4, 5].map((n, i) => (
            <div key={`bid${n}`} className={styles.bookRow}>
              <span />
              <strong className="positive">
                {formatNumber(
                  instrument.price -
                    n * (instrument.id === "samsung" ? 100 : 0.05),
                )}
              </strong>
              <span
                className="positive"
                style={{
                  background: `linear-gradient(to right, #ff667514 ${78 - i * 12}%, transparent ${78 - i * 12}%)`,
                }}
              >
                {[426, 368, 291, 312, 255][i]}
              </span>
            </div>
          ))}
        </section>
      </div>
      <div className={styles.accountBar}>
        <div>
          <Icon name="shield" size={18} />
          <div>
            <strong>계좌 전체 정리</strong>
            <p>현재 운용과 기존 계좌의 모든 미체결·보유 포지션을 정리합니다.</p>
          </div>
        </div>
        <button
          className="button danger"
          disabled={pending}
          onClick={() => setConfirm("all")}
        >
          미체결 취소·전체 포지션 청산
        </button>
      </div>
      <div className={styles.status} role="status" aria-live="polite">
        {state.message}
      </div>
      <div className={styles.accountGrid}>
        <section
          className={`panel ${styles.holdings}`}
          aria-labelledby="positions-title"
        >
          <div className="section-head">
            <h2 id="positions-title">보유 포지션</h2>
            <span className="badge">{state.positions.length}</span>
          </div>
          {state.positions.length ? (
            <div className="table-wrap">
              <table className="data-table">
                <caption className="sr-only">계좌 전체 보유 포지션</caption>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>구분</th>
                    <th>매매구분</th>
                    <th>수량</th>
                    <th>평균 진입가</th>
                    <th>현재가</th>
                    <th>평가손익</th>
                  </tr>
                </thead>
                <tbody>
                  {state.positions.map((position) => (
                    <tr key={position.id}>
                      <td>{instrumentLabel(position.instrumentId)}</td>
                      <td>{position.runId ? "현재 운용" : "기존 계좌"}</td>
                      <td
                        className={
                          position.side === "매수" ? "positive" : "negative"
                        }
                      >
                        {position.side}
                      </td>
                      <td>{position.quantity}계약</td>
                      <td>{formatNumber(position.average)}</td>
                      <td>{formatNumber(position.price)}</td>
                      <td className="positive">+{formatMoney(position.pnl)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty">보유 포지션이 없습니다.</p>
          )}
        </section>
        <section
          className={`panel ${styles.holdings}`}
          aria-labelledby="open-orders-title"
        >
          <div className="section-head">
            <h2 id="open-orders-title">미체결 주문</h2>
            <span className="badge">{openOrders.length}</span>
          </div>
          {openOrders.length ? (
            <div className="table-wrap">
              <table className={`data-table ${styles.ordersTable}`}>
                <caption className="sr-only">계좌 전체 미체결 주문</caption>
                <colgroup>
                  <col style={{ width: "26%" }} />
                  <col style={{ width: "28%" }} />
                  <col style={{ width: "12%" }} />
                  <col style={{ width: "14%" }} />
                  <col style={{ width: "20%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>시각</th>
                    <th>매매구분</th>
                    <th>가격</th>
                    <th>주문 / 체결 / 잔량</th>
                  </tr>
                </thead>
                <tbody>
                  {openOrders.map((order) => (
                    <tr key={order.id}>
                      <td>{instrumentLabel(order.instrumentId)}</td>
                      <td>{order.at}</td>
                      <td
                        className={
                          order.side === "매수" ? "positive" : "negative"
                        }
                      >
                        {order.side}
                      </td>
                      <td>{formatNumber(order.price)}</td>
                      <td>
                        {order.quantity} / {order.filled} / {remaining(order)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty">미체결 주문이 없습니다.</p>
          )}
        </section>
      </div>
      <RunHistory runs={state.runs} />
      {confirm && (
        <ConfirmDialog
          title={
            confirm === "all"
              ? "계좌 전체를 정리할까요?"
              : "현재 운용을 종료할까요?"
          }
          action={confirm === "all" ? "계좌 전체 정리" : "운용 종료"}
          onClose={() => setConfirm(null)}
          onConfirm={() => {
            setState((current) => beginStop(current, confirm === "all"));
            setConfirm(null);
          }}
        >
          <p>
            {confirm === "all"
              ? "계좌 전체의 신규 주문 판단을 멈추고, 기존 주문을 포함한 모든 미체결을 취소한 뒤 남은 포지션을 청산합니다."
              : "현재 운용의 판단을 멈추고, 해당 운용의 미체결 주문과 포지션을 정리합니다. 기존 계좌의 주문과 포지션은 유지합니다."}
          </p>
          <p>화면 검토용 샘플 동작이며 실제 주문을 전송하지 않습니다.</p>
        </ConfirmDialog>
      )}
    </>
  );
}
