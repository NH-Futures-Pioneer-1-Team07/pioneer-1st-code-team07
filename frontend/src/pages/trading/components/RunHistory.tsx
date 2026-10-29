import { useRef, useState } from "react";
import type { RunSummary } from "../../../apis/types";
import { formatMoney } from "../../../data/format";
import {
  formatDateTime,
  instrumentLabel,
  signed,
} from "../../../data/tradingView";
import Icon from "../../../components/common/Icon";
import RecordDetail from "../../../components/common/RecordDetail";
import { scrollToPanel } from "../../../components/common/scrollToPanel";
import styles from "./RunHistory.module.css";

const runKey = (run: RunSummary) => `${run.strategy_id}/${run.run_id}`;
const signedMoney = (value: number) => signed(value, formatMoney);
const statusLabel = (run: RunSummary) =>
  run.ended_at
    ? run.status === "error"
      ? "오류"
      : run.status === "interrupted"
        ? "중단"
        : "종료"
    : "운용 중";

export default function RunHistory({
  runs,
  error,
  liveNetPnl,
}: {
  runs: RunSummary[] | null;
  error: string | null;
  /** 운용 중인 이력은 결과가 아직 없어, 지금까지의 실현 순손익을 대신 보여 준다. */
  liveNetPnl: number | null;
}) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const splitRef = useRef<HTMLDivElement>(null);
  const list = runs ?? [];
  const selected = list.find((run) => runKey(run) === selectedKey);
  return (
    <div ref={splitRef} className={`${styles.split} ${open ? styles.splitOpen : ""}`}>
      <section
        className={`panel ${styles.history}`}
        aria-labelledby="trading-history-title"
      >
        <div className="section-head">
          <div>
            <h2 id="trading-history-title">모의매매 이력</h2>
          </div>
          <span className="badge">{list.length}</span>
        </div>
        {error && <p className="empty">이력을 불러오지 못했습니다. {error}</p>}
        {!error && runs === null && <p className="empty">불러오는 중…</p>}
        {!error && runs !== null && list.length === 0 && (
          <p className="empty">모의매매 이력이 없습니다.</p>
        )}
        {list.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <caption className="sr-only">모의매매 운용 목록</caption>
              <thead>
                <tr>
                  <th>번호</th>
                  <th>전략</th>
                  <th>종목</th>
                  <th>시작</th>
                  <th>종료</th>
                  <th>순손익</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {list.map((run, index) => {
                  const pnl = run.ended_at ? run.net_pnl : liveNetPnl;
                  const active = open && selected && runKey(selected) === runKey(run);
                  return (
                    <tr
                      key={runKey(run)}
                      className={styles.row + (active ? " " + styles.selected : "")}
                      onClick={() => {
                        setSelectedKey(runKey(run));
                        setOpen(true);
                        scrollToPanel(splitRef.current);
                      }}
                    >
                      <td className={styles.index}>{list.length - index}</td>
                      <td>
                        <button
                          type="button"
                          className={styles.rowButton}
                          aria-pressed={!!active}
                          aria-label={`${run.strategy_name} ${formatDateTime(run.started_at)} 운용 상세 보기`}
                        >
                          <strong>{run.strategy_name}</strong>
                        </button>
                      </td>
                      <td>{instrumentLabel(run.instrument.name)}</td>
                      <td>{formatDateTime(run.started_at)}</td>
                      <td>{run.ended_at ? formatDateTime(run.ended_at) : "—"}</td>
                      <td className={pnl === null ? "" : pnl >= 0 ? "positive" : "negative"}>
                        {pnl === null ? "—" : signedMoney(pnl)}
                      </td>
                      <td>
                        <span className={`badge state ${run.ended_at ? "" : "running"}`}>
                          <i />
                          {statusLabel(run)}
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
      {selected && (
        <RunDetail
          key={runKey(selected)}
          run={selected}
          open={open}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}

function RunDetail({
  run,
  open,
  onClose,
}: {
  run: RunSummary;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <section
      className={`panel ${styles.detailPanel}`}
      aria-labelledby="run-detail-title"
      aria-hidden={!open}
      inert={!open}
    >
      <div className={styles.detailInner}>
        <div className={styles.detailHeading}>
          <div>
            <h3 id="run-detail-title">
              {run.strategy_name}
              <span className={`badge state ${run.ended_at ? "" : "running"}`}>
                <i />
                {statusLabel(run)}
              </span>
            </h3>
          </div>
          <button
            type="button"
            className={styles.close}
            aria-label="운용 상세 닫기"
            onClick={onClose}
          >
            <Icon name="close" size={18} />
          </button>
        </div>
        <RecordDetail meta={run} />
      </div>
    </section>
  );
}
