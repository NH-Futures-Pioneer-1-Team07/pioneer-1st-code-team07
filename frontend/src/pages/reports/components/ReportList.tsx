import type { ReportsController } from "../useReportsPage";
import { reportKey } from "../useReportsPage";
import { dotted } from "../../../data/format";
import styles from "./ReportList.module.css";

export default function ReportList({ ctl }: { ctl: ReportsController }) {
  const { list, items, selected, select } = ctl;
  return (
    <section className={`panel ${styles.list}`} aria-labelledby="reports-list-title">
      <div className="section-head">
        <div>
          <h2 id="reports-list-title">보고서</h2>
        </div>
        <span className="badge">{items.length}</span>
      </div>
      {list.error && <p className={styles.note}>목록을 불러오지 못했습니다. {list.error}</p>}
      {!list.error && list.data === null && <p className={styles.note}>불러오는 중…</p>}
      {list.data !== null && items.length === 0 && (
        <p className={styles.note}>
          저장된 보고서가 없습니다. 조합 탐색 결과로 보고서를 쓰면 여기에 나타납니다.
        </p>
      )}
      <ul className={styles.items}>
        {items.map((item) => {
          const chosen = selected !== undefined && reportKey(selected) === reportKey(item);
          return (
            <li key={reportKey(item)}>
              <button
                type="button"
                className={`${styles.item} ${chosen ? styles.chosen : ""}`}
                aria-pressed={chosen}
                onClick={() => select(item)}
              >
                <strong>{item.title ?? item.name}</strong>
                <span className={styles.strategy}>{item.strategy_id}</span>
                {item.error ? (
                  <span className={styles.error}>읽을 수 없음 · {item.error}</span>
                ) : (
                  <span className={styles.meta}>
                    {dotted(item.updated ?? "")} 갱신 · 결과 {item.result_count}건
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
