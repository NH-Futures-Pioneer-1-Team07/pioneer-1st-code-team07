import styles from "./StrategySelect.module.css";

export interface StrategyItem {
  id: string;
  name: string;
  description: string;
}

export default function StrategySelect({
  id,
  items,
  selectedId,
  disabled,
  onChange,
}: {
  id: string;
  items: StrategyItem[];
  selectedId: string;
  disabled?: boolean;
  onChange: (id: string) => void;
}) {
  return (
    <fieldset className={styles.group} disabled={disabled}>
      <legend>전략 선택</legend>
      <div className={styles.list}>
        {items.map((item) => {
          const selected = item.id === selectedId;
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
