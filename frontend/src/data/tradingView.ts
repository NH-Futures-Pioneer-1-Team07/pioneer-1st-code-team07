import type { Candle, JournalLine, MarketSession, Phase, RunRef, RunSummary, TradingStatus } from "../apis/types.ts";

export const sideLabel = (side: string | null | undefined) =>
  side === "buy" ? "매수" : side === "sell" ? "매도" : "";

/** `2026-10-28T10:03:00+09:00` → `2026.10.28 10:03:00`. 시간대는 바꾸지 않고 서버가 준 한국 시간을 그대로 쓴다. */
export function formatDateTime(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})/.exec(iso);
  return match ? `${match[1]}.${match[2]}.${match[3]} ${match[4]}:${match[5]}:${match[6]}` : iso;
}

/** `100301` → `10:03:01` */
export function formatClock(hhmmss: string | null | undefined): string {
  const text = (hhmmss ?? "").trim();
  return /^\d{6}$/.test(text) ? `${text.slice(0, 2)}:${text.slice(2, 4)}:${text.slice(4)}` : "";
}

/**
 * 종목 이름을 `이름 · 월물` 형식으로 맞춘다.
 * NH 이름(`삼성전자 F 202611 ( 10)`)과 전략 매니페스트 이름(`삼성전자선물 2026년 11월물`)을 모두 받는다.
 */
export function instrumentLabel(name: string): string {
  const nh = /^(.+?)\s+F\s+(\d{4})(\d{2})\b/.exec(name.trim());
  if (nh) return `${nh[1]} 선물 · ${nh[2]}.${nh[3]}`;
  const manifest = /^(.+?)\s*(\d{4})년\s*(\d{1,2})월물$/.exec(name.trim());
  if (manifest) return `${manifest[1].replace(/선물$/, " 선물")} · ${manifest[2]}.${manifest[3].padStart(2, "0")}`;
  return name;
}

const MARKET_SESSION_LABELS: Record<MarketSession, string> = {
  before_open: "장 시작 전",
  auction: "동시호가",
  regular: "정규장",
  closed: "장 마감",
  holiday: "휴장",
  unknown: "장 정보 없음",
};

export const marketSessionLabel = (session: MarketSession | null | undefined): string =>
  MARKET_SESSION_LABELS[session ?? "unknown"] ?? MARKET_SESSION_LABELS.unknown;

/** 상단바에 보이는 시세 스트림 연결 문구. 장이 열렸는지가 아니라 연결 여부만 뜻한다. */
export const streamLabel = (state: string, failure: string | null): string =>
  state === "live" ? "시세 연결됨" : failure ? `시세 연결 끊김: ${failure}` : "시세 연결 중";

/** 이력 제목 옆에 보이는 이력 웹소켓 연결 문구. */
export const runStreamLabel = (state: string): string =>
  state === "live" ? "이력 실시간 연결됨" : state === "disconnected" ? "이력 연결 끊김" : "이력 연결 중";

/** 상단바에 보일 국내장 장 상태와 시세 연결 상태. 모의매매 화면이 채운다. */
export interface MarketStatus {
  session: MarketSession | null;
  stream: string;
  failure: string | null;
}

export const signed = (value: number, format: (n: number) => string) =>
  `${value > 0 ? "+" : ""}${format(value)}`;

const resultLabels: Record<string, string> = {
  buy: "매수",
  sell: "매도",
  hold: "진입 보류",
  skip: "건너뜀",
};

export interface DecisionRowView {
  key: string;
  at: string;
  action: string;
  reason: string;
  price: number | null;
  quantity: number | null;
}

export interface FillRowView {
  key: string;
  at: string;
  side: string;
  quantity: number;
  price: number;
  fee: number | null;
}

const num = (value: unknown): number | null => (typeof value === "number" ? value : null);

export function mapDecisions(lines: JournalLine[]): DecisionRowView[] {
  return lines.map((line) => {
    const orders = Array.isArray(line.orders) ? (line.orders as { quantity?: number }[]) : [];
    const quantity = orders.reduce((sum, order) => sum + (order.quantity ?? 0), 0);
    return {
      key: String(line.seq),
      at: formatDateTime(line.time),
      action: resultLabels[String(line.result)] ?? String(line.result ?? ""),
      reason: typeof line.reason === "string" ? line.reason : "",
      price: null,
      quantity: quantity > 0 ? quantity : null,
    };
  });
}

export function mapFills(lines: JournalLine[]): FillRowView[] {
  return lines.map((line) => ({
    key: String(line.seq),
    at: formatDateTime(line.time),
    side: sideLabel(String(line.side)),
    quantity: num(line.quantity) ?? 0,
    price: num(line.price) ?? 0,
    fee: num(line.fee),
  }));
}

export const phaseLabel = (phase: Phase): string =>
  phase === "running" ? "운용 중" : phase === "stopping" || phase === "clearing" ? "정리 중" : "대기";

