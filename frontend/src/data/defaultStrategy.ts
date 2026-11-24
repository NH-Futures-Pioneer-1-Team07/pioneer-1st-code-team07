/** 전략 id의 `weekNN_` 접두사에서 주차를 읽는다. 접두사가 없으면 0이다. */
export function weekOf(strategyId: string): number {
  const match = /^week(\d+)_/.exec(strategyId);
  return match ? Number(match[1]) : 0;
}

/** 목록에서 가장 최근 주차의 항목을 고른다. 주차가 같으면 id가 사전순으로 뒤선 항목이 이긴다(`week04_zf_…`가 `week04_z3n_…`보다 뒤). */
export function latestWeek<T>(items: readonly T[], idOf: (item: T) => string): T | undefined {
  return items.reduce<T | undefined>((best, item) => {
    if (best === undefined) return item;
    const gap = weekOf(idOf(item)) - weekOf(idOf(best));
    return gap > 0 || (gap === 0 && idOf(item) > idOf(best)) ? item : best;
  }, undefined);
}

const DEFAULT_RUN_STRATEGY_ID = "week06_zn_intraday_average_entry";

/** 모의매매와 백테스트의 초기 전략을 고른다. 미등록 환경에서는 최신 주차를 쓴다. */
export function defaultRunStrategy<T extends { id: string }>(items: readonly T[]): T | undefined {
  return items.find((item) => item.id === DEFAULT_RUN_STRATEGY_ID) ?? latestWeek(items, (item) => item.id);
}
