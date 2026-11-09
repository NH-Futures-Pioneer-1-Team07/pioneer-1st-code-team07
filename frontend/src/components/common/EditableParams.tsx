import { useEffect, useMemo, useState } from "react";
import type { ParameterSpec } from "../../apis/types";
import { defaultInputs, editableParams, firstProblem, paramProblem, paramsBody, unitLabel } from "../../data/paramView";
import Icon from "./Icon";
import styles from "./EditableParams.module.css";

/** 전략이 화면에서 바꿀 수 있다고 선언한 파라미터의 입력값. 전략이 바뀌거나 기본값이 바뀌면 기본값으로 되돌린다. */
export function useParamInputs(strategyId: string | null, parameters: Record<string, ParameterSpec> | undefined) {
  const entries = useMemo(() => editableParams(parameters), [parameters]);
  const defaults = JSON.stringify(defaultInputs(entries));
  const [values, setValues] = useState<Record<string, string>>({});
  useEffect(() => setValues(JSON.parse(defaults) as Record<string, string>), [strategyId, defaults]);
  const shown = { ...JSON.parse(defaults), ...values } as Record<string, string>;
  return {
    entries,
    values: shown,
    setValue: (name: string, text: string) => setValues((current) => ({ ...current, [name]: text })),
    problem: firstProblem(entries, shown),
    body: () => paramsBody(entries, shown),
  };
}

export type ParamInputs = ReturnType<typeof useParamInputs>;

export default function EditableParams({
  inputs,
  disabled,
  idPrefix,
}: {
  inputs: ParamInputs;
  disabled?: boolean;
  idPrefix: string;
}) {
  const { entries, values, setValue } = inputs;
  if (entries.length === 0) return null;
  return (
    <fieldset className={styles.params} disabled={disabled}>
      {entries.map(([name, spec]) => {
        const problem = paramProblem(name, spec, values[name] ?? "");
        const id = `${idPrefix}-${name}`;
        return (
          <div key={name} className="field">
            <span className={styles.labelRow}>
              <label htmlFor={id}>{spec.label ?? name}</label>
              <span className={styles.info} tabIndex={0} role="img" aria-label={`${spec.label ?? name} 설명`} aria-describedby={`${id}-help`}>
                <Icon name="info" size={13} />
                <span role="tooltip" id={`${id}-help`} className={styles.tip}>
                  {spec.description}
                </span>
              </span>
            </span>
            <div className={styles.input}>
              <input
                id={id}
                type="text"
                inputMode="decimal"
                autoComplete="off"
                value={values[name] ?? ""}
                aria-invalid={problem ? true : undefined}
                aria-describedby={problem ? `${id}-problem` : undefined}
                onChange={(event) => setValue(name, event.target.value.replace(/[^\d.]/g, "").slice(0, 7))}
              />
              <span>{unitLabel(spec)}</span>
            </div>
            {problem && (
              <p className={styles.problem} id={`${id}-problem`} role="alert">
                {problem}
              </p>
            )}
          </div>
        );
      })}
    </fieldset>
  );
}
