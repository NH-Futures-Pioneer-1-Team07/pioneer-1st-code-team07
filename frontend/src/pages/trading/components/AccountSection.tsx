import type { TradingController } from "../useTradingPage";
import Icon from "../../../components/common/Icon";
import { dash, formatMoney, pnlClass, won } from "../../../data/format";
import { formatClock, instrumentLabel, sideLabel, signed, statusMessage } from "../../../data/tradingView";
import styles from "./AccountSection.module.css";

const sideClassName = (side: string | null) => (side === "buy" ? "positive" : "negative");

export default function AccountSection({ ctl }: { ctl: TradingController }) {
  const {
    setConfirm,
    actionError,
    busy,
    status,
    pending,
    clearing,
    positions,
    openOrders,
  } = ctl;
  return (
    <>
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
    </>
  );
}
