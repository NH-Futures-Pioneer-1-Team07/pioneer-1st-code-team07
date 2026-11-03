import assert from "node:assert/strict";
import test from "node:test";
import { defaultInputs, editableParams, firstProblem, paramProblem, paramsBody } from "./paramView.ts";
import type { ParameterSpec } from "../apis/types.ts";

const rate: ParameterSpec = {
  default: 0.2, description: "손익 비율", editable: true, label: "익절·손절 기준", unit: "percent", min: 0.01, max: 1,
};
const plain: ParameterSpec = { default: 5, description: "수량", editable: false, label: null, unit: null, min: null, max: null };
const entries = editableParams({ profit_loss_rate: rate, quantity: plain, list: { ...plain, editable: true, default: [1, 2] } });

test("바꿀 수 있는 숫자 파라미터만 고른다", () => {
  assert.deepEqual(entries.map(([name]) => name), ["profit_loss_rate"]);
  assert.deepEqual(editableParams(undefined), []);
});

test("기본값은 퍼센트 단위로 입력칸에 채운다", () => {
  assert.deepEqual(defaultInputs(entries), { profit_loss_rate: "20" });
  assert.deepEqual(defaultInputs([["x", { ...plain, default: 0.07 * 100 }]]), { x: "7" });
});

test("입력값을 범위로 검증한다", () => {
  assert.equal(paramProblem("profit_loss_rate", rate, "20"), null);
  assert.equal(paramProblem("profit_loss_rate", rate, "1"), null);
  assert.equal(paramProblem("profit_loss_rate", rate, "100"), null);
  assert.match(paramProblem("profit_loss_rate", rate, "0") ?? "", /1% 이상/);
  assert.match(paramProblem("profit_loss_rate", rate, "101") ?? "", /100% 이하/);
  assert.match(paramProblem("profit_loss_rate", rate, "") ?? "", /숫자/);
  assert.match(paramProblem("profit_loss_rate", rate, "abc") ?? "", /숫자/);
  assert.equal(firstProblem(entries, { profit_loss_rate: "5" }), null);
  assert.match(firstProblem(entries, { profit_loss_rate: "500" }) ?? "", /익절·손절 기준/);
});

test("시작 요청에는 퍼센트를 비율로 바꿔 보낸다", () => {
  assert.deepEqual(paramsBody(entries, { profit_loss_rate: "20" }), { profit_loss_rate: 0.2 });
  assert.deepEqual(paramsBody(entries, { profit_loss_rate: "7.5" }), { profit_loss_rate: 0.075 });
  assert.deepEqual(paramsBody([["n", plain]], { n: "3" }), { n: 3 });
});
