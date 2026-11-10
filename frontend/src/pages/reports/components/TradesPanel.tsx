import { useMemo, useState } from "react";
import { fetchSweepTrades } from "../../../apis/reports";
import { usePolling } from "../../../apis/polling";
import type { ReportMeta } from "../../../apis/types";
import { useIncrementalRows } from "../../../components/common/useIncrementalRows";
import { pnlClass } from "../../../data/format";
import { reasonSummary } from "../../../data/reportCharts";
import { moneyText, shortTime } from "../../../data/reportView";
import styles from "./TradesPanel.module.css";

const sideText = (side: string) => (side === "buy" ? "매수" : "매도");

export default function TradesPanel({ meta }: { meta: ReportMeta }) {
  const [combo, setCombo] = useState(0);
  const [period, setPeriod] = useState(meta.periods[0]?.label ?? "");
  const item = meta.recommended[combo] ?? meta.recommended[0];
  const id = item?.ids[period];
  const trades = usePolling(() => fetchSweepTrades(meta.strategy_id, id!), 60000, [meta.strategy_id, id ?? null], id !== undefined);
  const data = id === undefined ? null : trades.data;
  const summary = useMemo(() => (data ? reasonSummary(data.trades) : []), [data]);
  const rows = data?.trades ?? [];
  const { count, onScroll } = useIncrementalRows(rows.length, id ?? "", 50);

  if (!item) return <p className={styles.note}>추천·대안 조합이 없어 거래를 보여 줄 수 없습니다.</p>;
  return (
    <div className={styles.panel}>
      <div className={styles.controls}>
        <div className={styles.toggle} role="group" aria-label="조합">
          {meta.recommended.map((option, index) => (
            <button key={option.label} type="button" className={index === combo ? styles.on : ""} aria-pressed={index === combo} onClick={() => setCombo(index)}>
              {option.label}
            </button>
          ))}
        </div>
        <div className={styles.toggle} role="group" aria-label="기간">
          {meta.periods.map((option) => (
            <button key={option.label} type="button" className={option.label === period ? styles.on : ""} aria-pressed={option.label === period} onClick={() => setPeriod(option.label)}>
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {id === undefined && <p className={styles.note}>이 조합은 이 기간의 결과가 보고서에 없습니다.</p>}
      {id !== undefined && trades.error && data === null && <p className={styles.error}>거래를 불러오지 못했습니다. {trades.error}</p>}
      {id !== undefined && !trades.error && data === null && <p className={styles.note}>불러오는 중…</p>}
      {data && (
        <>
          <h4>청산 이유별</h4>
          <div className="table-wrap" style={{ "--table-height": "auto" } as React.CSSProperties}>
            <table className={`data-table ${styles.table} ${styles.summaryTable}`}>
              <thead>
                <tr>
                  <th>청산 이유</th>
                  <th>거래 수</th>
                  <th>순손익</th>
                  <th>평균</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((row) => (
                  <tr key={row.reason}>
                    <td className={styles.reason}>{row.reason}</td>
                    <td>{row.count}</td>
                    <td className={pnlClass(row.netPnl)}>{moneyText(row.netPnl)}</td>
                    <td className={pnlClass(row.average)}>{moneyText(row.average)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h4>
            거래 목록 <small>{rows.length}건 · 체결 {data.fills.length}건</small>
          </h4>
          <div className={`table-wrap ${styles.scroll}`} onScroll={onScroll}>
            <table className={`data-table ${styles.table}`}>
              <thead>
                <tr>
                  <th>진입</th>
                  <th>청산</th>
                  <th>방향</th>
                  <th>수량</th>
                  <th>진입가</th>
                  <th>청산가</th>
                  <th>순손익</th>
                  <th>청산 이유</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, count).map((trade, index) => (
                  <tr key={`${trade.entry_id}-${index}`}>
                    <td>{shortTime(trade.opened_at)}</td>
                    <td>{shortTime(trade.closed_at)}</td>
                    <td>{sideText(trade.side)}</td>
                    <td>{trade.quantity}</td>
                    <td>{trade.entry_price}</td>
                    <td>{trade.exit_price}</td>
                    <td className={pnlClass(trade.net_pnl)}>{moneyText(trade.net_pnl)}</td>
                    <td className={styles.reasonCell} title={trade.exit_reason ?? undefined}>
                      {trade.exit_reason ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {count < rows.length && <p className={styles.note}>스크롤하면 거래를 더 불러옵니다 ({count}/{rows.length}건 표시).</p>}
        </>
      )}
    </div>
  );
}
