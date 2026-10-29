import { useEffect, useState } from "react";
import { errorMessage } from "../../apis/client";
import { useMarketStream } from "../../apis/marketStream";
import { usePolling } from "../../apis/polling";
import { useRunStream } from "../../apis/runStream";
import {
  fetchAccount,
  fetchCandles,
  fetchOrderBook,
  fetchQuote,
  fetchStatus,
  fetchStrategies,
  fetchStrategy,
} from "../../apis/trading";
import { formatClock } from "../../data/tradingView";
import type { MarketStatus } from "../../data/tradingView";

/** 모의매매 화면의 서버 조회, 시세 스트림, 운용 동작을 모은 훅. 화면 영역 컴포넌트가 이 값을 나눠 쓴다. */
export function useTradingPage(onMarketStatus: (status: MarketStatus) => void) {
  const [selected, setSelected] = useState<string | null>(null);
  const [interval, setInterval] = useState("5");
  const [confirm, setConfirm] = useState<"stop" | "all" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const strategies = usePolling(fetchStrategies, 60000);
  const status = usePolling(fetchStatus, 2000);
  const account = usePolling(fetchAccount, 5000);
  const runStream = useRunStream("paper");

  const phase = status.data?.phase ?? "idle";
  const items = strategies.data ?? [];
  const activeId = status.data?.run?.strategy_id ?? null;
  const strategyId = activeId ?? selected ?? items[0]?.id ?? null;
  const running = phase !== "idle";
  const pending = phase === "stopping" || phase === "clearing";
  const clearing = status.data?.clear?.state === "running";

  const detail = usePolling(
    () => fetchStrategy(strategyId as string),
    600000,
    [strategyId],
    !!strategyId,
  );
  const instrument = detail.data?.instruments[0] ?? null;
  const code = instrument?.code ?? null;

  const quote = usePolling(() => fetchQuote(code as string), 3000, [code], !!code);
  const candles = usePolling(
    () => fetchCandles(code as string, interval),
    5000,
    [code, interval],
    !!code,
  );
  const book = usePolling(() => fetchOrderBook(code as string), 3000, [code], !!code);
  const stream = useMarketStream(code);

  const livePrice = stream.lastTrade?.price ?? quote.data?.price ?? null;
  const prevClose = quote.data?.prev_close ?? null;
  const changeRate =
    livePrice !== null && prevClose ? ((livePrice - prevClose) / prevClose) * 100 : null;
  const levels = (stream.book ?? book.data)?.levels.slice(0, 5) ?? [];
  const totalAsk = (stream.book ?? book.data)?.total_ask_quantity ?? null;
  const totalBid = (stream.book ?? book.data)?.total_bid_quantity ?? null;
  const askShare =
    totalAsk !== null && totalBid !== null && totalAsk + totalBid > 0
      ? (totalAsk / (totalAsk + totalBid)) * 100
      : 50;
  const maxQuantity = Math.max(
    1,
    ...levels.flatMap((level) => [level.ask_quantity ?? 0, level.bid_quantity ?? 0]),
  );

  const deposit = account.data?.deposit;
  const positions = account.data?.positions ?? [];
  const openOrders = account.data?.open_orders ?? [];
  const pnl = status.data?.pnl;
  const session = quote.data?.market_session ?? null;
  useEffect(() => {
    onMarketStatus({ session, stream: stream.state, failure: stream.failure });
  }, [onMarketStatus, session, stream.state, stream.failure]);
  const receivedAt = formatClock(stream.lastTrade?.time);

  const act = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setActionError(null);
    try {
      await action();
    } catch (failure) {
      setActionError(errorMessage(failure));
    } finally {
      setBusy(false);
      status.reload();
      account.reload();
    }
  };

  return {
    selected, setSelected, interval, setInterval, confirm, setConfirm, actionError, busy, strategies, status, account, runStream, phase, items, activeId, strategyId, running, pending, clearing, detail, instrument, code, quote, candles, book, stream, livePrice, prevClose, changeRate, levels, totalAsk, totalBid, askShare, maxQuantity, deposit, positions, openOrders, pnl, session, receivedAt, act,
  };
}

export type TradingController = ReturnType<typeof useTradingPage>;
