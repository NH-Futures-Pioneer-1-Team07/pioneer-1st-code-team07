import { useEffect, useId, useState } from "react";
import { errorMessage } from "../../apis/client";
import { fetchJournal } from "../../apis/trading";
import type { RunRef } from "../../apis/types";
import { formatMoney, formatNumber } from "../../data/format";
import { mapDecisions, mapFills } from "../../data/tradingView";
import type { DecisionRowView, FillRowView } from "../../data/tradingView";
import DecisionTimeline, {
  sideClass,
} from "./DecisionTimeline";
import Tabs from "./Tabs";
import { useIncrementalRows } from "./useIncrementalRows";
import styles from "./RecordDetail.module.css";

const tabs = [
  { id: "decisions", label: "매매 판단" },
  { id: "fills", label: "체결" },
] as const;

interface Detail {
  decisions: DecisionRowView[];
  fills: FillRowView[];
  error: string | null;
}

export type RecordMeta = RunRef & { status: string; ended_at: string | null };

export default function RecordDetail({ meta }: { meta: RecordMeta }) {
  const [tab, setTab] = useState<"decisions" | "fills">("decisions");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const prefix = useId();

  useEffect(() => {
    setDetail(null);
    setFailure(null);
    setTab("decisions");
  }, [meta.strategy_id, meta.mode, meta.run_id]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [decisions, fills, events] = await Promise.all([
          fetchJournal(meta, "decision"),
          fetchJournal(meta, "fill"),
          meta.status === "error" ? fetchJournal(meta, "event") : Promise.resolve([]),
        ]);
        if (cancelled) return;
        const failed = events.filter((line) => line.level === "error").pop();
        setDetail({
          decisions: mapDecisions(decisions),
          fills: mapFills(fills),
          error: typeof failed?.text === "string" ? failed.text : null,
        });
        setFailure(null);
      } catch (error) {
        if (!cancelled) setFailure(errorMessage(error));
      }
    };
    void load();
    // 운용 중인 이력은 기록이 계속 늘어나므로 다시 불러온다.
    const timer = meta.ended_at ? undefined : window.setInterval(load, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [meta.strategy_id, meta.mode, meta.run_id, meta.status, meta.ended_at]);

  // 가장 최근 기록이 맨 위에 오도록 뒤집고, 번호는 오래된 기록부터 1번으로 매긴다.
  const decisions = detail ? [...detail.decisions].reverse() : [];
  const fills = detail ? [...detail.fills].reverse() : [];
  const rows = tab === "decisions" ? decisions : fills;
  // 백테스트는 봉마다 판단이 남아 수천 건이 될 수 있어, 스크롤하면서 나눠 그린다.
  const visible = useIncrementalRows(rows.length, `${meta.run_id}-${tab}`);
  return (
    <>
      <Tabs
        idPrefix={prefix}
        label="상세 내역"
        value={tab}
        onChange={setTab}
        tabs={tabs.map((item) => ({
          ...item,
          count: detail ? detail[item.id].length : 0,
        }))}
      />
      <div
        className={styles.panel}
        role="tabpanel"
        id={`${prefix}-${tab}-panel`}
        aria-labelledby={`${prefix}-${tab}-tab`}
        tabIndex={0}
      >
        {detail?.error && <p className="empty">{detail.error}</p>}
        {failure && <p className="empty">기록을 불러오지 못했습니다. {failure}</p>}
        {!failure && !detail && <p className="empty">불러오는 중…</p>}
        {detail && tab === "decisions" && (
          <DecisionTimeline
            rows={decisions.slice(0, visible.count)}
            total={decisions.length}
            onScroll={visible.onScroll}
          />
        )}
        {detail && tab === "fills" && (
          <div className={`table-wrap ${styles.fills}`} onScroll={visible.onScroll}>
            <table className={`data-table ${styles.recordTable}`}>
              <caption className="sr-only">체결</caption>
              <thead>
                <tr>
                  <th className={styles.index}>번호</th>
                  <th>체결 시각</th>
                  <th>매매구분</th>
                  <th>체결 수량</th>
                  <th>체결 가격</th>
                  <th>수수료</th>
                  <th>주문 당시 점수</th>
                </tr>
              </thead>
              <tbody>
                {fills.slice(0, visible.count).map((row, index) => (
                  <tr key={row.key}>
                    <td className={styles.index}>{fills.length - index}</td>
                    <td>{row.at}</td>
                    <td className={sideClass(row.side)}>{row.side}</td>
                    <td>{row.quantity}계약</td>
                    <td>{formatNumber(row.price)}</td>
                    <td>{row.fee === null ? "—" : formatMoney(row.fee)}</td>
                    <td>{row.score === null ? "—" : `${row.score}점`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {detail && rows.length === 0 && <p className="empty">기록이 없습니다.</p>}
      </div>
    </>
  );
}
