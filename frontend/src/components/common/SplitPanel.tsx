import type { ReactNode, Ref } from "react";
import Icon from "./Icon";
import styles from "./SplitPanel.module.css";

/**
 * 목록 옆에 상세 패널을 펼치는 레이아웃. 펼치면 목록과 상세가 반반으로 나뉜다.
 * 펼친 상태는 `data-open`으로 표시하므로, 목록 쪽 CSS가 `[data-open="true"]`로 컬럼 등을 바꿀 수 있다.
 */
export default function SplitPanel({
  open,
  innerRef,
  className = "",
  list,
  detail,
  detailLabelledBy,
}: {
  open: boolean;
  innerRef?: Ref<HTMLDivElement>;
  className?: string;
  list: ReactNode;
  detail: ReactNode;
  /** 상세 패널의 제목 요소 id */
  detailLabelledBy: string;
}) {
  return (
    <div ref={innerRef} className={`${styles.split} ${className}`} data-open={open}>
      {list}
      <section
        className={`panel ${styles.detail}`}
        aria-labelledby={detailLabelledBy}
        aria-hidden={!open}
        inert={!open}
      >
        <div className={styles.detailInner}>{detail}</div>
      </section>
    </div>
  );
}

export function PanelCloseButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" className={styles.close} aria-label={label} onClick={onClick}>
      <Icon name="close" size={18} />
    </button>
  );
}
