import { useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { inlineText, parseMarkdown } from "../../../data/markdown";
import type { Align, Block, Inline } from "../../../data/markdown";
import styles from "./MarkdownView.module.css";

function renderInline(items: Inline[]): ReactNode[] {
  return items.map((item, index) => {
    if (item.kind === "text") return item.text;
    if (item.kind === "bold") return <strong key={index}>{renderInline(item.children)}</strong>;
    if (item.kind === "code") return <code key={index}>{item.text}</code>;
    return <br key={index} />;
  });
}

const REQUEST_LANG = "sweep-request";

function CodeBlock({ lang, text }: { lang: string; text: string }) {
  const [copied, setCopied] = useState(false);
  const request = lang === REQUEST_LANG;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };
  return (
    <div className={styles.codeBlock}>
      {(request || lang) && (
        <div className={styles.codeHead}>
          <span>{request ? "다음 탐색 요청 (요청 파일로 저장해 python -m app.sweep run에 넘김)" : lang}</span>
          {request && (
            <button type="button" onClick={copy}>
              {copied ? "복사됨" : "복사"}
            </button>
          )}
        </div>
      )}
      <pre tabIndex={0}>
        <code>{text}</code>
      </pre>
    </div>
  );
}

const align = (value: Align) => ({ textAlign: value }) as CSSProperties;

function renderBlock(block: Block, index: number): ReactNode {
  switch (block.kind) {
    case "heading": {
      // 보고서 제목(#)은 상단에 따로 보여 주므로 본문에서는 ##부터 구역 제목으로 쓴다.
      if (block.level === 2) return <h3 key={index} className={styles.section}>{renderInline(block.children)}</h3>;
      if (block.level === 3) return <h4 key={index} className={styles.subsection}>{renderInline(block.children)}</h4>;
      return <h5 key={index} className={styles.minor}>{renderInline(block.children)}</h5>;
    }
    case "paragraph":
      return <p key={index} className={styles.paragraph}>{renderInline(block.children)}</p>;
    case "list": {
      const Tag = block.ordered ? "ol" : "ul";
      return (
        <Tag key={index} className={styles.list}>
          {block.items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInline(item)}</li>
          ))}
        </Tag>
      );
    }
    case "table":
      return (
        <div key={index} className={`table-wrap ${styles.tableWrap}`} style={{ "--table-height": "auto" } as CSSProperties}>
          <table className={`data-table ${styles.table}`}>
            <thead>
              <tr>
                {block.header.map((cell, cellIndex) => (
                  <th key={cellIndex} style={align(block.aligns[cellIndex] ?? "left")}>{renderInline(cell)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} style={align(block.aligns[cellIndex] ?? "left")}>{renderInline(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    case "code":
      return <CodeBlock key={index} lang={block.lang} text={block.text} />;
    case "quote":
      return <blockquote key={index} className={styles.quote}>{renderInline(block.children)}</blockquote>;
    case "rule":
      return <hr key={index} className={styles.rule} />;
  }
}

/** 보고서 본문. 첫 번째 `#` 제목이 `title`과 같으면 상단 제목과 겹치므로 뺀다. */
export default function MarkdownView({ text, title }: { text: string; title: string }) {
  const blocks = parseMarkdown(text);
  const first = blocks[0];
  const skipFirst = first?.kind === "heading" && first.level === 1 && inlineText(first.children) === title;
  return <div className={styles.markdown}>{(skipFirst ? blocks.slice(1) : blocks).map(renderBlock)}</div>;
}
