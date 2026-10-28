export interface StrategySummary {
  id: string;
  name: string;
  description: string;
}

export interface StrategyInstrument {
  name: string;
  code: string | null;
  multiplier: number | null;
}

export interface StrategyDetail extends StrategySummary {
  instruments: StrategyInstrument[];
  bar: { unit: string; size: number };
}

export interface Quote {
  code: string;
  name: string;
  contract: string | null;
  expiry: string | null;
  price: number | null;
  change: number | null;
  change_rate: number | null;
  volume: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  prev_close: number | null;
  upper_limit: number | null;
  lower_limit: number | null;
  multiplier: number | null;
  remaining_days: number | null;
}

export interface Candle {
  time: string;
  open: number | null;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BookLevel {
  ask_price: number | null;
  ask_quantity: number | null;
  bid_price: number | null;
  bid_quantity: number | null;
}

export interface OrderBook {
  code: string;
  time: string;
  price?: number | null;
  change_rate?: number | null;
  total_ask_quantity: number | null;
  total_bid_quantity: number | null;
  levels: BookLevel[];
}

export type Phase = "idle" | "running" | "stopping" | "clearing";

export interface RunPnl {
  realized_pnl: number;
  unrealized_pnl: number;
  fee: number;
  fee_estimated: boolean;
  total_pnl: number;
  trade_count: number;
}

export interface ClearState {
  state: "running" | "done";
  step: string;
  detail: string;
  result: {
    status: "completed" | "incomplete";
    open_orders: AccountOrder[];
    positions: AccountPosition[];
    cancelled: number;
    problems: string[];
  } | null;
}

export interface RunRef {
  strategy_id: string;
  mode: string;
  run_id: string;
}

export interface TradingStatus {
  phase: Phase;
  run: RunRef | null;
  strategy?: string;
  instrument?: string;
  feed?: string;
  last_price?: number | null;
  last_price_at?: string | null;
  last_bar_time?: string | null;
  entry_blocks?: string[];
  pnl?: RunPnl;
  clear?: ClearState;
  last_run?: (RunRef & { status: string }) | null;
}

export interface AccountPosition {
  code: string;
  name: string;
  side: "buy" | "sell" | null;
  quantity: number | null;
  closable_quantity: number | null;
  avg_price: number | null;
  last_price: number | null;
  pnl: number | null;
  pnl_rate: number | null;
}

export interface AccountOrder {
  order_no: string;
  code: string;
  side: "buy" | "sell" | null;
  status: string;
  quantity: number | null;
  filled_quantity: number | null;
  remaining_quantity: number | null;
  price: number | null;
  received_time: string;
}

export interface AccountView {
  deposit: {
    cash: number | null;
    total_assets: number | null;
    order_available_total: number | null;
    order_available_cash: number | null;
    initial_margin: number | null;
    maintenance_margin: number | null;
    futures_realized_pnl: number | null;
  };
  positions: AccountPosition[];
  open_orders: AccountOrder[];
}

export interface RunSummary extends RunRef {
  strategy_name: string;
  instrument: { name: string; code: string };
  started_at: string;
  ended_at: string | null;
  status: string;
  period?: { start: string; end: string };
  initial_capital?: number;
  net_pnl: number | null;
}

export interface JournalLine {
  seq: number;
  time: string;
  kind: string;
  [field: string]: unknown;
}

export interface JournalPage {
  items: JournalLine[];
  total: number;
  offset: number;
  limit: number;
}

export type MarketMessage =
  | { type: "state"; state: string; detail: string }
  | {
      type: "trade";
      code: string;
      time: string;
      price: number | null;
      quantity: number | null;
      cum_volume: number | null;
      is_trade: boolean;
    }
  | ({ type: "orderbook" } & OrderBook)
  | { type: "reconnected" }
  | { type: "subscription_failed"; code: string | null; reason_code: string; message: string };

export interface BacktestRange {
  strategy_id: string;
  instrument: { name: string; code: string };
  start: string | null;
  end: string | null;
  last_trading_day: string | null;
  /** 기간 안에서 봉이 적은 날 → 그날의 봉 수 */
  sparse_days?: Record<string, number>;
}

export interface Assumptions {
  fee: { rate: number; basis: string; source: string };
  slippage: { ticks: number; tick_size: number | null; direction: string };
  fill: { on_bar: string; on_price: string; intrabar_path: string };
  margin: string;
}

export interface BacktestProgress {
  stage: "prepare" | "compute" | "done";
  done: number;
  total: number;
}

export interface BacktestMeta extends RunRef {
  strategy_name: string;
  instrument: { name: string; code: string };
  started_at: string;
  ended_at: string | null;
  status: string;
  period: { start: string; end: string };
  initial_capital: number;
  assumptions: Assumptions;
  progress?: BacktestProgress;
}

export interface DailyBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestResult {
  initial_capital: number;
  final_equity: number;
  gross_pnl: number;
  fee: number;
  net_pnl: number;
  return_rate: number;
  trade_count: number;
  win_count: number;
  loss_count: number;
  max_drawdown: number;
  max_drawdown_rate: number;
  days: number;
  bars: number;
  equity_curve: { time: string; equity: number }[];
  /** 기간의 일봉. 이 항목이 생기기 전에 실행한 기록에는 없다. */
  daily_bars?: DailyBar[];
}

export interface BacktestRun {
  meta: BacktestMeta;
  result: BacktestResult | null;
}
