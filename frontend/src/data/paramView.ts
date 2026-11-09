import type { ParameterSpec } from "../apis/types.ts";

export type ParamEntry = [name: string, spec: ParameterSpec];

/** 화면에서 바꿀 수 있는 숫자 파라미터만 골라 명세 순서대로 돌려준다. */
export const editableParams = (parameters: Record<string, ParameterSpec> | undefined): ParamEntry[] =>
  Object.entries(parameters ?? {}).filter(([, spec]) => spec.editable && typeof spec.default === "number");

const shown = (spec: ParameterSpec, value: number): string =>
  String(Number((spec.unit === "percent" ? value * 100 : value).toFixed(6)));

export const unitLabel = (spec: ParameterSpec): string => (spec.unit === "percent" ? "%" : "");

/** 화면에서 바꿀 수 있는 숫자 파라미터 값의 표시. 퍼센트 단위는 비율을 퍼센트로 바꾼다(0.2 → `20%`). 그 외 값은 `null`이다. */
export function editableValueText(spec: ParameterSpec | undefined, value: unknown): string | null {
  return spec?.editable && typeof spec.default === "number" && typeof value === "number"
    ? `${shown(spec, value)}${unitLabel(spec)}`
    : null;
}

/** 이력에 붙일 사용 파라미터 요약. 화면에서 바꿀 수 있는 숫자 파라미터만 "이름 값" 순서로 쉼표로 잇는다. 없으면 빈 문자열이다. */
export function paramSummary(
  parameters: Record<string, ParameterSpec> | undefined,
  params: Record<string, unknown> | null | undefined,
): string {
  return editableParams(parameters)
    .flatMap(([name, spec]) => {
      const value = params?.[name];
      return typeof value === "number" ? [`${spec.label ?? name} ${shown(spec, value)}${unitLabel(spec)}`] : [];
    })
    .join(", ");
}

/** 입력칸의 처음 값. 전략이 정한 기본값이다. */
export const defaultInputs = (entries: ParamEntry[]): Record<string, string> =>
  Object.fromEntries(entries.map(([name, spec]) => [name, shown(spec, spec.default as number)]));

const bound = (spec: ParameterSpec, value: number | null): string | null => (value === null ? null : shown(spec, value));

/** 입력값이 허용 범위를 벗어나거나 숫자가 아니면 사유를 돌려준다. */
export function paramProblem(name: string, spec: ParameterSpec, text: string): string | null {
  const label = spec.label ?? name;
  const value = text.trim() === "" ? Number.NaN : Number(text);
  if (!Number.isFinite(value)) return `${label}을(를) 숫자로 입력해 주세요.`;
  const actual = spec.unit === "percent" ? value / 100 : value;
  const unit = unitLabel(spec);
  if (spec.min !== null && actual < spec.min - 1e-9) return `${label}은(는) ${bound(spec, spec.min)}${unit} 이상이어야 합니다.`;
  if (spec.max !== null && actual > spec.max + 1e-9) return `${label}은(는) ${bound(spec, spec.max)}${unit} 이하여야 합니다.`;
  return null;
}

export function firstProblem(entries: ParamEntry[], inputs: Record<string, string>): string | null {
  for (const [name, spec] of entries) {
    const problem = paramProblem(name, spec, inputs[name] ?? "");
    if (problem) return problem;
  }
  return null;
}

/** 시작 요청의 `params`. 퍼센트는 비율로 바꾼다(20 → 0.2). */
export const paramsBody = (entries: ParamEntry[], inputs: Record<string, string>): Record<string, number> =>
  Object.fromEntries(
    entries.map(([name, spec]) => {
      const value = Number(inputs[name]);
      return [name, spec.unit === "percent" ? Number((value / 100).toFixed(8)) : value];
    }),
  );
