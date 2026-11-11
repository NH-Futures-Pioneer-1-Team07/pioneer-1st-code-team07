import test from "node:test";
import assert from "node:assert/strict";
import { latestWeek, weekOf } from "./defaultStrategy.ts";

const id = (item: { id: string }) => item.id;

test("전략 id에서 주차를 읽는다", () => {
  assert.equal(weekOf("week04_zf_zn_spread"), 4);
  assert.equal(weekOf("week10_x"), 10);
  assert.equal(weekOf("sample"), 0);
});

test("가장 최근 주차 전략을 고른다", () => {
  const items = [{ id: "week02_a" }, { id: "week04_b" }, { id: "week03_c" }];
  assert.equal(latestWeek(items, id)?.id, "week04_b");
});

test("주차가 같거나 접두사가 없으면 id가 앞선 항목을 고른다", () => {
  assert.equal(latestWeek([{ id: "y" }, { id: "x" }], id)?.id, "x");
  assert.equal(latestWeek([{ id: "week04_zf_zn_spread" }, { id: "week04_z3n_zn_spread" }], id)?.id, "week04_z3n_zn_spread");
  assert.equal(latestWeek([{ id: "week03_a" }, { id: "week03_b" }], id)?.id, "week03_a");
  assert.equal(latestWeek([], id), undefined);
});
