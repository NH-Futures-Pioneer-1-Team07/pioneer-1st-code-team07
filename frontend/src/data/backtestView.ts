import type { BacktestProgress, BacktestRange, DailyBar, JournalLine } from "../apis/types.ts";

export const MIN_CAPITAL = 1_000_000;
export const MAX_CAPITAL = 10_000_000_000;

/** 데이터 준비를 앞 절반, 계산을 뒤 절반으로 보고 전체 진행률(0~100)을 만든다. */
export function progressPercent(progress: BacktestProgress | undefined, status: string): number {
  if (status === "completed" || progress?.stage === "done") return 100;
  if (!progress || progress.total <= 0) return 0;
  const ratio = Math.min(progress.done / progress.total, 1);
  return Math.round((progress.stage === "prepare" ? ratio * 50 : 50 + ratio * 50));
}

export function progressLabel(progress: BacktestProgress | undefined): string {
  if (!progress || progress.total <= 0) return "시작하는 중입니다";
  if (progress.stage === "prepare") return `과거 데이터를 준비하고 있어요 (${progress.done}/${progress.total}일)`;
  if (progress.stage === "compute") return `전략을 계산하고 있어요 (${progress.done}/${progress.total}일)`;
  return "마무리하는 중입니다";
}

export const statusLabel = (status: string) =>
  status === "running"
    ? "실행 중"
    : status === "completed"
      ? "완료"
      : status === "error"
        ? "오류"
        : status === "interrupted"
          ? "중단"
          : status;

/** 입력이 틀렸으면 이유를, 맞으면 빈 문자열을 돌려준다. */
export function validateInput(
  start: string,
  end: string,
  capital: string,
  range: BacktestRange | null,
): string {
  if (!range?.start || !range.end) return "테스트 가능 기간을 아직 알 수 없습니다.";
  if (!start || !end || start > end) return "시작일과 종료일을 확인해 주세요. 시작일은 종료일보다 늦을 수 없습니다.";
  if (start < range.start || end > range.end)
    return `테스트 기간은 ${range.start}부터 ${range.end}까지 선택해 주세요.`;
  const amount = Number(capital);
  if (!Number.isSafeInteger(amount) || amount < MIN_CAPITAL || amount > MAX_CAPITAL)
    return "초기자금은 1,000,000원부터 10,000,000,000원까지 정수로 입력해 주세요.";
  return "";
}

/** `0.000085` → `0.0085%` */
export const percentText = (rate: number) => `${Number((rate * 100).toPrecision(6))}%`;

export const returnText = (rate: number) =>
  `${rate > 0 ? "+" : ""}${(rate * 100).toFixed(2)}%`;

export interface EquityFill {
  time: string;
  side: string;
  quantity: number;
  price: number;
  reason: string;
}

export interface EquityPoint {
  day: string;
  equity: number;
  /** 전날 자산(첫 날은 초기자금) 대비 손익 */
  change: number;
  fills: EquityFill[];
  /** 그날의 일봉. 가격 자료가 없는 기록에는 null */
  bar: DailyBar | null;
}

/** 자산 곡선의 날짜마다 그날의 체결과 일봉을 붙인다. 곡선에 없는 날짜의 체결은 버린다. */
export function equityPoints(
  curve: { time: string; equity: number }[],
  initialCapital: number,
  fills: JournalLine[],
  bars: DailyBar[] = [],
): EquityPoint[] {
  const barByDay = new Map(bars.map((bar) => [bar.date, bar]));
  const byDay = new Map<string, EquityFill[]>();
  for (const line of fills) {
    const day = line.time.slice(0, 10);
    const list = byDay.get(day) ?? [];
    list.push({
      time: line.time.slice(11, 16),
      side: String(line.side),
      quantity: typeof line.quantity === "number" ? line.quantity : 0,
      price: typeof line.price === "number" ? line.price : 0,
      reason: typeof line.reason === "string" ? line.reason : "",
    });
    byDay.set(day, list);
  }
  let previous = initialCapital;
  return curve.map((point) => {
    const day = point.time.slice(0, 10);
    const row = {
      day,
      equity: point.equity,
      change: point.equity - previous,
      fills: byDay.get(day) ?? [],
      bar: barByDay.get(day) ?? null,
    };
    previous = point.equity;
    return row;
  });
}

/** 처음 보여 줄 기간: 가능 기간의 마지막 7일(달력 기준). */
export function defaultPeriod(range: BacktestRange | null): { start: string; end: string } | null {
  if (!range?.start || !range.end) return null;
  const last = new Date(`${range.end}T00:00:00Z`);
  last.setUTCDate(last.getUTCDate() - 6);
  const start = last.toISOString().slice(0, 10);
  return { start: start < range.start ? range.start : start, end: range.end };
}
