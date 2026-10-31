import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchBacktestRun } from "../../../apis/backtest";
import type { BacktestRun, RunSummary } from "../../../apis/types";
import type { BacktestController } from "../useBacktestPage";
import {
  CORE_METRICS,
  MAX_COMPARE,
  METRICS,
  METRIC_GROUPS,
  RUN_COLORS,
  RUN_LETTERS,
  bestIndex,
  compareBlocker,
  curveRows,
  formatDelta,
  formatValue,
  paramRows,
} from "../../../data/compareView";
import type { CompareEntry, MetricDef } from "../../../data/compareView";
import { dotted, formatMoney, pnlClass } from "../../../data/format";
import { formatDateTime, instrumentLabel, runKey } from "../../../data/tradingView";
import styles from "./CompareSection.module.css";

/** 그래프로 그리는 수치. 나머지는 수치 카드로 그린다. */
const isChart = (def: MetricDef) => def.shape === "equity" || def.shape === "drawdown" || def.shape === "daily";
const dayLabel = (day: string) => day.slice(5).replace("-", ".");
const axisStyle = { fill: "var(--text-tertiary)", fontSize: 11 };
const tooltipStyle = {
  background: "rgb(23 26 32 / 94%)",
  border: "1px solid rgb(255 255 255 / 8%)",
  borderRadius: 10,
  fontSize: 12,
};

interface Slot {
  entry: CompareEntry;
  letter: string;
  color: string;
}

function RunTag({ slot }: { slot: Slot }) {
  return (
    <span className={styles.tag} style={{ background: slot.color }}>
      {slot.letter}
    </span>
  );
}

function ScalarCard({ def, slots }: { def: MetricDef; slots: Slot[] }) {
  const values = slots.map((slot) => def.value?.(slot.entry.result) ?? null);
  const best = bestIndex(values, def.better);
  const scale = Math.max(...values.map((value) => Math.abs(value ?? 0)), 1e-9);
  const base = values[0];
  return (
    <ul className={styles.bars}>
      {slots.map((slot, index) => {
        const value = values[index];
        return (
          <li key={slot.entry.key}>
            <RunTag slot={slot} />
            <div className={styles.track}>
              {value !== null && (
                <i style={{ width: `${(Math.abs(value) / scale) * 100}%`, background: slot.color }} />
              )}
            </div>
            <strong className={def.unit === "money" ? pnlClass(value) : undefined}>
              {value === null ? "—" : formatValue(def.unit, value)}
            </strong>
            <small className={styles.delta}>
              {index > 0 && value !== null && base !== null ? formatDelta(def.unit, value - base) : ""}
            </small>
            <span className={styles.best}>{best === index ? "최고" : ""}</span>
          </li>
        );
      })}
    </ul>
  );
}

function WinLossCard({ slots }: { slots: Slot[] }) {
  return (
    <ul className={styles.bars}>
      {slots.map((slot) => {
        const { win_count: win, loss_count: loss } = slot.entry.result;
        const total = win + loss || 1;
        return (
          <li key={slot.entry.key}>
            <RunTag slot={slot} />
            <div className={styles.track}>
              <i className={styles.win} style={{ width: `${(win / total) * 100}%` }} />
              <i className={styles.loss} style={{ width: `${(loss / total) * 100}%` }} />
            </div>
            <strong>
              <span className="positive">{win}승</span> <span className="negative">{loss}패</span>
            </strong>
          </li>
        );
      })}
    </ul>
  );
}

