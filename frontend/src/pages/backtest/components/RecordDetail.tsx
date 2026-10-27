import { formatMoney, formatNumber } from "../../../data/fixtures";
import type { TestRecord } from "../../../data/backtest";
import DecisionTimeline from "../../../components/common/DecisionTimeline";
import styles from "./RecordDetail.module.css";

export type DetailTab = "decisions" | "fills";

export default function RecordDetail({
  record,
  tab,
}: {
  record: TestRecord;
  tab: DetailTab;
}) {
  const day = (date: string) => date.replaceAll("-", ".");
  if (tab === "decisions")
    return (
      <DecisionTimeline
        rows={[
          {
            at: `${day(record.endDate)} 15:45:00`,
            action: "매도",
            price: record.exitPrice,
            quantity: record.quantity,
            score: null,
          },
          {
            at: `${day(record.startDate)} 09:10:00`,
            action: "매수",
            price: record.entryPrice,
            quantity: record.quantity,
            score: record.score,
          },
          {
            at: `${day(record.startDate)} 09:05:00`,
            action: "진입 보류",
            price: null,
            quantity: null,
            score: Math.max(0, record.score - 18),
          },
        ]}
      />
    );
  return (
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
          <tr>
            <td>{day(record.startDate)} 09:15:00</td>
            <td className="positive">매수</td>
            <td>{record.quantity}계약</td>
            <td>{formatNumber(record.entryPrice)}</td>
            <td>{formatMoney(record.cost / 2)}</td>
            <td>{record.score}점</td>
          </tr>
          <tr>
            <td>{day(record.endDate)} 15:45:00</td>
            <td className="negative">매도</td>
            <td>{record.quantity}계약</td>
            <td>{formatNumber(record.exitPrice)}</td>
            <td>{formatMoney(record.cost / 2)}</td>
            <td>—</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
