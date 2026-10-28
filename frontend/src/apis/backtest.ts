import { http } from "./client";
import type { Assumptions, BacktestRange, BacktestRun, RunRef } from "./types";

export const fetchRange = (strategyId: string) =>
  http
    .get<BacktestRange>("/api/backtests/range", { params: { strategy_id: strategyId } })
    .then((r) => r.data);

export const fetchAssumptions = () =>
  http.get<Assumptions>("/api/backtests/assumptions").then((r) => r.data);

export const fetchCurrentBacktest = () =>
  http.get<{ run: RunRef | null }>("/api/backtests/current").then((r) => r.data.run);

export const startBacktest = (body: {
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
}) => http.post<RunRef>("/api/backtests", body).then((r) => r.data);

export const fetchBacktestRun = (run: RunRef) =>
  http
    .get<BacktestRun>(`/api/runs/${run.strategy_id}/${run.mode}/${run.run_id}`)
    .then((r) => r.data);
