import ConfigPanel from "./components/ConfigPanel";
import CompareSection from "./components/CompareSection";
import HistoryPanel from "./components/HistoryPanel";
import ResultPanel from "./components/ResultPanel";
import { useBacktestPage } from "./useBacktestPage";
import styles from "./BacktestPage.module.css";

export default function BacktestPage() {
  const ctl = useBacktestPage();

  return (
    <div className={styles.page}>
      <span className={styles.screenReader} role="status">
        {ctl.announcement}
      </span>
      <div className={styles.pageHeading}>
        <div>
          <h1>백테스트</h1>
        </div>
      </div>
      <div className={styles.columns}>
        <ConfigPanel ctl={ctl} />
        <ResultPanel ctl={ctl} />
      </div>
      <HistoryPanel ctl={ctl} />
      <CompareSection ctl={ctl} />
    </div>
  );
}