/** 화면 아래 상태 줄에 보여 줄 문장. 방금 한 동작의 오류가 있으면 그것이 먼저다. */
export function statusMessage(status: TradingStatus | null, actionError: string | null): string {
  if (actionError) return actionError;
  if (!status) return "";
  const clear = status.clear;
  if (clear?.state === "running") return `계좌 전체 정리 중: ${clear.detail}`;
  if (status.phase === "stopping") return "운용을 종료하는 중입니다. 미체결 주문을 취소하고 보유 포지션을 청산합니다.";
  if (status.phase === "running") {
    const blocks = status.entry_blocks ?? [];
    return blocks.length ? `신규 주문을 멈췄습니다: ${blocks.join(", ")}` : "";;
  }
  if (clear?.state === "done" && clear.result) {
    const result = clear.result;
    if (result.status === "completed") return `계좌 전체 정리를 마쳤습니다. 미체결 ${result.cancelled}건을 취소했습니다.`;
    const problems = result.problems.length ? ` (${result.problems.join("; ")})` : "";
    return `정리가 끝나지 않았습니다. 남은 미체결 ${result.open_orders.length}건, 보유 ${result.positions.length}건${problems}`;
  }
  if (status.last_run?.status === "error") return "직전 운용이 오류로 끝났습니다. 계좌의 보유 포지션과 미체결 주문을 확인하세요.";
  return "";
}

// ---- 차트 ----

export interface CandleShape {
  x: number;
  width: number;
  wickTop: number;
  wickBottom: number;
  bodyTop: number;
  bodyHeight: number;
  volumeTop: number;
  volumeHeight: number;
  rising: boolean;
}

export interface ChartLayout {
  shapes: CandleShape[];
  ticks: { y: number; value: number }[];
  lastY: number | null;
  min: number;
  max: number;
}

/** 캔들과 거래량을 `width × height` 안에 놓는다. 오른쪽 `axisWidth`는 가격 눈금 자리다. */
export function chartLayout(candles: Candle[], width: number, height: number, axisWidth: number): ChartLayout {
  const empty: ChartLayout = { shapes: [], ticks: [], lastY: null, min: 0, max: 0 };
  if (!candles.length || width <= axisWidth) return empty;
  const top = 12;
  const priceBottom = height * 0.76;
  const volumeBottom = height - 22;
  const lows = candles.map((c) => c.low);
  const highs = candles.map((c) => c.high);
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const span = max - min || Math.max(max * 0.001, 1);
  const y = (price: number) => top + ((max - price) / span) * (priceBottom - top);
  const maxVolume = Math.max(...candles.map((c) => c.volume), 1);
  const slot = (width - axisWidth) / candles.length;
  const bar = Math.max(1, Math.min(slot * 0.7, 14));

  const shapes = candles.map((candle, index) => {
    const open = candle.open ?? (index > 0 ? candles[index - 1].close : candle.close);
    const x = index * slot + (slot - bar) / 2;
    const bodyTop = y(Math.max(open, candle.close));
    const bodyBottom = y(Math.min(open, candle.close));
    const volumeHeight = Math.max(1, (candle.volume / maxVolume) * (volumeBottom - priceBottom - 6));
    return {
      x,
      width: bar,
      wickTop: y(candle.high),
      wickBottom: y(candle.low),
      bodyTop,
      bodyHeight: Math.max(1.5, bodyBottom - bodyTop),
      volumeTop: volumeBottom - volumeHeight,
      volumeHeight,
      rising: candle.close >= open,
    };
  });
  const ticks = [0, 1, 2, 3].map((row) => {
    const value = max - (span * row) / 3;
    return { y: y(value), value };
  });
  return { shapes, ticks, lastY: y(candles[candles.length - 1].close), min, max };
}

/** 가로축에 보여 줄 시각 눈금 네 개. */
export function timeTicks(candles: Candle[], daily: boolean): { index: number; label: string }[] {
  if (!candles.length) return [];
  const picks = [0, 1, 2, 3].map((n) => Math.round(((candles.length - 1) * n) / 3));
  return [...new Set(picks)].map((index) => {
    const time = candles[index].time;
    return { index, label: daily ? time.slice(5).replace("-", ".") : time.slice(11, 16) };
  });
}

/** 실행 하나를 가리키는 키. 목록에서 선택·갱신할 때 쓴다. */
export const runKey = (run: RunRef) => `${run.strategy_id}/${run.run_id}`;

/** 모의매매 이력 목록과 상세에 보이는 운용 상태 문구. */
export const runStatusLabel = (run: Pick<RunSummary, "ended_at" | "status">): string =>
  run.ended_at
    ? run.status === "error"
      ? "오류"
      : run.status === "interrupted"
        ? "중단"
        : "종료"
    : "운용 중";

/** 시작 시각이 최근인 실행이 앞에 오도록 목록에 실행 하나를 넣거나 바꾼다. */
export const upsertRun = (runs: RunSummary[], run: RunSummary): RunSummary[] =>
  [run, ...runs.filter((item) => runKey(item) !== runKey(run))].sort((a, b) =>
    b.started_at.localeCompare(a.started_at),
  );
