import { useEffect, useId, useState } from "react";
import { errorMessage } from "../../../apis/client";
import { fetchJournal } from "../../../apis/trading";
import type { BacktestMeta } from "../../../apis/types";
import { formatMoney, formatNumber } from "../../../data/format";
import { mapDecisions, mapFills } from "../../../data/tradingView";
import type { DecisionRowView, FillRowView } from "../../../data/tradingView";
import DecisionTimeline, {
  sideClass,
} from "../../../components/common/DecisionTimeline";
import Tabs from "../../../components/common/Tabs";
import styles from "./RecordDetail.module.css";

const tabs = [
  { id: "decisions", label: "매매 판단" },
  { id: "fills", label: "체결" },
] as const;

/** 한 번에 그리는 줄 수. 백테스트는 봉마다 판단이 남아 수천 건이 될 수 있다. */
const ROW_LIMIT = 300;

interface Detail {
  decisions: DecisionRowView[];
  fills: FillRowView[];
  error: string | null;
}

export default function RecordDetail({ meta }: { meta: BacktestMeta }) {
  const [tab, setTab] = useState<"decisions" | "fills">("decisions");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const prefix = useId();

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setFailure(null);
    setTab("decisions");
    (async () => {
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
      } catch (error) {
        if (!cancelled) setFailure(errorMessage(error));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [meta.strategy_id, meta.mode, meta.run_id, meta.status]);

  const rows = detail ? detail[tab] : [];
  return (
    <>
      <Tabs
        idPrefix={prefix}
        label="백테스트 상세 내역"
        value={tab}
        onChange={setTab}
        tabs={tabs.map((item) => ({
          ...item,
          count: detail ? detail[item.id].length : 0,
        }))}
      />
      <div
        role="tabpanel"
        id={`${prefix}-${tab}-panel`}
        aria-labelledby={`${prefix}-${tab}-tab`}
        tabIndex={0}
      >
        {detail?.error && <p className="empty">{detail.error}</p>}
        {failure && <p className="empty">기록을 불러오지 못했습니다. {failure}</p>}
        {!failure && !detail && <p className="empty">불러오는 중…</p>}
        {detail && tab === "decisions" && (
          <DecisionTimeline rows={detail.decisions.slice(0, ROW_LIMIT)} />
        )}
        {detail && tab === "fills" && (
          <div className="table-wrap">
            <table className={`data-table ${styles.recordTable}`}>
              <caption className="sr-only">백테스트 체결</caption>
              <thead>
                <tr>
                  <th>체결 시각</th>
                  <th>매매구분</th>
                  <th>체결 수량</th>
                  <th>체결 가격</th>
                  <th>수수료</th>
                  <th>주문 당시 점수</th>
                </tr>
              </thead>
              <tbody>
                {detail.fills.slice(0, ROW_LIMIT).map((row) => (
                  <tr key={row.key}>
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
        {rows.length > ROW_LIMIT && (
          <p className="empty">
            앞의 {ROW_LIMIT}건만 보여 줍니다. 전체 {rows.length}건은 실행 기록 파일에 있습니다.
          </p>
        )}
      </div>
    </>
  );
}
