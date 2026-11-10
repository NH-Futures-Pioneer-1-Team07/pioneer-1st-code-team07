import { useMemo, useState } from "react";
import { usePolling } from "../../apis/polling";
import { latestWeek } from "../../data/defaultStrategy";
import { fetchReport, fetchReports } from "../../apis/reports";
import type { ReportSummary } from "../../apis/types";

const POLL_MS = 15000;

export const reportKey = (report: Pick<ReportSummary, "strategy_id" | "name">) => `${report.strategy_id}/${report.name}`;

/** 목록과 선택한 보고서의 상세. 파일이 바뀌면 다음 조회에서 화면이 갱신된다. */
export function useReportsPage(active: boolean) {
  const list = usePolling(fetchReports, POLL_MS, [], active);
  const [chosenKey, setChosenKey] = useState<string | null>(null);

  const items = list.data ?? [];
  // 고른 보고서가 목록에 없으면 가장 최근 주차 전략의 읽을 수 있는 첫 보고서를 보여 준다.
  const selected = useMemo(() => {
    const readable = items.filter((item) => item.error === null);
    const latest = latestWeek(readable, (item) => item.strategy_id);
    return (
      items.find((item) => reportKey(item) === chosenKey) ??
      readable.find((item) => item.strategy_id === latest?.strategy_id)
    );
  }, [items, chosenKey]);
  const detail = usePolling(
    () => fetchReport(selected!.strategy_id, selected!.name),
    POLL_MS,
    [selected ? reportKey(selected) : null],
    active && selected !== undefined && selected.error === null,
  );

  return {
    list,
    items,
    selected,
    detail,
    select: (report: ReportSummary) => setChosenKey(reportKey(report)),
  };
}

export type ReportsController = ReturnType<typeof useReportsPage>;
