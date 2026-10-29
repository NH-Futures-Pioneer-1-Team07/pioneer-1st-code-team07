import test from "node:test";
import assert from "node:assert/strict";
import { dotted, formatMoney, formatNumber, pnlClass } from "./format.ts";

test("숫자와 금액을 천 단위로 끊어 보여 준다", () => {
  assert.equal(formatNumber(1234567), "1,234,567");
  assert.equal(formatMoney(1234.6), "1,235원");
});

test("날짜를 점으로 구분해 보여 주고 빈 값은 그대로 둔다", () => {
  assert.equal(dotted("2026-10-29"), "2026.10.29");
  assert.equal(dotted(""), "");
});

test("손익에 맞는 색상 클래스를 고른다", () => {
  assert.equal(pnlClass(100), "positive");
  assert.equal(pnlClass(-1), "negative");
  assert.equal(pnlClass(0), "");
  assert.equal(pnlClass(null), "");
  assert.equal(pnlClass(undefined), "");
});
