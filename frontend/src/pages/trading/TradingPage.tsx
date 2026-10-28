import { useState } from "react";
import { errorMessage } from "../../apis/client";
import { useMarketStream } from "../../apis/marketStream";
import { usePolling } from "../../apis/polling";
import {
  clearAccount,
  fetchAccount,
  fetchCandles,
  fetchOrderBook,
  fetchQuote,
  fetchRuns,
  fetchStatus,
  fetchStrategies,
  fetchStrategy,
  startTrading,
  stopTrading,
} from "../../apis/trading";
import { formatMoney, formatNumber } from "../../data/fixtures";
import {
  formatClock,
  instrumentLabel,
  phaseLabel,
  sideLabel,
  signed,
  statusMessage,
} from "../../data/tradingView";
import Icon from "../../components/common/Icon";
import ConfirmDialog from "../../components/common/ConfirmDialog";
import StrategySelect from "../../components/common/StrategySelect";
import PriceChart from "./components/PriceChart";
import RunHistory from "./components/RunHistory";
import styles from "./TradingPage.module.css";

const dash = "—";
const won = (value: number | null | undefined) =>
  value === null || value === undefined ? dash : formatNumber(value);
const sideClassName = (side: string | null) =>
  side === "buy" ? "positive" : "negative";
const pnlClass = (value: number | null | undefined) =>
  value === null || value === undefined || value === 0
    ? ""
    : value > 0
      ? "positive"
      : "negative";

