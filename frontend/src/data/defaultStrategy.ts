/** 전략 id의 `weekNN_` 접두사에서 주차를 읽는다. 접두사가 없으면 0이다. */
export function weekOf(strategyId: string): number {
  const match = /^week(\d+)_/.exec(strategyId);
  return match ? Number(match[1]) : 0;
}

/** 목록에서 가장 최근 주차의 항목을 고른다. 주차가 같으면 앞선 항목이 이긴다. */
export function latestWeek<T>(items: readonly T[], idOf: (item: T) => string): T | undefined {
  return items.reduce<T | undefined>(
    (best, item) => (best === undefined || weekOf(idOf(item)) > weekOf(idOf(best)) ? item : best),
    undefined,
  );
}
