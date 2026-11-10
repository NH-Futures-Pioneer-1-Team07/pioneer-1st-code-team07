import { useMemo } from "react";
import { usePolling } from "../../../apis/polling";
import { fetchSweepResults } from "../../../apis/reports";
import type { ReportDetail } from "../../../apis/types";
import { numericParams } from "../../../data/reportCharts";
import EquityLineChart from "./EquityLineChart";
import PeriodBarChart from "./PeriodBarChart";
import SensitivityChart from "./SensitivityChart";
import styles from "./ReportCharts.module.css";

export default function ReportCharts({ report }: { report: ReportDetail }) {
  const { meta, table } = report;
  const ids = useMemo(() => [...new Set(meta.recommended.flatMap((item) => Object.values(item.ids)))], [meta.recommended]);
  const results = usePolling(() => fetchSweepResults(meta.strategy_id, ids), 60000, [meta.strategy_id, ids.join(",")], ids.length > 0);
  const hasSensitivity = table !== null && numericParams(table).length > 0;

  return (
    <>
      {table !== null && (
        <section className={styles.block} aria-labelledby="chart-sensitivity-title">
          <header>
            <h3 id="chart-sensitivity-title">파라미터별 성과</h3>
            <p>바꾼 파라미터 값에 따라 기간별 성과가 어떻게 달라지는지 봅니다. 선이 기간마다 같은 방향이면 일관성이 높습니다.</p>
          </header>
          {hasSensitivity ? <SensitivityChart table={table} periods={meta.periods} /> : <p className={styles.note}>바꾼 숫자 파라미터가 없어 그래프를 그릴 수 없습니다.</p>}
        </section>
      )}
      {ids.length > 0 && (
        <>
          <section className={styles.block} aria-labelledby="chart-periods-title">
            <header>
              <h3 id="chart-periods-title">기간별 순손익</h3>
              <p>추천·대안 조합이 전체 기간과 구간마다 얼마를 벌거나 잃었는지 비교합니다.</p>
            </header>
            {results.data === null ? (
              <p className={styles.note}>{results.error ? `결과를 불러오지 못했습니다. ${results.error}` : "불러오는 중…"}</p>
            ) : (
              <PeriodBarChart meta={meta} results={results.data} />
            )}
          </section>
          <section className={styles.block} aria-labelledby="chart-equity-title">
            <header>
              <h3 id="chart-equity-title">수익률 곡선</h3>
              <p>초기자금 대비 일별 자산의 변화입니다. 기간을 바꿔 가며 곡선이 어떻게 달라지는지 봅니다.</p>
            </header>
            {results.data === null ? (
              <p className={styles.note}>{results.error ? "" : "불러오는 중…"}</p>
            ) : (
              <EquityLineChart meta={meta} results={results.data} />
            )}
          </section>
        </>
      )}
    </>
  );
}
