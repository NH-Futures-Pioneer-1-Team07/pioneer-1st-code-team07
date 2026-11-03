import type { ParameterSpec, RunSummary } from "../../apis/types";
import { paramSummary } from "../../data/paramView";

/** 이력의 전략 이름. 사용한 파라미터가 있으면 이름 뒤에 괄호로 붙인다. */
export default function RunName({
  run,
  specs,
}: {
  run: Pick<RunSummary, "strategy_name" | "strategy_id" | "params">;
  specs: Record<string, Record<string, ParameterSpec>>;
}) {
  const summary = paramSummary(specs[run.strategy_id], run.params);
  return (
    <>
      <strong>{run.strategy_name}</strong>
      {summary && <span style={{ marginLeft: 6, color: "var(--text-tertiary)", fontSize: 11 }}>({summary})</span>}
    </>
  );
}
