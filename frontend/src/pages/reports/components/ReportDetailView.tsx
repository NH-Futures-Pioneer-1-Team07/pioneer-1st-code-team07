import { usePolling } from "../../../apis/polling";
import { fetchStrategy } from "../../../apis/trading";
import type { ReportsController } from "../useReportsPage";
import { dotted } from "../../../data/format";
import { paramText, roleLabel } from "../../../data/reportView";
import MarkdownView from "./MarkdownView";
import ReportCharts from "./ReportCharts";
import TradesPanel from "./TradesPanel";
import ReportTable from "./ReportTable";
import styles from "./ReportDetailView.module.css";

export default function ReportDetailView({ ctl }: { ctl: ReportsController }) {
  const { list, selected, detail } = ctl;
  // 파라미터를 한글 이름·단위로 보이려고 전략 명세를 함께 읽는다. 못 읽으면 코드 이름과 원값으로 보인다.
  const strategy = usePolling(
    () => fetchStrategy(selected!.strategy_id),
    600000,
    [selected?.strategy_id],
    selected !== undefined && selected.error === null,
  );
  const specs = strategy.data?.parameters;

  if (list.data !== null && selected === undefined) {
    const broken = ctl.items.length > 0;
    return (
      <section className={`panel ${styles.detail}`}>
        <p className={styles.state}>
          {broken ? "읽을 수 있는 보고서가 없습니다. 왼쪽 목록의 오류 사유를 확인하세요." : "왼쪽에 보고서가 생기면 여기에 내용이 표시됩니다."}
        </p>
      </section>
    );
  }
  if (selected === undefined) {
    return (
      <section className={`panel ${styles.detail}`}>
        <p className={styles.state}>{list.error ? "보고서를 불러오지 못했습니다." : "불러오는 중…"}</p>
      </section>
    );
  }
  if (selected.error !== null) {
    return (
      <section className={`panel ${styles.detail}`} aria-live="polite">
        <h2>{selected.name}</h2>
        <p className={styles.errorText}>보고서를 읽을 수 없습니다. {selected.error}</p>
      </section>
    );
  }
  const report = detail.data;
  if (report === null) {
    return (
      <section className={`panel ${styles.detail}`} aria-live="polite">
        <p className={styles.state}>{detail.error ? `보고서를 불러오지 못했습니다. ${detail.error}` : "불러오는 중…"}</p>
      </section>
    );
  }
  const { meta } = report;
  return (
    <section className={`panel ${styles.detail}`} aria-labelledby="report-title">
      <header className={styles.head}>
        <h2 id="report-title">{meta.title}</h2>
        <p className={styles.question}>{meta.question}</p>
        <div className={styles.badges}>
          <span className="badge">{dotted(meta.updated)} 갱신</span>
          <span className="badge">결과 {meta.result_count}건</span>
          <span className="badge">{meta.author}</span>
          <span className="badge">{meta.strategy_id}</span>
        </div>
        {detail.error && <p className={styles.errorText}>최신 내용을 불러오지 못했습니다. {detail.error}</p>}
      </header>

      {meta.recommended.length > 0 && (
        <div className={styles.cards} aria-label="추천 조합">
          {meta.recommended.map((item) => (
            <article
              key={item.label}
              className={`${styles.card} ${item.role === "recommended" ? styles.primary : ""}`}
            >
              <span className={styles.role}>{roleLabel(item.role)}</span>
              <strong>{item.label}</strong>
              <div className={styles.chips}>
                {Object.entries(item.params).map(([name, value]) => (
                  <span key={name}>{paramText(name, value, specs)}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}

      <MarkdownView text={report.body} title={meta.title} />

      <ReportCharts report={report} specs={specs} />

      {meta.recommended.length > 0 && (
        <section className={styles.tableSection} aria-labelledby="report-trades-title">
          <h3 id="report-trades-title">거래</h3>
          <TradesPanel meta={meta} />
        </section>
      )}

      <section className={styles.tableSection} aria-labelledby="report-table-title">
        <h3 id="report-table-title">비교표</h3>
        {report.table === null ? (
          <p className={styles.state}>이 보고서에는 비교표(table.csv)가 없습니다.</p>
        ) : (
          <ReportTable table={report.table} periods={meta.periods} specs={specs} />
        )}
      </section>
    </section>
  );
}
