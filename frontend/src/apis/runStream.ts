import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { JournalLine, RunSummary } from "./types";

export type RunMessage =
  | { type: "ready" }
  | { type: "resync" }
  | { type: "run"; run: RunSummary }
  | { type: "journal"; line: JournalLine }
  | { type: "pnl"; strategy_id: string; mode: string; run_id: string; net_pnl: number };

export interface RunStream {
  /** `connecting`, `live`(서버가 `ready`를 보낸 뒤), `disconnected` */
  state: string;
  /** `ready`·`resync`를 받을 때마다 늘어난다. 늘어나면 REST로 현재 상태를 다시 조회한다 */
  syncs: number;
  subscribe: (listener: (message: RunMessage) => void) => () => void;
}

const RETRY_MS = [1000, 2000, 5000];

export const runStreamUrl = (mode: string, location: Pick<Location, "protocol" | "host">) =>
  `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/runs?mode=${mode}`;

/** 실행 이력의 변경을 받는다. 끊기면 다시 연결한다. */
export function useRunStream(mode: "paper" | "backtest"): RunStream {
  const [state, setState] = useState("connecting");
  const [syncs, setSyncs] = useState(0);
  const listeners = useRef(new Set<(message: RunMessage) => void>());

  const subscribe = useCallback((listener: (message: RunMessage) => void) => {
    listeners.current.add(listener);
    return () => {
      listeners.current.delete(listener);
    };
  }, []);

  useEffect(() => {
    let closed = false;
    let socket: WebSocket | null = null;
    let retry = 0;
    let timer: number | undefined;

    const connect = () => {
      setState("connecting");
      socket = new WebSocket(runStreamUrl(mode, window.location));
      socket.onmessage = (event) => {
        retry = 0;
        const message = JSON.parse(event.data) as RunMessage;
        if (message.type === "ready") setState("live");
        if (message.type === "ready" || message.type === "resync") setSyncs((count) => count + 1);
        listeners.current.forEach((listener) => listener(message));
      };
      socket.onclose = () => {
        if (closed) return;
        setState("disconnected");
        timer = window.setTimeout(connect, RETRY_MS[Math.min(retry++, RETRY_MS.length - 1)]);
      };
    };
    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      socket?.close();
    };
  }, [mode]);

  return useMemo(() => ({ state, syncs, subscribe }), [state, syncs, subscribe]);
}
