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

/** 시세를 조회할 종목의 시장. 해외 종목은 거래소 코드도 보낸다. */
export interface MarketTarget {
  market: "domestic" | "overseas";
  exchange?: string | null;
}

const marketParams = (target?: MarketTarget) =>
  target ? { market: target.market, ...(target.exchange ? { exchange: target.exchange } : {}) } : {};

export const fetchQuote = (code: string, target?: MarketTarget) =>
  http.get<Quote>(`/api/market/${code}/quote`, { params: marketParams(target) }).then((r) => r.data);

export const fetchCandles = (code: string, interval: string, count = 120, target?: MarketTarget) =>
  http
    .get<Candle[]>(`/api/market/${code}/candles`, { params: { interval, count, ...marketParams(target) } })
    .then((r) => r.data);

export const fetchOrderBook = (code: string, target?: MarketTarget) =>
  http
    .get<OrderBook>(`/api/market/${code}/orderbook`, { params: marketParams(target) })
    .then((r) => r.data);

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
