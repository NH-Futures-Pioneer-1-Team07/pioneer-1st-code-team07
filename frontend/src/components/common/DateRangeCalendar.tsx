import { useEffect, useId, useRef, useState } from "react";
import { dotted } from "../../data/format";
import Icon from "./Icon";
import styles from "./DateRangeCalendar.module.css";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

const pad = (value: number) => String(value).padStart(2, "0");
const toKey = (y: number, m: number, d: number) => `${y}-${pad(m)}-${pad(d)}`;

export default function DateRangeCalendar({
  start,
  end,
  min,
  max,
  sparse = {},
  onChange,
}: {
  start: string;
  end: string;
  min: string;
  max: string;
  /** 봉이 적은 날 → 그날의 봉 수. 붉게 표시하고 선택은 막지 않는다. */
  sparse?: Record<string, number>;
  onChange: (start: string, end: string) => void;
}) {
  const initial = start || min;
  const [view, setView] = useState({
    y: Number(initial.slice(0, 4)),
    m: Number(initial.slice(5, 7)),
  });
  const [picking, setPicking] = useState<"start" | "end">("start");
  const [hover, setHover] = useState("");
  const [open, setOpen] = useState(false);
  const bodyId = useId();
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (
        event.target instanceof Node &&
        !rootRef.current?.contains(event.target)
      )
        setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      setOpen(false);
      rootRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const firstDay = new Date(view.y, view.m - 1, 1).getDay();
  const lastDay = new Date(view.y, view.m, 0).getDate();
  const monthKey = (y: number, m: number) => y * 12 + m;
  const canPrev =
    monthKey(view.y, view.m) >
    monthKey(Number(min.slice(0, 4)), Number(min.slice(5, 7)));
  const canNext =
    monthKey(view.y, view.m) <
    monthKey(Number(max.slice(0, 4)), Number(max.slice(5, 7)));

  function moveMonth(step: number) {
    const index = view.y * 12 + (view.m - 1) + step;
    setView({ y: Math.floor(index / 12), m: (index % 12) + 1 });
  }

  function openAt(target: "start" | "end") {
    if (open && picking === target) {
      setOpen(false);
      return;
    }
    const focus = (target === "end" && end) || start || min;
    setView({ y: Number(focus.slice(0, 4)), m: Number(focus.slice(5, 7)) });
    setPicking(target);
    setOpen(true);
  }

  function pick(key: string) {
    if (picking === "end" && start && key >= start) {
      onChange(start, key);
      setPicking("start");
      setHover("");
      setOpen(false);
    } else {
      onChange(key, "");
      setPicking("end");
    }
  }

  const previewEnd = end || (picking === "end" && hover >= start ? hover : "");
  const cells = [
    ...Array.from({ length: firstDay }, (_, i) => <span key={`blank-${i}`} />),
    ...Array.from({ length: lastDay }, (_, i) => {
      const day = i + 1;
      const key = toKey(view.y, view.m, day);
      const disabled = key < min || key > max;
      const isStart = key === start;
      const isEnd = key === end;
      const isPreviewEnd = !end && key === previewEnd && key !== start;
      const inRange = Boolean(
        start && previewEnd && key > start && key < previewEnd,
      );
      const hasBand = Boolean(start && previewEnd && previewEnd > start);
      const classes = [
        styles.cell,
        inRange && styles.inRange,
        hasBand && isStart && styles.bandRight,
        hasBand && (isEnd || isPreviewEnd) && styles.bandLeft,
      ]
        .filter(Boolean)
        .join(" ");
      const dayClasses = [
        styles.day,
        (isStart || isEnd) && styles.selected,
        isPreviewEnd && styles.preview,
        sparse[key] !== undefined && styles.sparse,
      ]
        .filter(Boolean)
        .join(" ");
      return (
        <div key={key} className={classes}>
          <button
            type="button"
            className={dayClasses}
            disabled={disabled}
            aria-pressed={isStart || isEnd}
            aria-label={`${view.y}년 ${view.m}월 ${day}일${isStart ? " 시작일" : isEnd ? " 종료일" : ""}${sparse[key] !== undefined ? `, 봉이 적은 날 ${sparse[key]}개` : ""}`}
            title={sparse[key] !== undefined ? `봉이 적은 날 (${sparse[key]}개)` : undefined}
            onClick={() => pick(key)}
            onMouseEnter={() => setHover(key)}
            onFocus={() => setHover(key)}
          >
            {day}
          </button>
        </div>
      );
    }),
  ];

  return (
    <div
      ref={rootRef}
      className={styles.calendar}
      onMouseLeave={() => setHover("")}
    >
      <div className={styles.summary} aria-live="polite">
        <button
          type="button"
          className={open && picking === "start" ? styles.active : ""}
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => openAt("start")}
        >
          <span>시작일</span>
          <strong>{dotted(start) || "선택"}</strong>
        </button>
        <i aria-hidden="true" />
        <button
          type="button"
          className={open && picking === "end" ? styles.active : ""}
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => openAt("end")}
        >
          <span>종료일</span>
          <strong>{dotted(end) || "선택"}</strong>
        </button>
      </div>
      <div
        id={bodyId}
        className={`${styles.collapse} ${open ? styles.open : ""}`}
        inert={!open}
      >
        <div className={styles.body}>
          <div className={styles.nav}>
            <button
              type="button"
              aria-label="이전 달"
              disabled={!canPrev}
              onClick={() => moveMonth(-1)}
            >
              <Icon name="arrow" size={16} />
            </button>
            <strong>
              {view.y}년 {view.m}월
            </strong>
            <button
              type="button"
              aria-label="다음 달"
              disabled={!canNext}
              onClick={() => moveMonth(1)}
            >
              <Icon name="arrow" size={16} />
            </button>
          </div>
          <div className={styles.weekdays} aria-hidden="true">
            {WEEKDAYS.map((name) => (
              <span key={name}>{name}</span>
            ))}
          </div>
          <div className={styles.grid}>{cells}</div>
          {Object.keys(sparse).length > 0 && (
            <p className={styles.legend}>
              <i aria-hidden="true" /> 봉이 적은 날 · 전략이 판단을 못 해 보류가 많아요
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