function CurveCard({ def, slots }: { def: MetricDef; slots: Slot[] }) {
  const shape = def.shape as "equity" | "drawdown" | "daily";
  const data = useMemo(() => curveRows(slots.map((slot) => slot.entry), shape), [slots, shape]);
  const tick = (value: number) =>
    shape === "daily" ? `${Math.round(value / 10000).toLocaleString("ko-KR")}만` : `${(value * 100).toFixed(1)}%`;
  const tip = (value: unknown) => {
    const number = Number(value);
    return shape === "daily" ? formatMoney(number) : `${(number * 100).toFixed(2)}%`;
  };
  const common = (
    <>
      <CartesianGrid vertical={false} stroke="var(--data-line)" strokeOpacity={0.6} />
      <XAxis dataKey="day" tickFormatter={dayLabel} tickLine={false} axisLine={false} tick={axisStyle} minTickGap={32} />
      <YAxis orientation="right" width={64} tickFormatter={tick} tickLine={false} axisLine={false} tick={axisStyle} />
      <ReferenceLine y={0} stroke="var(--text-tertiary)" strokeOpacity={0.5} strokeDasharray="2 5" />
      <Tooltip
        contentStyle={tooltipStyle}
        labelFormatter={(label) => dotted(String(label))}
        formatter={(value, name) => [tip(value), `${name}`]}
        cursor={shape === "daily" ? { fill: "rgb(255 255 255 / 4%)" } : { stroke: "var(--text-tertiary)", strokeOpacity: 0.4 }}
        isAnimationActive={false}
      />
    </>
  );
  return (
    <div className={styles.chart}>
      <ResponsiveContainer width="100%" height="100%">
        {shape === "daily" ? (
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
            {common}
            {slots.map((slot) => (
              <Bar key={slot.entry.key} name={slot.letter} dataKey={slot.entry.key} fill={slot.color} maxBarSize={10} isAnimationActive={false} />
            ))}
          </BarChart>
        ) : (
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
            {common}
            {slots.map((slot) => (
              <Line key={slot.entry.key} name={slot.letter} type="monotone" dataKey={slot.entry.key} stroke={slot.color} strokeWidth={1.75} dot={false} isAnimationActive={false} />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

function ParamCard({ slots }: { slots: Slot[] }) {
  const rows = paramRows(slots.map((slot) => slot.entry));
  return (
    <div className="table-wrap" style={{ height: "auto", maxHeight: 360 }}>
      <table className={`data-table ${styles.paramTable}`}>
        <thead>
          <tr>
            <th>설정</th>
            {slots.map((slot) => (
              <th key={slot.entry.key}>
                <RunTag slot={slot} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>전략</td>
            {slots.map((slot) => (
              <td key={slot.entry.key}>{slot.entry.strategyName}</td>
            ))}
          </tr>
          {rows.map((row) => (
            <tr key={row.name} className={row.differs ? styles.differs : undefined}>
              <td>{row.name}</td>
              {row.values.map((value, index) => (
                <td key={slots[index].entry.key}>{value ?? "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** 실행 이력 중 기준과 같은 조건의 이력을 골라 설정과 성과를 나란히 비교한다. */
export default function CompareSection({ ctl }: { ctl: BacktestController }) {
  const { formId, list } = ctl;
  const [keys, setKeys] = useState<string[]>([]);
  const [metricIds, setMetricIds] = useState<string[]>(CORE_METRICS);
  const [loaded, setLoaded] = useState<Record<string, BacktestRun>>({});
  const [failed, setFailed] = useState<string[]>([]);

  const candidates = list.filter((run) => run.status === "completed");
  const byKey = new Map(list.map((run) => [runKey(run), run]));
  const chosen = keys.flatMap((key) => byKey.get(key) ?? []);
  const base = chosen[0];

  // 완료된 이력은 바뀌지 않으므로 한 번 불러온 결과를 계속 쓴다.
  useEffect(() => {
    for (const run of chosen) {
      const key = runKey(run);
      if (loaded[key] || failed.includes(key)) continue;
      fetchBacktestRun(run)
        .then((data) => setLoaded((current) => ({ ...current, [key]: data })))
        .catch(() => setFailed((current) => [...current, key]));
    }
  }, [keys.join(","), list.length]);

  function toggleRun(run: RunSummary) {
    const key = runKey(run);
    setKeys((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : current.length < MAX_COMPARE
          ? [...current, key]
          : current,
    );
  }

  function toggleMetric(id: string) {
    setMetricIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  const slots: Slot[] = chosen.flatMap((run, index) => {
    const data = loaded[runKey(run)];
    if (!data?.result) return [];
    const entry: CompareEntry = {
      key: runKey(run),
      strategyId: run.strategy_id,
      strategyName: run.strategy_name,
      meta: data.meta,
      result: data.result,
    };
    return [{ entry, letter: RUN_LETTERS[index], color: RUN_COLORS[index] }];
  });
  const waiting = chosen.length > slots.length && chosen.some((run) => !failed.includes(runKey(run)));
  const comparing = slots.length >= 2;
  const shownMetrics = metricIds.map((id) => METRICS.find((metric) => metric.id === id)).filter((m): m is MetricDef => !!m);

  return (
    <section className={`panel ${styles.compare}`} aria-labelledby={`${formId}-compare-title`}>
      <div className="section-head">
        <div>
          <h2 id={`${formId}-compare-title`}>이력 비교</h2>
          <p>
            첫 번째로 고른 이력(A)과 종목·초기자금·기간이 같은 이력만 함께 고를 수 있습니다. 최대 {MAX_COMPARE}개.
          </p>
        </div>
        <span className="badge">
          {keys.length}/{MAX_COMPARE}
        </span>
      </div>

      {candidates.length === 0 ? (
        <p className="empty">비교할 수 있는 완료된 이력이 없습니다.</p>
      ) : (
        <div className="table-wrap" style={{ height: "auto", maxHeight: 280 }}>
          <table className={`data-table ${styles.pickTable}`}>
            <thead>
              <tr>
                <th>선택</th>
                <th>비교 가능</th>
                <th>실행 일시</th>
                <th>전략</th>
                <th>종목</th>
                <th>테스트 기간</th>
                <th>순손익</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((run) => {
                const key = runKey(run);
                const index = keys.indexOf(key);
                const picked = index >= 0;
                const blocker = picked ? null : compareBlocker(base, run);
                const full = !picked && keys.length >= MAX_COMPARE;
                const reason = blocker ?? (full ? `최대 ${MAX_COMPARE}개까지 선택할 수 있음` : null);
                return (
                  <tr key={key} className={reason ? styles.disabled : undefined}>
                    <td>
                      <label className={styles.check}>
                        <input
                          type="checkbox"
                          checked={picked}
                          disabled={reason !== null}
                          onChange={() => toggleRun(run)}
                          aria-label={`${formatDateTime(run.started_at)} ${run.strategy_name} 비교에 ${picked ? "제외" : "추가"}`}
                        />
                        {picked && (
                          <span className={styles.tag} style={{ background: RUN_COLORS[index] }}>
                            {RUN_LETTERS[index]}
                          </span>
                        )}
                      </label>
                    </td>
                    <td className={styles.reason}>{picked ? (index === 0 ? "기준" : "선택됨") : (reason ?? "가능")}</td>
                    <td>{formatDateTime(run.started_at)}</td>
                    <td>{run.strategy_name}</td>
                    <td>{instrumentLabel(run.instrument.name)}</td>
                    <td>{run.period ? `${dotted(run.period.start)} — ${dotted(run.period.end)}` : "—"}</td>
                    <td className={pnlClass(run.net_pnl)}>
                      {run.net_pnl === null ? "—" : `${run.net_pnl > 0 ? "+" : ""}${formatMoney(run.net_pnl)}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {keys.length > 0 && (
        <>
          <div className={styles.catalog}>
            <div className={styles.catalogHead}>
              <strong>비교할 수치</strong>
              <span>
                <button type="button" onClick={() => setMetricIds(CORE_METRICS)}>핵심 수치</button>
                <button type="button" onClick={() => setMetricIds(METRICS.map((metric) => metric.id))}>전체 선택</button>
                <button type="button" onClick={() => setMetricIds([])}>모두 해제</button>
              </span>
            </div>
            {METRIC_GROUPS.map((group) => (
              <div key={group} className={styles.group}>
                <span>{group}</span>
                <div>
                  {METRICS.filter((metric) => metric.group === group).map((metric) => (
                    <button
                      key={metric.id}
                      type="button"
                      className={metricIds.includes(metric.id) ? styles.chipOn : styles.chip}
                      aria-pressed={metricIds.includes(metric.id)}
                      onClick={() => toggleMetric(metric.id)}
                    >
                      {metric.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {!comparing && (
            <p className={styles.hint}>
              {waiting
                ? "결과를 불러오는 중…"
                : failed.length > 0
                  ? "일부 이력의 결과를 불러오지 못했습니다."
                  : "비교하려면 이력을 하나 더 선택하세요."}
            </p>
          )}

          {comparing && (
            <>
              <ul className={styles.legend}>
                {slots.map((slot) => (
                  <li key={slot.entry.key}>
                    <RunTag slot={slot} />
                    <span>
                      {slot.entry.strategyName} · {formatDateTime(slot.entry.meta.started_at)}
                    </span>
                  </li>
                ))}
              </ul>
              <div className={styles.board}>
                <article className={`${styles.card} ${styles.wide}`}>
                  <h3>설정값</h3>
                  <ParamCard slots={slots} />
                </article>
                {[...shownMetrics.filter((def) => !isChart(def)), ...shownMetrics.filter(isChart)].map((def) => (
                  <article key={def.id} className={`${styles.card} ${isChart(def) ? styles.wide : ""}`}>
                    <h3>{def.label}</h3>
                    {def.shape === "scalar" && <ScalarCard def={def} slots={slots} />}
                    {def.shape === "winloss" && <WinLossCard slots={slots} />}
                    {isChart(def) && <CurveCard def={def} slots={slots} />}
                  </article>
                ))}
              </div>
              {shownMetrics.length === 0 && <p className={styles.hint}>비교할 수치를 선택하세요.</p>}
            </>
          )}
        </>
      )}
    </section>
  );
}
