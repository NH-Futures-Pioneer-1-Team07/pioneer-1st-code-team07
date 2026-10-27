import { strategies } from "../../data/fixtures";
import type { Strategy } from "../../data/fixtures";
import styles from "./StrategySelect.module.css";

export default function StrategySelect({
  id,
  strategy,
  disabled,
  onChange,
}: {
  id: string;
  strategy: Strategy;
  disabled?: boolean;
  onChange: (id: string) => void;
}) {
  return (
    <fieldset className={styles.group} disabled={disabled}>
      <legend>전략 선택</legend>
      <div className={styles.list}>
        {strategies.map((item) => {
          const selected = item.id === strategy.id;
          return (
            <label
              key={item.id}
              className={styles.card + (selected ? " " + styles.selected : "")}
            >
              <input
                type="radio"
                name={id}
                value={item.id}
                checked={selected}
                onChange={() => onChange(item.id)}
              />
              <span className={styles.head}>
                <span className={styles.led} aria-hidden="true" />
                <strong>{item.name}</strong>
              </span>
              {selected && (
                <span className={styles.detail}>
                  <span>{item.description}</span>
                </span>
              )}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
