/**
 * 검증 보고서에 쓰는 마크다운 문법만 화면 요소로 바꾸기 쉬운 구조로 변환한다.
 * 제목, 문단, 목록, 표, 코드 블록, 인용, 구분선과 굵게·코드·줄바꿈(`<br>`)을 다룬다.
 * HTML은 해석하지 않고 글자로 둔다.
 */

export type Inline =
  | { kind: "text"; text: string }
  | { kind: "bold"; children: Inline[] }
  | { kind: "code"; text: string }
  | { kind: "break" };

export type Align = "left" | "right" | "center";

export type Block =
  | { kind: "heading"; level: number; children: Inline[] }
  | { kind: "paragraph"; children: Inline[] }
  | { kind: "list"; ordered: boolean; items: Inline[][] }
  | { kind: "table"; header: Inline[][]; aligns: Align[]; rows: Inline[][][] }
  | { kind: "code"; lang: string; text: string }
  | { kind: "quote"; children: Inline[] }
  | { kind: "rule" };

const INLINE = /\*\*(.+?)\*\*|`([^`]+)`|<br\s*\/?>/;

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  let rest = text;
  while (rest) {
    const match = INLINE.exec(rest);
    if (!match) {
      out.push({ kind: "text", text: rest });
      break;
    }
    if (match.index > 0) out.push({ kind: "text", text: rest.slice(0, match.index) });
    if (match[1] !== undefined) out.push({ kind: "bold", children: parseInline(match[1]) });
    else if (match[2] !== undefined) out.push({ kind: "code", text: match[2] });
    else out.push({ kind: "break" });
    rest = rest.slice(match.index + match[0].length);
  }
  return out;
}

function splitRow(line: string): string[] {
  let body = line.trim();
  if (body.startsWith("|")) body = body.slice(1);
  if (body.endsWith("|") && !body.endsWith("\\|")) body = body.slice(0, -1);
  return body.split(/(?<!\\)\|/).map((cell) => cell.trim().replaceAll("\\|", "|"));
}

const SEPARATOR = /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/;

function alignOf(cell: string): Align {
  const left = cell.startsWith(":");
  const right = cell.endsWith(":");
  if (left && right) return "center";
  return right ? "right" : "left";
}

const isTableStart = (lines: string[], index: number) =>
  lines[index].includes("|") && index + 1 < lines.length && SEPARATOR.test(lines[index + 1]) && lines[index + 1].includes("-");

export function parseMarkdown(text: string): Block[] {
  const lines = text.replaceAll("\r\n", "\n").split("\n");
  const blocks: Block[] = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    const fence = /^```\s*(\S*)\s*$/.exec(line);
    if (fence) {
      const body: string[] = [];
      index += 1;
      while (index < lines.length && !/^```\s*$/.test(lines[index])) {
        body.push(lines[index]);
        index += 1;
      }
      index += 1; // 닫는 ```
      blocks.push({ kind: "code", lang: fence[1], text: body.join("\n") });
      continue;
    }
    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      blocks.push({ kind: "heading", level: heading[1].length, children: parseInline(heading[2].trim()) });
      index += 1;
      continue;
    }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) {
      blocks.push({ kind: "rule" });
      index += 1;
      continue;
    }
    if (isTableStart(lines, index)) {
      const header = splitRow(line).map(parseInline);
      const aligns = splitRow(lines[index + 1]).map(alignOf);
      const rows: Inline[][][] = [];
      index += 2;
      while (index < lines.length && lines[index].trim() && lines[index].includes("|")) {
        rows.push(splitRow(lines[index]).map(parseInline));
        index += 1;
      }
      blocks.push({ kind: "table", header, aligns, rows });
      continue;
    }
    const bullet = /^\s*[-*]\s+/;
    const numbered = /^\s*\d+[.)]\s+/;
    if (bullet.test(line) || numbered.test(line)) {
      const ordered = numbered.test(line);
      const marker = ordered ? numbered : bullet;
      const items: Inline[][] = [];
      while (index < lines.length && marker.test(lines[index])) {
        let item = lines[index].replace(marker, "");
        index += 1;
        // 들여쓴 이어지는 줄은 같은 항목으로 합친다.
        while (index < lines.length && /^\s{2,}\S/.test(lines[index]) && !bullet.test(lines[index]) && !numbered.test(lines[index])) {
          item += ` ${lines[index].trim()}`;
          index += 1;
        }
        items.push(parseInline(item.trim()));
      }
      blocks.push({ kind: "list", ordered, items });
      continue;
    }
    if (line.startsWith(">")) {
      const quoted: string[] = [];
      while (index < lines.length && lines[index].startsWith(">")) {
        quoted.push(lines[index].replace(/^>\s?/, ""));
        index += 1;
      }
      blocks.push({ kind: "quote", children: parseInline(quoted.join(" ").trim()) });
      continue;
    }
    const paragraph: string[] = [];
    while (index < lines.length && lines[index].trim() && !startsBlock(lines, index)) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    blocks.push({ kind: "paragraph", children: parseInline(paragraph.join(" ")) });
  }
  return blocks;
}

function startsBlock(lines: string[], index: number): boolean {
  const line = lines[index];
  return (
    /^```/.test(line) ||
    /^#{1,6}\s/.test(line) ||
    /^\s*[-*]\s+/.test(line) ||
    /^\s*\d+[.)]\s+/.test(line) ||
    line.startsWith(">") ||
    isTableStart(lines, index)
  );
}

/** 코드 블록 중 `lang`으로 표시한 첫 블록의 본문. 없으면 `null`. */
export function findCodeBlock(blocks: Block[], lang: string): string | null {
  for (const block of blocks) {
    if (block.kind === "code" && block.lang === lang) return block.text;
  }
  return null;
}

/** 인라인 요소를 글자만 남겨 합친다. */
export function inlineText(items: Inline[]): string {
  return items
    .map((item) => {
      if (item.kind === "text" || item.kind === "code") return item.text;
      if (item.kind === "bold") return inlineText(item.children);
      return " ";
    })
    .join("");
}
