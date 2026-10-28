import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage } from "./client";

/** 일정 간격으로 `fetcher`를 불러 결과를 돌려준다. 오류가 나도 마지막 값을 유지한다. */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  deps: unknown[] = [],
  enabled = true,
): { data: T | null; error: string | null; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const latest = useRef(fetcher);
  latest.current = fetcher;
  const key = JSON.stringify(deps);
  const lastKey = useRef(key);
  const reload = useCallback(() => setTick((value) => value + 1), []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer: number | undefined;
    const run = async () => {
      try {
        const value = await latest.current();
        if (cancelled) return;
        setData(value);
        setError(null);
      } catch (failure) {
        if (!cancelled) setError(errorMessage(failure));
      }
      if (!cancelled) timer = window.setTimeout(run, intervalMs);
    };
    if (lastKey.current !== key) {
      lastKey.current = key;
      setData(null);
    }
    void run();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [intervalMs, enabled, tick, key]);

  return { data, error, reload };
}
