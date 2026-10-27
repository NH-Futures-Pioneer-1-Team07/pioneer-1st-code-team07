import { useState } from "react";
import {
  formatMoney,
  formatNumber,
  instrumentTitle,
} from "../../../data/fixtures";
import type { RunRecord } from "../../../data/trading";
import Icon from "../../../components/common/Icon";
import DecisionTimeline, {
  sideClass,
} from "../../../components/common/DecisionTimeline";
import Tabs from "../../../components/common/Tabs";
import styles from "./RunHistory.module.css";

export default function RunHistory({ runs }: { runs: RunRecord[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const selected = runs.find((run) => run.id === selectedId);
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
          <span className="badge">{runs.length}</span>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <caption className="sr-only">샘플 운용 목록</caption>
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
              {runs.map((run) => {
                const active = open && selected?.id === run.id;
                return (
                  <tr
                    key={run.id}
                    className={
                      styles.row + (active ? " " + styles.selected : "")
                    }
                    onClick={() => {
                      setSelectedId(run.id);
                      setOpen(true);
                    }}
                  >
                    <td>
                      <button
                        type="button"
                        className={styles.rowButton}
                        aria-pressed={active}
                        aria-label={`${run.strategy.name} ${run.startedAt} 운용 상세 보기`}
                      >
                        <strong>{run.strategy.name}</strong>
                      </button>
                    </td>
                    <td>{instrumentTitle(run.instrument)}</td>
                    <td>{run.startedAt}</td>
                    <td>{run.endedAt ?? "운용 중"}</td>
                    <td
                      className={
                        run.pnl - run.cost >= 0 ? "positive" : "negative"
                      }
                    >
                      {signedMoney(run.pnl - run.cost)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      {selected && (
        <RunDetail
          key={selected.id}
          run={selected}
          open={open}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}

const signedMoney = (value: number) =>
  `${value > 0 ? "+" : ""}${formatMoney(value)}`;

const detailTabs = [
  { id: "decisions", label: "매매 판단" },
  { id: "fills", label: "체결" },
] as const;

function RunDetail({
  run: selected,
  open,
  onClose,
}: {
  run: RunRecord;
  open: boolean;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<"decisions" | "fills">("decisions");
  const sideOf = (orderId: string) =>
    selected.orders.find((order) => order.id === orderId)?.side ?? "";

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
              {selected.strategy.name}
              <span className="badge">
                {selected.endedAt ? "종료" : "운용 중"}
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
        <p className={styles.summary}>
          {instrumentTitle(selected.instrument)} · 실현·평가 합계{" "}
          {signedMoney(selected.pnl)}{" "}
          <span>비용 {formatMoney(selected.cost)}</span>
        </p>
        <Tabs
          idPrefix="history"
          label="운용 상세 내역"
          value={tab}
          onChange={setTab}
          tabs={detailTabs.map((item) => ({
            ...item,
            count: selected[item.id].length,
          }))}
        />
        <div
          role="tabpanel"
          id={`history-${tab}-panel`}
          aria-labelledby={`history-${tab}-tab`}
        >
          {tab === "decisions" && (
            <DecisionTimeline rows={selected.decisions} />
          )}
          {tab === "fills" && (
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
                  {selected.fills.map((row) => (
                    <tr key={row.id}>
                      <td>{row.at}</td>
                      <td className={sideClass(sideOf(row.orderId))}>
                        {sideOf(row.orderId)}
                      </td>
                      <td>{row.quantity}계약</td>
                      <td>{formatNumber(row.price)}</td>
                      <td>
                        {row.score === null
                          ? "— (종료 청산)"
                          : `${row.score}점`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
