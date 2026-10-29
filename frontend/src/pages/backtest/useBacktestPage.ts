import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  fetchAssumptions,
  fetchBacktestRun,
  fetchCurrentBacktest,
  fetchRange,
  startBacktest,
} from "../../apis/backtest";
import { errorMessage } from "../../apis/client";
import { usePolling } from "../../apis/polling";
import { fetchRuns, fetchStrategies } from "../../apis/trading";
import type { RunRef, RunSummary } from "../../apis/types";
import { defaultPeriod, progressPercent, validateInput } from "../../data/backtestView";
import { runKey } from "../../data/tradingView";

/** 백테스트 화면의 입력값, 서버 조회, 실행 상태를 모은 훅. 화면 영역 컴포넌트가 이 값을 나눠 쓴다. */
export function useBacktestPage() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [capital, setCapital] = useState("50000000");
  const [slippage, setSlippage] = useState("");
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const [active, setActive] = useState<RunRef | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const splitRef = useRef<HTMLDivElement>(null);
  const [announcement, setAnnouncement] = useState("");
  const formId = useId();

  const strategies = usePolling(fetchStrategies, 60000);
  const items = strategies.data ?? [];
  const strategy = items.find((item) => item.id === selectedStrategy) ?? items[0];
  const strategyId = strategy?.id ?? null;

  const range = usePolling(() => fetchRange(strategyId as string), 600000, [strategyId], !!strategyId);
  const assumptions = usePolling(fetchAssumptions, 600000);
  const runs = usePolling(() => fetchRuns("backtest"), 10000);
  const list = runs.data ?? [];

  // 화면을 다시 열었을 때 실행 중인 백테스트를 이어서 본다.
  useEffect(() => {
    fetchCurrentBacktest()
      .then((run) => run && setActive(run))
      .catch(() => undefined);
  }, []);

  const live = usePolling(
    () => fetchBacktestRun(active as RunRef),
    1000,
    [active ? runKey(active) : null],
    !!active,
  );
  const liveMeta = live.data?.meta;
  useEffect(() => {
    if (!active || !liveMeta || liveMeta.status === "running") return;
    setSelectedKey(runKey(active));
    setActive(null);
    runs.reload();
    setAnnouncement(
      liveMeta.status === "completed"
        ? "백테스트가 완료됐습니다. 결과와 실행 이력을 확인하세요."
        : "백테스트가 오류로 끝났습니다.",
    );
  }, [liveMeta?.status]);

  const selected: RunSummary | undefined =
    list.find((run) => runKey(run) === selectedKey) ??
    list.find((run) => run.status !== "running");
  const report = usePolling(
    () => fetchBacktestRun(selected as RunRef),
    600000,
    [selected ? `${runKey(selected)}/${selected.status}` : null],
    !!selected,
  );
  const reportMeta = report.data?.meta;
  const result = report.data?.result ?? null;

  const busy = starting || !!active;
  const available = range.data?.start && range.data.end ? range.data : null;
  useEffect(() => {
    const period = defaultPeriod(available);
    if (period && !startDate && !endDate) {
      setStartDate(period.start);
      setEndDate(period.end);
    }
  }, [available, startDate, endDate]);

  // 슬리피지 입력칸은 서버의 가정 값으로 처음 채운다.
  useEffect(() => {
    const ticks = assumptions.data?.slippage.ticks;
    if (ticks !== undefined) setSlippage((current) => (current === "" ? String(ticks) : current));
  }, [assumptions.data?.slippage.ticks]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = validateInput(startDate, endDate, capital, available, slippage);
    if (problem || !strategyId) {
      setError(problem || "전략을 선택해 주세요.");
      return;
    }
    setError("");
    setStarting(true);
    try {
      const run = await startBacktest({
        strategy_id: strategyId,
        start_date: startDate,
        end_date: endDate,
        initial_capital: Number(capital),
        slippage_ticks: Number(slippage),
      });
      setActive(run);
      setAnnouncement("백테스트를 시작했습니다. 과거 데이터를 준비합니다.");
      runs.reload();
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setStarting(false);
    }
  }

  const percent = progressPercent(liveMeta?.progress, liveMeta?.status ?? "running");

  return {
    selectedStrategy, setSelectedStrategy, startDate, setStartDate, endDate, setEndDate, capital, setCapital, slippage, setSlippage, error, setError, starting, active, selectedKey, setSelectedKey, detailOpen, setDetailOpen, splitRef, announcement, formId, strategies, items, strategy, strategyId, range, assumptions, runs, list, live, liveMeta, selected, report, reportMeta, result, busy, available, submit, percent,
  };
}

export type BacktestController = ReturnType<typeof useBacktestPage>;
