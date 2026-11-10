import { http } from "./client";
import type { ReportDetail, ReportSummary, SweepResult, SweepTrades } from "./types";

export const fetchReports = () => http.get<ReportSummary[]>("/api/reports").then((r) => r.data);

export const fetchReport = (strategyId: string, name: string) =>
  http
    .get<ReportDetail>(`/api/reports/${encodeURIComponent(strategyId)}/${encodeURIComponent(name)}`)
    .then((r) => r.data);

export const fetchSweepResults = (strategyId: string, ids: string[]) =>
  http
    .get<SweepResult[]>(`/api/sweeps/${encodeURIComponent(strategyId)}/results`, { params: { ids: ids.join(",") } })
    .then((r) => r.data);

export const fetchSweepTrades = (strategyId: string, id: string) =>
  http
    .get<SweepTrades>(`/api/sweeps/${encodeURIComponent(strategyId)}/trades/${encodeURIComponent(id)}`)
    .then((r) => r.data);