export default function TradingPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [interval, setInterval] = useState("5");
  const [confirm, setConfirm] = useState<"stop" | "all" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const strategies = usePolling(fetchStrategies, 60000);
  const status = usePolling(fetchStatus, 2000);
  const account = usePolling(fetchAccount, 5000);
  const runs = usePolling(() => fetchRuns("paper"), 10000);

  const phase = status.data?.phase ?? "idle";
  const items = strategies.data ?? [];
  const activeId = status.data?.run?.strategy_id ?? null;
  const strategyId = activeId ?? selected ?? items[0]?.id ?? null;
  const running = phase !== "idle";
  const pending = phase === "stopping" || phase === "clearing";
  const clearing = status.data?.clear?.state === "running";

  const detail = usePolling(
    () => fetchStrategy(strategyId as string),
    600000,
    [strategyId],
    !!strategyId,
  );
  const instrument = detail.data?.instruments[0] ?? null;
  const code = instrument?.code ?? null;

  const quote = usePolling(() => fetchQuote(code as string), 3000, [code], !!code);
  const candles = usePolling(
    () => fetchCandles(code as string, interval),
    5000,
    [code, interval],
    !!code,
  );
  const book = usePolling(() => fetchOrderBook(code as string), 3000, [code], !!code);
  const stream = useMarketStream(code);

  const livePrice = stream.lastTrade?.price ?? quote.data?.price ?? null;
  const prevClose = quote.data?.prev_close ?? null;
  const changeRate =
    livePrice !== null && prevClose ? ((livePrice - prevClose) / prevClose) * 100 : null;
  const levels = (stream.book ?? book.data)?.levels.slice(0, 5) ?? [];
  const totalAsk = (stream.book ?? book.data)?.total_ask_quantity ?? null;
  const totalBid = (stream.book ?? book.data)?.total_bid_quantity ?? null;
  const askShare =
    totalAsk !== null && totalBid !== null && totalAsk + totalBid > 0
      ? (totalAsk / (totalAsk + totalBid)) * 100
      : 50;
  const maxQuantity = Math.max(
    1,
    ...levels.flatMap((level) => [level.ask_quantity ?? 0, level.bid_quantity ?? 0]),
  );

  const deposit = account.data?.deposit;
  const positions = account.data?.positions ?? [];
  const openOrders = account.data?.open_orders ?? [];
  const pnl = status.data?.pnl;
  const streamNote =
    stream.state === "live"
      ? "실시간 시세 수신 중"
      : stream.failure
        ? `시세 연결 문제: ${stream.failure}`
        : "시세 연결 중";
  const receivedAt = formatClock(stream.lastTrade?.time);

  const act = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setActionError(null);
    try {
      await action();
    } catch (failure) {
      setActionError(errorMessage(failure));
    } finally {
      setBusy(false);
      status.reload();
      account.reload();
      runs.reload();
    }
  };

  return (
    <>
      <div className={styles.pageHeading}>
        <div>
          <h1>모의매매</h1>
        </div>
        <span className={styles.accountLabel}>
          <Icon name="shield" size={15} />
          NH 모의계좌
        </span>
      </div>
      <div className={styles.summaryHeading}>
        <span>
          {account.error
            ? `계좌를 불러오지 못했습니다. ${account.error}`
            : account.data
              ? "5초마다 갱신"
              : "계좌를 불러오는 중…"}
        </span>
      </div>
      <div className={styles.metrics} role="group" aria-label="계좌 전체 자산">
        <div className={styles.metric}>
          <span>예탁자산</span>
          <strong>
            {won(deposit?.total_assets)}
            <small>원</small>
          </strong>
          <p>계좌에 맡긴 현금에 평가손익을 더한 전체 자산</p>
        </div>
        <div className={styles.metric}>
          <span>예탁현금</span>
          <strong>
            {won(deposit?.cash)}
            <small>원</small>
          </strong>
          <p>계좌에 맡겨 둔 현금</p>
        </div>
        <div className={styles.metric}>
          <span>주문 가능 금액</span>
          <strong>
            {won(deposit?.order_available_total)}
            <small>원</small>
          </strong>
          <p>새 주문에 쓸 수 있는 금액</p>
        </div>
        <div className={styles.metric}>
          <span>사용 증거금</span>
          <strong>
            {won(deposit?.initial_margin)}
            <small>원</small>
          </strong>
          <p>보유 포지션과 미체결 주문에 묶인 금액</p>
        </div>
      </div>
      <div className={styles.tradingGrid}>
        <section className={`panel ${styles.control}`} aria-labelledby="run-title">
          <div className="section-head">
            <h2 id="run-title">전략 운용</h2>
            <span
              className={`${styles.stateBadge} ${phase === "running" ? styles.running : ""}`}
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
                {quote.data?.contract && (
                  <span className="badge">{quote.data.contract}</span>
                )}
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
          </div>
          <div className={styles.quote}>
            <strong>{won(livePrice)}</strong>
            <span className={pnlClass(changeRate)}>
              {changeRate === null
                ? dash
                : `${changeRate > 0 ? "+" : ""}${changeRate.toFixed(2)}%`}
            </span>
          </div>
          <div className={styles.connection}>
            <span>
              <i />
              {streamNote}
            </span>
            <span>거래량 {won(stream.lastTrade?.cum_volume ?? quote.data?.volume)}계약</span>
            <span>수신 {receivedAt || dash}</span>
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
            <span>
              매도 잔량 <strong>{won(totalAsk)}</strong>
            </span>
            <div>
              <i style={{ width: `${askShare}%` }} />
              <b />
            </div>
            <span>
              매수 잔량 <strong>{won(totalBid)}</strong>
            </span>
          </div>
        </section>
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
          disabled={busy || pending || clearing}
          onClick={() => setConfirm("all")}
        >
          미체결 취소·전체 포지션 청산
        </button>
      </div>
      <div className={styles.status} role="status" aria-live="polite">
        {statusMessage(status.data, actionError ?? status.error)}
      </div>
      <div className={styles.accountGrid}>
        <section className={`panel ${styles.holdings}`} aria-labelledby="positions-title">
          <div className="section-head">
            <h2 id="positions-title">보유 포지션</h2>
            <span className="badge">{positions.length}</span>
          </div>
          {positions.length ? (
            <div className="table-wrap">
              <table className="data-table">
                <caption className="sr-only">계좌 전체 보유 포지션</caption>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>매매구분</th>
                    <th>수량</th>
                    <th>평균 진입가</th>
                    <th>현재가</th>
                    <th>평가손익</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((position) => (
                    <tr key={`${position.code}-${position.side}`}>
                      <td>{instrumentLabel(position.name)}</td>
                      <td className={sideClassName(position.side)}>
                        {sideLabel(position.side)}
                      </td>
                      <td>{won(position.quantity)}계약</td>
                      <td>{won(position.avg_price)}</td>
                      <td>{won(position.last_price)}</td>
                      <td className={pnlClass(position.pnl)}>
                        {position.pnl === null ? dash : signed(position.pnl, formatMoney)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty">보유 포지션이 없습니다.</p>
          )}
        </section>
        <section className={`panel ${styles.holdings}`} aria-labelledby="open-orders-title">
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
                    <tr key={order.order_no}>
                      <td>{order.code}</td>
                      <td>{formatClock(order.received_time) || order.received_time}</td>
                      <td className={sideClassName(order.side)}>{sideLabel(order.side)}</td>
                      <td>{won(order.price)}</td>
                      <td>
                        {won(order.quantity)} / {won(order.filled_quantity)} /{" "}
                        {won(order.remaining_quantity)}
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
      <RunHistory runs={runs.data} error={runs.error} />
      {confirm && (
        <ConfirmDialog
          title={
            confirm === "all" ? "계좌 전체를 정리할까요?" : "현재 운용을 종료할까요?"
          }
          action={confirm === "all" ? "계좌 전체 정리" : "운용 종료"}
          onClose={() => setConfirm(null)}
          onConfirm={() => {
            void act(confirm === "all" ? clearAccount : stopTrading);
            setConfirm(null);
          }}
        >
          <p>
            {confirm === "all"
              ? "계좌 전체의 신규 주문 판단을 멈추고, 기존 주문을 포함한 모든 미체결을 취소한 뒤 남은 포지션을 청산합니다."
              : "현재 운용의 판단을 멈추고, 해당 운용의 미체결 주문과 포지션을 정리합니다."}
          </p>
          <p>NH 모의계좌에 실제로 취소·청산 주문이 전송됩니다.</p>
        </ConfirmDialog>
      )}
    </>
  );
}
