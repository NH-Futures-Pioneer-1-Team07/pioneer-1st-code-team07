import test from "node:test";
import assert from "node:assert/strict";
import { defaultRunStrategy, latestWeek, weekOf } from "./defaultStrategy.ts";

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

test("주차가 같거나 접두사가 없으면 id가 뒤선 항목을 고른다", () => {
  assert.equal(latestWeek([{ id: "x" }, { id: "y" }], id)?.id, "y");
  assert.equal(latestWeek([{ id: "week04_zf_zn_spread" }, { id: "week04_z3n_zn_spread" }], id)?.id, "week04_zf_zn_spread");
  assert.equal(latestWeek([{ id: "week03_a" }, { id: "week03_b" }], id)?.id, "week03_b");
  assert.equal(latestWeek([], id), undefined);
});

test("뒤 주차가 등록되어도 두 실행 화면의 기본 전략은 6주차 ZN이다", () => {
  const zn = { id: "week06_zn_intraday_average_entry" };
  assert.equal(defaultRunStrategy([{ id: "week07_example" }, zn]), zn);
});

test("6주차 ZN이 없으면 등록된 가장 최근 주차 전략을 고른다", () => {
  const latest = { id: "week05_kospi200_basis_zscore" };
  assert.equal(defaultRunStrategy([{ id: "week03_zn_treasury_futures" }, latest]), latest);
  assert.equal(defaultRunStrategy([]), undefined);
});
