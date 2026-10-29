import type { TradingController } from "../useTradingPage";
import Icon from "../../../components/common/Icon";
import { won } from "../../../data/format";
import styles from "./AccountSummary.module.css";

export default function AccountSummary({ ctl }: { ctl: TradingController }) {
  const {
    account,
    deposit,
  } = ctl;
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
    </>
  );
}
