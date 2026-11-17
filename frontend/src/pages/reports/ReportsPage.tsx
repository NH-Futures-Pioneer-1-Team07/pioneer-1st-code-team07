import ReportDetailView from "./components/ReportDetailView";
import ReportList from "./components/ReportList";
import { useReportsPage } from "./useReportsPage";
import styles from "./ReportsPage.module.css";

export default function ReportsPage({ active }: { active: boolean }) {
  const ctl = useReportsPage(active);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeading}>
        <h1>검증 리포트</h1>
      </div>
      <div className={styles.columns}>
        <ReportList ctl={ctl} />
        <ReportDetailView ctl={ctl} />
      </div>
    </div>
  );
}
