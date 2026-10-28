import { http } from "./client";
import type {
  AccountView,
  Candle,
  JournalLine,
  JournalPage,
  OrderBook,
  Quote,
  RunRef,
  RunSummary,
  StrategyDetail,
  StrategySummary,
  TradingStatus,
} from "./types";

export const fetchStrategies = () =>
  http.get<StrategySummary[]>("/api/strategies").then((r) => r.data);

export const fetchStrategy = (id: string) =>
  http.get<StrategyDetail>(`/api/strategies/${id}`).then((r) => r.data);

export const fetchStatus = () =>
  http.get<TradingStatus>("/api/trading/status").then((r) => r.data);

export const fetchAccount = () =>
  http.get<AccountView>("/api/trading/account").then((r) => r.data);

export const startTrading = (strategyId: string) =>
  http.post<RunRef>("/api/trading/start", { strategy_id: strategyId }).then((r) => r.data);

export const stopTrading = () =>
  http.post<{ phase: string }>("/api/trading/stop").then((r) => r.data);

export const clearAccount = () =>
  http.post<{ phase: string }>("/api/trading/clear").then((r) => r.data);

export const fetchQuote = (code: string) =>
  http.get<Quote>(`/api/market/${code}/quote`).then((r) => r.data);

export const fetchCandles = (code: string, interval: string, count = 120) =>
  http
    .get<Candle[]>(`/api/market/${code}/candles`, { params: { interval, count } })
    .then((r) => r.data);

export const fetchOrderBook = (code: string) =>
  http.get<OrderBook>(`/api/market/${code}/orderbook`).then((r) => r.data);

export const fetchRuns = (mode: "paper" | "backtest") =>
  http.get<RunSummary[]>("/api/runs", { params: { mode } }).then((r) => r.data);

export async function fetchJournal(run: RunRef, kind: string): Promise<JournalLine[]> {
  const url = `/api/runs/${run.strategy_id}/${run.mode}/${run.run_id}/journal`;
  const lines: JournalLine[] = [];
  for (let offset = 0; ; offset += 1000) {
    const page = (await http.get<JournalPage>(url, { params: { kind, offset, limit: 1000 } })).data;
    lines.push(...page.items);
    if (lines.length >= page.total || page.items.length === 0) return lines;
  }
}
