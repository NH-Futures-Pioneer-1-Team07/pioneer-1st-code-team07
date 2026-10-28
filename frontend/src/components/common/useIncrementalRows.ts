import { useEffect, useState } from "react";
import type { UIEvent } from "react";

/** 많은 줄을 한 번에 그리지 않고, 스크롤이 끝에 가까워질 때마다 `step`줄씩 더 보여 준다. */
export function useIncrementalRows(total: number, resetKey: string, step = 100) {
  const [count, setCount] = useState(step);

  useEffect(() => setCount(step), [resetKey, step]);

  const onScroll = (event: UIEvent<HTMLElement>) => {
    const box = event.currentTarget;
    if (box.scrollTop + box.clientHeight >= box.scrollHeight - 200) {
      setCount((current) => Math.min(total, current + step));
    }
  };

  return { count: Math.min(count, total), onScroll };
}
