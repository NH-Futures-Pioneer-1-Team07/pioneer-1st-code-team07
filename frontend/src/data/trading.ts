import { instruments, strategies } from "./fixtures.ts";
import type { Instrument, Strategy } from "./fixtures.ts";

export type Phase = "idle" | "running" | "stopping" | "clearing";
export interface Position {
  id: string;
  runId: string | null;
  instrumentId: string;
  side: "매수" | "매도";
  quantity: number;
  average: number;
  price: number;
  pnl: number;
}
export interface Order {
  id: string;
  runId: string | null;
  instrumentId: string;
  side: "매수" | "매도";
  type: string;
  at: string;
  price: number;
  quantity: number;
  filled: number;
  status: string;
  score: number | null;
  originalId?: string;
  note?: string;
}
export interface Fill {
  id: string;
  orderId: string;
  at: string;
  quantity: number;
  price: number;
  score: number | null;
}
export interface Decision {
  at: string;
  score: number;
  action: string;
  price: number | null;
  quantity: number | null;
}
export interface RunRecord {
  id: string;
  strategy: Strategy;
  instrument: Instrument;
  startedAt: string;
  endedAt: string | null;
  pnl: number;
  cost: number;
  decisions: Decision[];
  orders: Order[];
  fills: Fill[];
}
export interface TradingState {
  phase: Phase;
  activeRunId: string | null;
  positions: Position[];
  orders: Order[];
  runs: RunRecord[];
  sequence: number;
  externalRealized: number;
  message: string;
}

const TODAY = "2026.10.27";
const YESTERDAY = "2026.10.26";

const decisionSamples = (
  strategy: Strategy,
  entry: number,
  day: string,
): Decision[] => [
  {
    at: `${day} 10:32:00`,
    score: strategy.score,
    action: "매수",
    price: entry,
    quantity: 2,
  },
  {
    at: `${day} 10:31:00`,
    score: 59,
    action: "진입 보류",
    price: null,
    quantity: null,
  },
  {
    at: `${day} 10:30:00`,
    score: 72,
    action: "매수",
    price: entry,
    quantity: 1,
  },
];

function makeRun(
  id: string,
  strategy: Strategy,
  instrument: Instrument,
  historical = false,
): RunRecord {
  const day = historical ? YESTERDAY : TODAY;
  const at = (time: string) => `${day} ${time}`;
  const entry = instrument.price - (instrument.id === "samsung" ? 2400 : 0.1);
  const pnl = Math.round(
    (instrument.price - entry) *
      2 *
      (instrument.id === "samsung" ? 10 : 250000),
  );
  const order = (
    suffix: string,
    status: string,
    quantity: number,
    filled: number,
    options: Partial<Order> = {},
  ): Order => ({
    id: `${id}-${suffix}`,
    runId: id,
    instrumentId: instrument.id,
    side: "매수",
    type: "지정가",
    at: at("10:30:02"),
    price: instrument.price,
    quantity,
    filled,
    status,
    score: strategy.score,
    ...options,
  });
  const orders: Order[] = [
    order("01", "전체체결", 1, 1, { score: 72, price: entry }),
    order("02", historical ? "취소" : "부분체결", 2, 1, {
      at: at("10:32:02"),
      price: entry,
    }),
    order("03", "취소", 1, 0, {
      at: at("10:32:03"),
      note: "연결 취소 주문으로 잔량 취소",
    }),
    order("04", "거부", 1, 0, {
      note: "주문 가능 수량 초과 · 샘플 오류 NH-DEMO-01",
      at: at("10:32:05"),
    }),
    order("05", "취소", 1, 0, {
      originalId: `${id}-03`,
      type: "취소",
      note: "원주문 잔량 취소 예시",
      at: at("10:32:06"),
    }),
    order("07", "정정", 1, 0, {
      at: at("10:32:04"),
      note: "정정 주문으로 대체됨",
    }),
    order("06", historical ? "취소" : "접수", 1, 0, {
      originalId: `${id}-07`,
      type: "정정",
      note: "가격 정정 접수 예시",
      at: at("10:32:07"),
    }),
    order("08", historical ? "취소" : "미체결", 1, 0, { at: at("10:32:08") }),
  ];
  const fills: Fill[] = [
    {
      id: `${id}-F1`,
      orderId: `${id}-01`,
      at: at("10:30:03"),
      quantity: 1,
      price: entry,
      score: 72,
    },
    {
      id: `${id}-F2`,
      orderId: `${id}-02`,
      at: at("10:32:03"),
      quantity: 1,
      price: entry,
      score: strategy.score,
    },
  ];
  if (historical) {
    orders.push(
      order("CLOSE", "전체체결", 2, 2, {
        at: at("15:20:00"),
        type: "시장가",
        side: "매도",
        score: null,
        note: "운용 종료 청산",
      }),
    );
    fills.push({
      id: `${id}-FC`,
      orderId: `${id}-CLOSE`,
      at: at("15:20:00"),
      quantity: 2,
      price: instrument.price,
      score: null,
    });
  }
  return {
    id,
    strategy: {
      ...strategy,
      symbols: [...strategy.symbols],
      indicators: [...strategy.indicators],
    },
    instrument: { ...instrument },
    startedAt: historical ? `${YESTERDAY} 09:15:00` : `${TODAY} 10:30:00`,
    endedAt: historical ? `${YESTERDAY} 15:20:00` : null,
    pnl,
    cost: 2400,
    decisions: decisionSamples(strategy, entry, day),
    orders,
    fills,
  };
}

