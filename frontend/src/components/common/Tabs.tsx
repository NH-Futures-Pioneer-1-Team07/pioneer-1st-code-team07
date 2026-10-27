import { useCallback, useLayoutEffect, useRef } from "react";
import type { KeyboardEvent, ReactNode } from "react";
import styles from "./Tabs.module.css";

export interface TabItem<T extends string> {
  id: T;
  label: string;
  count?: number;
}

export default function Tabs<T extends string>({
  idPrefix,
  label,
  tabs,
  value,
  onChange,
  trailing,
}: {
  idPrefix: string;
  label: string;
  tabs: readonly TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  trailing?: ReactNode;
}) {
  const listRef = useRef<HTMLDivElement>(null);
  const indicatorRef = useRef<HTMLSpanElement>(null);

  const placeIndicator = useCallback(() => {
    const selected = listRef.current?.querySelector<HTMLButtonElement>(
      '[aria-selected="true"]',
    );
    const indicator = indicatorRef.current;
    if (!selected || !indicator) return;
    indicator.style.width = `${selected.offsetWidth}px`;
    indicator.style.transform = `translateX(${selected.offsetLeft}px)`;
  }, []);

  useLayoutEffect(() => {
    placeIndicator();
    const list = listRef.current;
    if (!list) return;
    const observer = new ResizeObserver(placeIndicator);
    observer.observe(list);
    list
      .querySelectorAll("button")
      .forEach((button) => observer.observe(button));
    return () => observer.disconnect();
  }, [placeIndicator, tabs, value]);

  function move(event: KeyboardEvent<HTMLDivElement>) {
    const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    const index = tabs.findIndex((tab) => tab.id === value);
    const next =
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? tabs.length - 1
          : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) %
            tabs.length;
    onChange(tabs[next].id);
    listRef.current
      ?.querySelectorAll<HTMLButtonElement>("button")
      [next]?.focus();
  }

  return (
    <div className={styles.bar}>
      <div
        ref={listRef}
        className={styles.list}
        role="tablist"
        aria-label={label}
        onKeyDown={move}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`${idPrefix}-${tab.id}-tab`}
            type="button"
            role="tab"
            tabIndex={value === tab.id ? 0 : -1}
            aria-selected={value === tab.id}
            aria-controls={`${idPrefix}-${tab.id}-panel`}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
            {tab.count !== undefined && <span>{tab.count}</span>}
          </button>
        ))}
        <span
          ref={indicatorRef}
          className={styles.indicator}
          aria-hidden="true"
        />
      </div>
      {trailing && <div className={styles.trailing}>{trailing}</div>}
    </div>
  );
}
