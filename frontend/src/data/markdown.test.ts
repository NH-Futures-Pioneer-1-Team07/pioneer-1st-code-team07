import assert from "node:assert/strict";
import test from "node:test";
import { findCodeBlock, inlineText, parseInline, parseMarkdown } from "./markdown.ts";

test("굵게와 코드와 줄바꿈을 인라인 요소로 나눈다", () => {
  assert.deepEqual(parseInline("앞 **굵게** 중간 `코드` 뒤<br>다음"), [
    { kind: "text", text: "앞 " },
    { kind: "bold", children: [{ kind: "text", text: "굵게" }] },
    { kind: "text", text: " 중간 " },
    { kind: "code", text: "코드" },
    { kind: "text", text: " 뒤" },
    { kind: "break" },
    { kind: "text", text: "다음" },
  ]);
});

test("HTML 태그는 해석하지 않고 글자로 둔다", () => {
  assert.deepEqual(parseInline("<script>alert(1)</script>"), [{ kind: "text", text: "<script>alert(1)</script>" }]);
});

test("제목과 문단과 구분선을 나눈다", () => {
  const blocks = parseMarkdown("# 제목\n\n첫 줄\n이어지는 줄\n\n---\n\n#### 소제목");
  assert.equal(blocks.length, 4);
  assert.deepEqual(blocks[0], { kind: "heading", level: 1, children: [{ kind: "text", text: "제목" }] });
  assert.deepEqual(blocks[1], { kind: "paragraph", children: [{ kind: "text", text: "첫 줄 이어지는 줄" }] });
  assert.equal(blocks[2].kind, "rule");
  assert.equal(blocks[3].kind === "heading" && blocks[3].level, 4);
});

test("글머리 목록과 번호 목록과 이어지는 줄을 항목으로 묶는다", () => {
  const blocks = parseMarkdown("- 하나\n- 둘\n  이어짐\n\n1. 첫째\n2. 둘째");
  assert.equal(blocks[0].kind === "list" && blocks[0].ordered, false);
  assert.deepEqual(blocks[0].kind === "list" && blocks[0].items.map(inlineText), ["하나", "둘 이어짐"]);
  assert.equal(blocks[1].kind === "list" && blocks[1].ordered, true);
  assert.deepEqual(blocks[1].kind === "list" && blocks[1].items.map(inlineText), ["첫째", "둘째"]);
});

test("표의 머리글과 정렬과 행을 읽는다", () => {
  const blocks = parseMarkdown("| 이름 | 값 | 비율 |\n|---|---:|:---:|\n| a | 1,000 | **굵게** |\n| b | 2 | `x` |\n\n뒤 문단");
  assert.equal(blocks.length, 2);
  const table = blocks[0];
  assert.equal(table.kind, "table");
  if (table.kind !== "table") return;
  assert.deepEqual(table.header.map(inlineText), ["이름", "값", "비율"]);
  assert.deepEqual(table.aligns, ["left", "right", "center"]);
  assert.equal(table.rows.length, 2);
  assert.deepEqual(table.rows[0].map(inlineText), ["a", "1,000", "굵게"]);
});

test("표 셀 안의 이스케이프한 파이프는 칸을 나누지 않는다", () => {
  const table = parseMarkdown("| a | b |\n|---|---|\n| x \\| y | z |")[0];
  assert.equal(table.kind === "table" && inlineText(table.rows[0][0]), "x | y");
});

test("코드 블록은 언어와 본문을 그대로 담고 닫히지 않아도 끝까지 읽는다", () => {
  const blocks = parseMarkdown("```sweep-request\n{\n  \"a\": 1\n}\n```\n\n```\n닫히지 않음");
  assert.deepEqual(blocks[0], { kind: "code", lang: "sweep-request", text: "{\n  \"a\": 1\n}" });
  assert.deepEqual(blocks[1], { kind: "code", lang: "", text: "닫히지 않음" });
});

test("코드 블록 안의 마크다운은 해석하지 않는다", () => {
  const blocks = parseMarkdown("```\n# 제목 아님\n- 목록 아님\n```");
  assert.equal(blocks.length, 1);
  assert.equal(blocks[0].kind === "code" && blocks[0].text, "# 제목 아님\n- 목록 아님");
});

test("인용문을 한 블록으로 묶는다", () => {
  const blocks = parseMarkdown("> 첫째\n> 둘째");
  assert.equal(blocks[0].kind === "quote" && inlineText(blocks[0].children), "첫째 둘째");
});

test("지정한 언어의 첫 코드 블록 본문을 찾는다", () => {
  const blocks = parseMarkdown("```json\n1\n```\n\n```sweep-request\n2\n```");
  assert.equal(findCodeBlock(blocks, "sweep-request"), "2");
  assert.equal(findCodeBlock(blocks, "없음"), null);
});

test("빈 글은 블록이 없다", () => {
  assert.deepEqual(parseMarkdown(""), []);
  assert.deepEqual(parseMarkdown("\n\n  \n"), []);
});
