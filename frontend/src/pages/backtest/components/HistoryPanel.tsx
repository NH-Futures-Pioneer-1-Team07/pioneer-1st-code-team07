import type { BacktestController } from "../useBacktestPage";
import { dotted, formatMoney, formatNumber, pnlClass } from "../../../data/format";
import { formatDateTime, instrumentLabel, runKey, signed } from "../../../data/tradingView";
import { percentText, statusLabel } from "../../../data/backtestView";
import RecordDetail from "../../../components/common/RecordDetail";
import { scrollToPanel } from "../../../components/common/scrollToPanel";
import SplitPanel, { PanelCloseButton } from "../../../components/common/SplitPanel";
import styles from "./HistoryPanel.module.css";

export default function HistoryPanel({ ctl }: { ctl: BacktestController }) {
  const {
    formId,
    runs,
    list,
    selected,
    detailOpen,
    setDetailOpen,
    setSelectedKey,
    splitRef,
    reportMeta,
  } = ctl;
  const listPanel = (
    <section
      className={`panel ${styles.history}`}
      aria-labelledby={`${formId}-history-title`}
    >
      <div className="section-head">
        <div>
          <h2 id={`${formId}-history-title`}>실행 이력</h2>
        </div>
        <span className="badge">{list.length}</span>
      </div>
      {runs.error && <p className="empty">이력을 불러오지 못했습니다. {runs.error}</p>}
      {!runs.error && runs.data === null && <p className="empty">불러오는 중…</p>}
      {runs.data !== null && list.length === 0 && (
        <p className="empty">백테스트 이력이 없습니다.</p>
      )}
      {list.length > 0 && (
        <div className="table-wrap">
          <table className={`data-table run-table ${styles.historyTable}`}>
            <thead>
              <tr>
                <th>번호</th>
                <th>실행 일시</th>
                <th>전략</th>
                <th>종목</th>
                <th>테스트 기간</th>
                <th>초기자금</th>
                <th>슬리피지</th>
                <th>순손익</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              {list.map((run, index) => {
                const chosen = detailOpen && selected !== undefined && runKey(selected) === runKey(run);
                return (
                  <tr
                    key={runKey(run)}
                    className={`clickable ${chosen ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedKey(runKey(run));
                      setDetailOpen(true);
                      scrollToPanel(splitRef.current);
                    }}
                  >
                    <td className="index">{list.length - index}</td>
                    <td>
                      <button
                        type="button"
                        className={styles.historyButton}
                        aria-pressed={chosen}
                        aria-label={`${formatDateTime(run.started_at)} 실행 상세 보기`}
                      >
                        {formatDateTime(run.started_at)}
                      </button>
                    </td>
                    <td>
                      <strong>{run.strategy_name}</strong>
                    </td>
                    <td>{instrumentLabel(run.instrument.name)}</td>
                    <td>
                      {run.period
                        ? `${dotted(run.period.start)} — ${dotted(run.period.end)}`
                        : "—"}
                    </td>
                    <td>
                      {run.initial_capital === undefined
                        ? "—"
                        : formatMoney(run.initial_capital)}
                    </td>
                    <td>
                      {run.assumptions?.slippage?.ticks == null
                        ? "—"
                        : `${run.assumptions.slippage.ticks}틱`}
                    </td>
                    <td className={run.net_pnl === null ? "" : pnlClass(run.net_pnl)}>
                      {run.net_pnl === null ? "—" : signed(run.net_pnl, formatMoney)}
                    </td>
                    <td>
                      <span
                        className={run.status === "completed" ? styles.complete : undefined}
                      >
                        {statusLabel(run.status)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );

  const detailPanel = (
    <>
      <div className="section-head">
        <div>
          <span className="eyebrow">
            {reportMeta ? formatDateTime(reportMeta.started_at) : ""}
          </span>
          <h2 id={`${formId}-detail-title`}>실행 상세 기록</h2>
        </div>
        <PanelCloseButton label="실행 상세 기록 닫기" onClick={() => setDetailOpen(false)} />
      </div>
      {reportMeta && (
        <>
          <dl className={styles.snapshot}>
            <div>
              <dt>테스트 기간</dt>
              <dd>
                {dotted(reportMeta.period.start)} — {dotted(reportMeta.period.end)}
              </dd>
            </div>
            <div>
              <dt>초기자금</dt>
              <dd>{formatMoney(reportMeta.initial_capital)}</dd>
            </div>
            <div>
              <dt>비용</dt>
              <dd>체결대금의 {percentText(reportMeta.assumptions.fee.rate)}</dd>
            </div>
            <div>
              <dt>슬리피지</dt>
              <dd>
                {reportMeta.assumptions.slippage.ticks}틱
                {reportMeta.assumptions.slippage.tick_size !== null &&
                  `(${formatNumber(reportMeta.assumptions.slippage.tick_size)})`}{" "}
                · {reportMeta.assumptions.slippage.direction}
              </dd>
            </div>
          </dl>
          <RecordDetail meta={reportMeta} />
          <p className={styles.endNotice}>
            <span aria-hidden="true">ⓘ</span>{" "}
            <strong>백테스트 종료 청산</strong>은 기간이 끝났을 때 남은 보유분을
            마지막 봉 종가에서 정리한 체결입니다. 수수료와 슬리피지는 체결가에
            반영돼 있습니다.
          </p>
        </>
      )}
    </>
  );

  return (
    <SplitPanel
      open={detailOpen}
      innerRef={splitRef}
      detailLabelledBy={`${formId}-detail-title`}
      list={listPanel}
      detail={detailPanel}
    />
  );
}
