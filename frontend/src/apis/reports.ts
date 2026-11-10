import { http } from "./client";
import type { ReportDetail, ReportSummary } from "./types";

export const fetchReports = () => http.get<ReportSummary[]>("/api/reports").then((r) => r.data);

export const fetchReport = (strategyId: string, name: string) =>
  http
    .get<ReportDetail>(`/api/reports/${encodeURIComponent(strategyId)}/${encodeURIComponent(name)}`)
    .then((r) => r.data);
