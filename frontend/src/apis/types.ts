export interface StrategySummary {
  id: string;
  name: string;
  description: string;
}

export interface StrategyInstrument {
  name: string;
  market: "domestic" | "overseas";
  code: string | null;
  exchange: string | null;
  multiplier: number | null;
  margin: number | null;
  /** 스프레드 종목이면 구성 종목과 계약 비율과 가격 가중치(음수인 종목은 스프레드 가격에서 뺀다). 가중치가 없으면 계약 비율이다 */
  legs?: { code: string; ratio: number; weight?: number | null }[] | null;
}

/** 전략 파라미터 명세. `editable`이면 시작 전에 화면에서 바꿀 수 있고 `percent`는 0.2를 20%로 보여 준다. */
export interface ParameterSpec {
  default: unknown;
  description: string;
  editable: boolean;
  label: string | null;
  unit: "percent" | null;
  min: number | null;
  max: number | null;
}

/** 모의매매 차트에 그릴 전략의 판단용 선. `bar`는 판단 기준 봉 차트, `daily`는 일봉 차트에 그린다. */
export interface ChartLineSpec {
  series: "bar" | "daily";
  kind: "sma" | "previous_close" | "level";
  period: number | null;
  label: string;
  description: string;
}

export interface StrategyDetail extends StrategySummary {
  instruments: StrategyInstrument[];
  bar: { unit: string; size: number };
  parameters: Record<string, ParameterSpec>;
  chart_lines: ChartLineSpec[];
}

export type MarketSession = "before_open" | "auction" | "regular" | "closed" | "holiday" | "unknown";

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
  market_session: MarketSession;
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

/** 전략이 설명하는 현재 판단. 구역마다 제목·한 줄 결론·색·표로 이루어진다. */
export interface JudgmentSection {
  title: string;
  headline: string;
  tone: "buy" | "sell" | "neutral";
  rows: [string, string][];
}

/** 전략이 차트에 수평선으로 그리라고 내려주는 경계(스프레드 밴드 등) */
export interface JudgmentLevel {
  label: string;
  value: number;
  description: string;
}

export interface Judgment {
  sections: JudgmentSection[];
  levels?: JudgmentLevel[];
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
  judgment?: Judgment | null;
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
  /** 실행 때 쓴 전략 파라미터 */
  params?: Record<string, unknown> | null;
  instrument: { name: string; code: string; market?: "domestic" | "overseas" };
  started_at: string;
  ended_at: string | null;
  status: string;
  period?: { start: string; end: string };
  initial_capital?: number;
  assumptions?: Assumptions;
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
  instrument: { name: string; code: string; market?: "domestic" | "overseas" };
  started_at: string;
  ended_at: string | null;
  status: string;
  period: { start: string; end: string };
  initial_capital: number;
  assumptions: Assumptions;
  /** 전략마다 키가 다른 실행 파라미터 */
  params?: Record<string, unknown>;
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

/** 검증 보고서 목록 항목. 머리말이 깨졌으면 `error`만 채워진다. */
export interface ReportSummary {
  strategy_id: string;
  name: string;
  title?: string;
  question?: string;
  updated?: string;
  author?: string;
  result_count?: number;
  recommended?: (string | null)[];
  error: string | null;
}

export interface ReportPeriod {
  label: string;
  start: string;
  end: string;
  kind: "full" | "split";
}

export interface ReportRecommendation {
  label: string;
  role: "recommended" | "alternative";
  params: Record<string, unknown>;
  ids: Record<string, string>;
}

export interface ReportMeta {
  strategy_id: string;
  name: string;
  title: string;
  question: string;
  updated: string;
  author: string;
  result_count: number;
  periods: ReportPeriod[];
  recommended: ReportRecommendation[];
}

export type TableCell = number | string | null;

export interface ReportTable {
  columns: string[];
  rows: TableCell[][];
}

export interface ReportDetail {
  strategy_id: string;
  name: string;
  meta: ReportMeta;
  body: string;
  table: ReportTable | null;
}

/** 조합 탐색 결과 한 줄(조합 하나 × 기간 하나). */
export interface SweepResult {
  id: string;
  strategy_id: string;
  params: Record<string, unknown>;
  start: string;
  end: string;
  slippage_ticks: number;
  initial_capital: number;
  summary: {
    net_pnl: number;
    gross_pnl: number;
    fee: number;
    return_rate: number;
    max_drawdown_rate: number;
    trade_count: number;
    win_count: number;
    loss_count: number;
  };
  daily_equity: { time: string; equity: number }[];
}

export interface SweepTrade {
  kind: "trade";
  entry_id: string;
  side: "buy" | "sell";
  quantity: number;
  opened_at: string | null;
  closed_at: string | null;
  entry_price: number;
  exit_price: number;
  gross_pnl: number;
  fee: number;
  net_pnl: number;
  entry_reason: string | null;
  exit_reason: string | null;
}

export interface SweepFill {
  kind: "fill";
  time: string | null;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  raw_price: number;
  fee: number;
  intent: "entry" | "exit";
  entry_id: string;
  source: string | null;
}

export interface SweepTrades {
  trades: SweepTrade[];
  fills: SweepFill[];
}
