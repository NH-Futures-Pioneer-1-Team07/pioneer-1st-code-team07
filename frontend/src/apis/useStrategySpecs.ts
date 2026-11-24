import { useEffect, useState } from "react";
import type { ParameterSpec } from "./types";
import { fetchStrategies, fetchStrategy } from "./trading";

type Specs = Record<string, Record<string, ParameterSpec>>;

/** 등록된 전략의 파라미터 명세를 불러온다. 지워졌거나 못 불러온 전략은 빈 명세로 둔다. */
async function loadSpecs(ids: string[]): Promise<Specs> {
  const registered = await fetchStrategies().then(
    (items) => new Set(items.map((item) => item.id)),
    () => new Set<string>(),
  );
  const entries = await Promise.all(
    ids.map(async (id) => {
      if (!registered.has(id)) return [id, {}] as const;
      const parameters = await fetchStrategy(id).then((detail) => detail.parameters, () => ({}));
      return [id, parameters] as const;
    }),
  );
  return Object.fromEntries(entries);
}

/** 전략 id별 파라미터 명세. 이력 목록에 나오는 전략의 것을 한 번씩만 불러온다. */
export function useStrategySpecs(strategyIds: string[]): Specs {
  const [specs, setSpecs] = useState<Specs>({});
  const missing = [...new Set(strategyIds)].filter((id) => !(id in specs)).sort().join(",");
  useEffect(() => {
    if (!missing) return;
    let cancelled = false;
    void loadSpecs(missing.split(",")).then(
      (loaded) => !cancelled && setSpecs((current) => ({ ...current, ...loaded })),
    );
    return () => {
      cancelled = true;
    };
  }, [missing]);
  return specs;
}
