import { useEffect, useState } from "react";
import type { MarketMessage, OrderBook } from "./types";

type Trade = Extract<MarketMessage, { type: "trade" }>;

export interface MarketStream {
  /** `connecting`, `live`, `reconnecting`, `stopped`, 또는 화면과 서버 사이가 끊긴 `disconnected` */
  state: string;
  lastTrade: Trade | null;
  book: OrderBook | null;
  /** 시세가 끊겼다 다시 연결된 횟수. 늘어나면 REST로 다시 조회한다 */
  reconnects: number;
  failure: string | null;
}

const RETRY_MS = [1000, 2000, 5000];

export const streamUrl = (code: string, location: Pick<Location, "protocol" | "host">) =>
  `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/market?code=${code}`;

/** 종목의 실시간 체결·호가를 받는다. 끊기면 다시 연결한다. */
export function useMarketStream(code: string | null): MarketStream {
  const [stream, setStream] = useState<MarketStream>({
    state: "connecting",
    lastTrade: null,
    book: null,
    reconnects: 0,
    failure: null,
  });

  useEffect(() => {
    setStream({ state: "connecting", lastTrade: null, book: null, reconnects: 0, failure: null });
    if (!code) return;
    let closed = false;
    let socket: WebSocket | null = null;
    let retry = 0;
    let timer: number | undefined;

    const connect = () => {
      socket = new WebSocket(streamUrl(code, window.location));
      socket.onmessage = (event) => {
        retry = 0;
        const message = JSON.parse(event.data) as MarketMessage;
        setStream((current) => apply(current, message));
      };
      socket.onclose = (event) => {
        if (closed) return;
        if (event.code >= 4000) {
          setStream((current) => ({ ...current, state: "disconnected", failure: event.reason || `연결이 거부되었습니다 (${event.code})` }));
          return;
        }
        setStream((current) => ({ ...current, state: "disconnected" }));
        timer = window.setTimeout(connect, RETRY_MS[Math.min(retry++, RETRY_MS.length - 1)]);
      };
    };
    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      socket?.close();
    };
  }, [code]);

  return stream;
}

export function apply(current: MarketStream, message: MarketMessage): MarketStream {
  switch (message.type) {
    case "state":
      return { ...current, state: message.state, failure: null };
    case "trade":
      return message.is_trade ? { ...current, lastTrade: message } : current;
    case "orderbook":
      return { ...current, book: message };
    case "reconnected":
      return { ...current, reconnects: current.reconnects + 1 };
    case "subscription_failed":
      return { ...current, failure: message.message || message.reason_code };
  }
}
