import type { TradingController } from "../useTradingPage";
import styles from "./JudgmentPanel.module.css";

/** 운용 중인 전략이 설명하는 현재 판단. 전략이 구역을 정해 내려주고 화면은 그대로 그린다. */
export default function JudgmentPanel({ ctl }: { ctl: TradingController }) {
  const { running, status } = ctl;
  const sections = running ? (status.data?.judgment?.sections ?? []) : [];
  return (
    <section className={`panel ${styles.judgment}`} aria-labelledby="judgment-title">
      <div className="section-head">
        <h2 id="judgment-title">현재 판단</h2>
        <span className={styles.hint}>
          {sections.length > 0 ? "봉이 마감될 때마다 갱신됩니다" : "운용 중인 전략의 판단이 여기에 표시됩니다"}
        </span>
      </div>
      {sections.length > 0 && (
        <div className={styles.sections}>
          {sections.map((section) => (
            <article key={section.title} className={styles.section}>
              <header>
                <span>{section.title}</span>
                <strong className={styles[section.tone]}>{section.headline}</strong>
              </header>
              <dl>
                {section.rows.map(([name, value]) => (
                  <div key={name}>
                    <dt>{name}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
