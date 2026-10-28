import { useEffect, useState } from "react";
import { errorMessage } from "../../../apis/client";
import { fetchJournal } from "../../../apis/trading";
import type { RunSummary } from "../../../apis/types";
import { formatMoney, formatNumber } from "../../../data/format";
import {
  formatDateTime,
  instrumentLabel,
  mapDecisions,
  mapFills,
  signed,
} from "../../../data/tradingView";
import type { DecisionRowView, FillRowView } from "../../../data/tradingView";
import Icon from "../../../components/common/Icon";
import DecisionTimeline, {
  sideClass,
} from "../../../components/common/DecisionTimeline";
import Tabs from "../../../components/common/Tabs";
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
}: {
  runs: RunSummary[] | null;
  error: string | null;
}) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const list = runs ?? [];
  const selected = list.find((run) => runKey(run) === selectedKey);
  return (
    <div className={`${styles.split} ${open ? styles.splitOpen : ""}`}>
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
                  <th>전략</th>
                  <th>종목</th>
                  <th>시작</th>
                  <th>종료</th>
                  <th>순손익</th>
                </tr>
              </thead>
              <tbody>
                {list.map((run) => {
                  const active = open && selected && runKey(selected) === runKey(run);
                  return (
                    <tr
                      key={runKey(run)}
                      className={styles.row + (active ? " " + styles.selected : "")}
                      onClick={() => {
                        setSelectedKey(runKey(run));
                        setOpen(true);
                      }}
                    >
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
                      <td>{run.ended_at ? formatDateTime(run.ended_at) : "운용 중"}</td>
                      <td
                        className={
                          run.net_pnl === null
                            ? ""
                            : run.net_pnl >= 0
                              ? "positive"
                              : "negative"
                        }
                      >
                        {run.net_pnl === null ? "—" : signedMoney(run.net_pnl)}
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

const detailTabs = [
  { id: "decisions", label: "매매 판단" },
  { id: "fills", label: "체결" },
] as const;

interface Detail {
  decisions: DecisionRowView[];
  fills: FillRowView[];
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
  const [tab, setTab] = useState<"decisions" | "fills">("decisions");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [decisions, fills] = await Promise.all([
          fetchJournal(run, "decision"),
          fetchJournal(run, "fill"),
        ]);
        if (cancelled) return;
        setDetail({ decisions: mapDecisions(decisions), fills: mapFills(fills) });
        setFailure(null);
      } catch (error) {
        if (!cancelled) setFailure(errorMessage(error));
      }
    };
    void load();
    // 운용 중인 이력은 기록이 계속 늘어나므로 다시 불러온다.
    const timer = run.ended_at ? undefined : window.setInterval(load, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [run]);

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
              <span className="badge">{statusLabel(run)}</span>
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
        <p className={styles.summary}>
          {instrumentLabel(run.instrument.name)} · 순손익{" "}
          {run.net_pnl === null ? "—" : signedMoney(run.net_pnl)}{" "}
          <span>수수료는 추정값입니다</span>
        </p>
        <Tabs
          idPrefix="history"
          label="운용 상세 내역"
          value={tab}
          onChange={setTab}
          tabs={detailTabs.map((item) => ({
            ...item,
            count: detail ? detail[item.id].length : 0,
          }))}
        />
        <div
          role="tabpanel"
          id={`history-${tab}-panel`}
          aria-labelledby={`history-${tab}-tab`}
        >
          {failure && <p className="empty">기록을 불러오지 못했습니다. {failure}</p>}
          {!failure && detail === null && <p className="empty">불러오는 중…</p>}
          {detail && tab === "decisions" && (
            <DecisionTimeline rows={detail.decisions} />
          )}
          {detail && tab === "fills" && (
            <div className="table-wrap">
              <table className="data-table">
                <caption className="sr-only">선택 운용의 체결</caption>
                <thead>
                  <tr>
                    <th>체결 시각</th>
                    <th>매매구분</th>
                    <th>체결 수량</th>
                    <th>체결 가격</th>
                    <th>주문 당시 점수</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.fills.map((row) => (
                    <tr key={row.key}>
                      <td>{row.at}</td>
                      <td className={sideClass(row.side)}>{row.side}</td>
                      <td>{row.quantity}계약</td>
                      <td>{formatNumber(row.price)}</td>
                      <td>{row.score === null ? "—" : `${row.score}점`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {detail.fills.length === 0 && <p className="empty">체결이 없습니다.</p>}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