export function createTradingState(): TradingState {
  return {
    phase: "idle",
    activeRunId: null,
    sequence: 0,
    externalRealized: 0,
    message: "",
    positions: [
      {
        id: "existing-position",
        runId: null,
        instrumentId: "samsung",
        side: "매수",
        quantity: 1,
        average: 71600,
        price: 72400,
        pnl: 8000,
      },
    ],
    orders: [
      {
        id: "EXISTING-01",
        runId: null,
        instrumentId: "samsung",
        side: "매수",
        type: "지정가",
        at: `${TODAY} 09:15:00`,
        price: 71000,
        quantity: 1,
        filled: 0,
        status: "미체결",
        score: null,
      },
    ],
    runs: [makeRun("DEMO-001", strategies[0], instruments[0], true)],
  };
}

export function startRun(
  state: TradingState,
  strategy: Strategy,
  instrument: Instrument,
): TradingState {
  if (state.phase !== "idle" || !strategy.symbols.includes(instrument.id))
    return state;
  const sequence = state.sequence + 1;
  const run = makeRun(
    `DEMO-${String(sequence + 1).padStart(3, "0")}`,
    strategy,
    instrument,
  );
  return {
    ...state,
    sequence,
    phase: "running",
    activeRunId: run.id,
    message: `${strategy.name} 샘플 운용을 시작했습니다.`,
    positions: [
      ...state.positions,
      {
        id: `${run.id}-position`,
        runId: run.id,
        instrumentId: instrument.id,
        side: "매수",
        quantity: 2,
        average: run.fills[0].price,
        price: instrument.price,
        pnl: run.pnl,
      },
    ],
    orders: [...state.orders, ...run.orders],
    runs: [run, ...state.runs],
  };
}

const INITIAL_CASH = 50_000_000;
const MARGIN_PER_CONTRACT = 1_200_000;

export interface AccountSummary {
  /** 예탁현금: 맡긴 현금에 확정된 운용 손익을 반영한 금액 */
  cash: number;
  /** 사용 증거금: 보유 포지션에 묶인 금액 */
  margin: number;
  /** 보유 포지션의 평가손익 합계 */
  evaluation: number;
  /** 예탁자산: 예탁현금 + 평가손익 */
  assets: number;
  /** 주문 가능 금액: 예탁현금 - 사용 증거금 */
  orderable: number;
}

export function accountSummary(state: TradingState): AccountSummary {
  const sum = (values: number[]) =>
    values.reduce((total, value) => total + value, 0);
  const margin = sum(
    state.positions.map((position) => position.quantity * MARGIN_PER_CONTRACT),
  );
  const cash =
    INITIAL_CASH +
    state.externalRealized +
    sum(
      state.runs.filter((run) => run.endedAt).map((run) => run.pnl - run.cost),
    );
  const evaluation = sum(state.positions.map((position) => position.pnl));
  return {
    cash,
    margin,
    evaluation,
    assets: cash + evaluation,
    orderable: cash - margin,
  };
}

export const remaining = (order: Order) =>
  ["미체결", "부분체결", "접수"].includes(order.status)
    ? order.quantity - order.filled
    : 0;

export function beginStop(state: TradingState, all: boolean): TradingState {
  if (
    state.phase === "stopping" ||
    state.phase === "clearing" ||
    (!all && state.phase !== "running")
  )
    return state;
  return {
    ...state,
    phase: all ? "clearing" : "stopping",
    message: all
      ? "계좌 전체 신규 판단 중단 → 미체결 취소 → 포지션 청산을 시연합니다."
      : "현재 운용 신규 판단 중단 → 미체결 취소 → 포지션 청산을 시연합니다.",
  };
}

export function finishStop(state: TradingState): TradingState {
  if (state.phase !== "stopping" && state.phase !== "clearing") return state;
  const all = state.phase === "clearing";
  const applies = (runId: string | null) => all || runId === state.activeRunId;
  const orders = state.orders.map((order) =>
    applies(order.runId) && remaining(order) > 0
      ? { ...order, status: "취소", note: "종료 처리로 잔량 취소" }
      : order,
  );
  const active = state.runs.find((run) => run.id === state.activeRunId);
  let completed: RunRecord | undefined;
  if (active) {
    const closingOrder: Order = {
      id: `${active.id}-CLOSE`,
      runId: active.id,
      instrumentId: active.instrument.id,
      side: "매도",
      type: "시장가",
      at: `${TODAY} 10:33:00`,
      price: active.instrument.price,
      quantity: 2,
      filled: 2,
      status: "전체체결",
      score: null,
      note: all ? "계좌 전체 청산" : "운용 종료 청산",
    };
    orders.push(closingOrder);
    completed = {
      ...active,
      endedAt: `${TODAY} 10:33:00`,
      orders: [...orders.filter((order) => order.runId === active.id)],
      fills: [
        ...active.fills,
        {
          id: `${active.id}-FC`,
          orderId: closingOrder.id,
          at: `${TODAY} 10:33:00`,
          quantity: 2,
          price: active.instrument.price,
          score: null,
        },
      ],
    };
  }
  return {
    ...state,
    phase: "idle",
    activeRunId: null,
    orders,
    externalRealized:
      state.externalRealized +
      (all
        ? state.positions
            .filter((position) => position.runId === null)
            .reduce((sum, position) => sum + position.pnl, 0)
        : 0),
    positions: state.positions.filter((position) => !applies(position.runId)),
    runs: state.runs.map((run) => (run.id === completed?.id ? completed : run)),
    message: all
      ? "샘플 계좌 정리 완료 · 미체결 0건 · 보유 0계약"
      : "샘플 운용 종료 · 해당 운용 미체결 0건 · 보유 0계약. 기존 계좌 주문·포지션은 유지됩니다.",
  };
}
