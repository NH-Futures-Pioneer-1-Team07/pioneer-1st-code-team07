import type { BacktestController } from "../useBacktestPage";
import Icon from "../../../components/common/Icon";
import EquityChart from "./EquityChart";
import { dotted, formatMoney, pnlClass } from "../../../data/format";
import { progressLabel, returnText, statusLabel } from "../../../data/backtestView";
import { formatDateTime, instrumentLabel, signed } from "../../../data/tradingView";
import styles from "./ResultPanel.module.css";

export default function ResultPanel({ ctl }: { ctl: BacktestController }) {
  const {
    startDate,
    endDate,
    active,
    formId,
    strategy,
    live,
    liveMeta,
    report,
    reportMeta,
    result,
    busy,
    percent,
  } = ctl;
  return (
    <section
      className={`panel ${styles.result}`}
      aria-labelledby={`${formId}-result-title`}
      aria-busy={busy}
    >
      <div className="section-head">
        <div>
          <h2 id={`${formId}-result-title`}>백테스트 결과</h2>
        </div>
      </div>
      {active && (
        <div className={styles.progressPanel} role="status">
          <div>
            <strong>{progressLabel(liveMeta?.progress)}</strong>
            <span>{percent}%</span>
          </div>
          <progress max="100" value={percent} aria-label="백테스트 진행률" />
          <p>
            {liveMeta
              ? `${liveMeta.strategy_name} · ${instrumentLabel(liveMeta.instrument.name)} · ${dotted(liveMeta.period.start)} — ${dotted(liveMeta.period.end)}`
              : "실행 정보를 불러오는 중…"}
          </p>
          {live.error && <p>{live.error}</p>}
        </div>
      )}
      {!active && reportMeta && (
        <div
          className={`${styles.progressPanel} ${reportMeta.status === "completed" ? styles.done : styles.idle}`}
          role="status"
        >
          <div>
            <strong className={styles.doneTitle}>
              {reportMeta.status === "completed" && <Icon name="check" size={16} />}
              {reportMeta.status === "completed"
                ? "백테스트가 완료됐어요"
                : `백테스트가 ${statusLabel(reportMeta.status)}로 끝났어요`}
            </strong>
            <span className={styles.doneSide}>
              {reportMeta.status === "completed" ? "100%" : statusLabel(reportMeta.status)}
            </span>
          </div>
          <progress
            max="100"
            value={reportMeta.status === "completed" ? 100 : 0}
            aria-label="백테스트 진행률"
          />
          <p>
            {formatDateTime(reportMeta.started_at)} · {reportMeta.strategy_name} ·{" "}
            {instrumentLabel(reportMeta.instrument.name)} ·{" "}
            {dotted(reportMeta.period.start)} — {dotted(reportMeta.period.end)}
          </p>
        </div>
      )}
      {!active && !reportMeta && (
        <div
          className={`${styles.progressPanel} ${styles.idle}`}
          role="status"
        >
          <div>
            <strong>
              {report.error ? "결과를 불러오지 못했어요" : "백테스트 실행 전이에요"}
            </strong>
            <span>0%</span>
          </div>
          <progress max="100" value={0} aria-label="백테스트 진행률" />
          <p>
            {report.error ??
              `${strategy?.name ?? "전략 선택"} · ${startDate ? dotted(startDate) : "시작일 선택"} — ${endDate ? dotted(endDate) : "종료일 선택"}`}
          </p>
        </div>
      )}
      {reportMeta && (
        <>
          <div className={styles.reportHeading}>
            <div>
              <strong>{reportMeta.strategy_name}</strong>
              <p>
                {instrumentLabel(reportMeta.instrument.name)} ·{" "}
                {dotted(reportMeta.period.start)} — {dotted(reportMeta.period.end)}
              </p>
            </div>
          </div>
          <div className={styles.performanceCards}>
            <div>
              <span>초기자금</span>
              <strong>{formatMoney(reportMeta.initial_capital)}</strong>
            </div>
            <div>
              <span>최종자산</span>
              <strong>{result ? formatMoney(result.final_equity) : "—"}</strong>
            </div>
            <div>
              <span>
                순손익 <small>비용 반영</small>
              </span>
              <strong className={result ? pnlClass(result.net_pnl) : ""}>
                {result ? signed(result.net_pnl, formatMoney) : "—"}
              </strong>
              {result && (
                <small className={pnlClass(result.net_pnl)}>
                  {returnText(result.return_rate)}
                </small>
              )}
            </div>
          </div>
          <div className={styles.chartHeading}>
            <h3>자산 변화</h3>
            <ul className={styles.chartLegend}>
              <li>
                <i data-mark="line" /> 노란 선: 하루마다 찍은 자산 변화
              </li>
              <li>
                <i data-mark="candle" /> 중간 봉: 그날의 일봉. 종가가 시가 이상이면 빨강, 낮으면 파랑
              </li>
              <li>
                <i data-mark="bar" /> 하단 막대: 그날 체결 건수. 이익이면 빨강, 손실이면 파랑
              </li>
            </ul>
          </div>
          <EquityChart meta={reportMeta} result={result} />
          <div className={styles.resultFooter}>
            <span>
              수수료 합계 <strong>{result ? formatMoney(result.fee) : "—"}</strong>
            </span>
            <span>
              {result
                ? `거래 ${result.trade_count}건 (승 ${result.win_count} · 패 ${result.loss_count}) · 최대 낙폭 ${formatMoney(result.max_drawdown)} (${(result.max_drawdown_rate * 100).toFixed(2)}%)`
                : "결과가 없습니다. 상세 기록에서 원인을 확인하세요."}
            </span>
          </div>
        </>
      )}
    </section>
  );
}
