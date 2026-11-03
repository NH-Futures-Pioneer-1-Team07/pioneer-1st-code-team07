import { useEffect, useState } from "react";
import type { ParameterSpec } from "./types";
import { fetchStrategy } from "./trading";

/** 전략 id별 파라미터 명세. 이력 목록에 나오는 전략의 것을 한 번씩만 불러온다. */
export function useStrategySpecs(strategyIds: string[]): Record<string, Record<string, ParameterSpec>> {
  const [specs, setSpecs] = useState<Record<string, Record<string, ParameterSpec>>>({});
  const missing = [...new Set(strategyIds)].filter((id) => !(id in specs)).sort().join(",");
  useEffect(() => {
    if (!missing) return;
    let cancelled = false;
    for (const id of missing.split(",")) {
      fetchStrategy(id)
        .then((detail) => !cancelled && setSpecs((current) => ({ ...current, [id]: detail.parameters })))
        // 지워진 전략처럼 명세를 못 불러오면 파라미터 표시만 건너뛴다.
        .catch(() => !cancelled && setSpecs((current) => ({ ...current, [id]: {} })));
    }
    return () => {
      cancelled = true;
    };
  }, [missing]);
  return specs;
}
