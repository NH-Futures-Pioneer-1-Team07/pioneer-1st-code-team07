import ConfirmDialog from "../../components/common/ConfirmDialog";
import { clearAccount, stopTrading } from "../../apis/trading";
import type { MarketStatus } from "../../data/tradingView";
import AccountSection from "./components/AccountSection";
import AccountSummary from "./components/AccountSummary";
import ControlPanel from "./components/ControlPanel";
import MarketPanel from "./components/MarketPanel";
import OrderBookPanel from "./components/OrderBookPanel";
import RunHistory from "./components/RunHistory";
import { useTradingPage } from "./useTradingPage";
import styles from "./TradingPage.module.css";

export default function TradingPage({ onMarketStatus }: { onMarketStatus: (status: MarketStatus) => void }) {
  const ctl = useTradingPage(onMarketStatus);
  const { confirm, setConfirm, act, runStream } = ctl;

  return (
    <>
      <AccountSummary ctl={ctl} />
      <div className={styles.tradingGrid}>
        <ControlPanel ctl={ctl} />
        <MarketPanel ctl={ctl} />
        <OrderBookPanel ctl={ctl} />
      </div>
      <AccountSection ctl={ctl} />
      <RunHistory stream={runStream} />
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
