import { useEffect, useId, useState } from "react";
import type { FormEvent } from "react";
import {
  fetchAssumptions,
  fetchBacktestRun,
  fetchCurrentBacktest,
  fetchRange,
  startBacktest,
} from "../../apis/backtest";
import { errorMessage } from "../../apis/client";
import { usePolling } from "../../apis/polling";
import { fetchRuns, fetchStrategies } from "../../apis/trading";
import type { RunRef, RunSummary } from "../../apis/types";
import {
  defaultPeriod,
  percentText,
  progressLabel,
  progressPercent,
  returnText,
  statusLabel,
  validateInput,
} from "../../data/backtestView";
import { formatMoney, formatNumber } from "../../data/format";
import { formatDateTime, instrumentLabel, signed } from "../../data/tradingView";
import StrategySelect from "../../components/common/StrategySelect";
import Icon from "../../components/common/Icon";
import DateRangeCalendar from "../../components/common/DateRangeCalendar";
import EquityChart from "./components/EquityChart";
import RecordDetail from "./components/RecordDetail";
import styles from "./BacktestPage.module.css";

const runKey = (run: RunRef) => `${run.strategy_id}/${run.run_id}`;
const dotted = (day: string) => day.replaceAll("-", ".");
const pnlClass = (value: number) => (value > 0 ? "positive" : value < 0 ? "negative" : "");

export default function BacktestPage() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [capital, setCapital] = useState("50000000");
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const [active, setActive] = useState<RunRef | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const formId = useId();

  const strategies = usePolling(fetchStrategies, 60000);
  const items = strategies.data ?? [];
  const strategy = items.find((item) => item.id === selectedStrategy) ?? items[0];
  const strategyId = strategy?.id ?? null;

  const range = usePolling(() => fetchRange(strategyId as string), 600000, [strategyId], !!strategyId);
  const assumptions = usePolling(fetchAssumptions, 600000);
  const runs = usePolling(() => fetchRuns("backtest"), 10000);
  const list = runs.data ?? [];

  // 화면을 다시 열었을 때 실행 중인 백테스트를 이어서 본다.
  useEffect(() => {
    fetchCurrentBacktest()
      .then((run) => run && setActive(run))
      .catch(() => undefined);
  }, []);

  const live = usePolling(
    () => fetchBacktestRun(active as RunRef),
    1000,
    [active ? runKey(active) : null],
    !!active,
  );
  const liveMeta = live.data?.meta;
  useEffect(() => {
    if (!active || !liveMeta || liveMeta.status === "running") return;
    setSelectedKey(runKey(active));
    setActive(null);
    runs.reload();
    setAnnouncement(
      liveMeta.status === "completed"
        ? "백테스트가 완료됐습니다. 결과와 실행 이력을 확인하세요."
        : "백테스트가 오류로 끝났습니다.",
    );
  }, [liveMeta?.status]);

  const selected: RunSummary | undefined =
    list.find((run) => runKey(run) === selectedKey) ??
    list.find((run) => run.status !== "running");
  const report = usePolling(
    () => fetchBacktestRun(selected as RunRef),
    600000,
    [selected ? `${runKey(selected)}/${selected.status}` : null],
    !!selected,
  );
  const reportMeta = report.data?.meta;
  const result = report.data?.result ?? null;

  const busy = starting || !!active;
  const available = range.data?.start && range.data.end ? range.data : null;
  useEffect(() => {
    const period = defaultPeriod(available);
    if (period && !startDate && !endDate) {
      setStartDate(period.start);
      setEndDate(period.end);
    }
  }, [available, startDate, endDate]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = validateInput(startDate, endDate, capital, available);
    if (problem || !strategyId) {
      setError(problem || "전략을 선택해 주세요.");
      return;
    }
    setError("");
    setStarting(true);
    try {
      const run = await startBacktest({
        strategy_id: strategyId,
        start_date: startDate,
        end_date: endDate,
        initial_capital: Number(capital),
      });
      setActive(run);
      setAnnouncement("백테스트를 시작했습니다. 과거 데이터를 준비합니다.");
      runs.reload();
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setStarting(false);
    }
  }

  const percent = progressPercent(liveMeta?.progress, liveMeta?.status ?? "running");

  return (
    <div className={styles.page}>
      <span className={styles.screenReader} role="status">
        {announcement}
      </span>
      <div className={styles.pageHeading}>
        <div>
          <h1>백테스트</h1>
        </div>
      </div>
      <div className={styles.columns}>
        <section
          className={`panel ${styles.configuration}`}
          aria-labelledby={`${formId}-title`}
        >
          <div className="section-head">
            <h2 id={`${formId}-title`}>테스트 조건</h2>
          </div>
          <div className={styles.strategyField}>
            {strategies.error && (
              <p className="empty">전략을 불러오지 못했습니다. {strategies.error}</p>
            )}
            {strategy && (
              <StrategySelect
                id={`${formId}-strategy`}
                items={items}
                selectedId={strategy.id}
                disabled={busy}
                onChange={(id) => {
                  setSelectedStrategy(id);
                  setStartDate("");
                  setEndDate("");
                  setError("");
                }}
              />
            )}
          </div>
          <form
            onSubmit={submit}
            noValidate
            aria-describedby={error ? `${formId}-error` : undefined}
          >
            <fieldset className={styles.fields} disabled={busy}>
              <div className={styles.instrument}>
                <span className={styles.instrumentLabel}>테스트 종목</span>
                <div className={styles.instrumentCard}>
                  <div>
                    <strong>
                      {range.data ? instrumentLabel(range.data.instrument.name) : "—"}
                    </strong>
                  </div>
                  <small>
                    {range.data?.instrument.code ?? "—"}
                    {range.data?.last_trading_day
                      ? ` · 만기 ${range.data.last_trading_day}`
                      : ""}
                  </small>
                </div>
              </div>
              {available ? (
                <DateRangeCalendar
                  key={strategyId}
                  start={startDate}
                  end={endDate}
                  min={available.start as string}
                  max={available.end as string}
                  onChange={(start, end) => {
                    setStartDate(start);
                    setEndDate(end);
                    setError("");
                  }}
                />
              ) : (
                <p className="empty">
                  {range.error
                    ? `테스트 가능 기간을 확인하지 못했습니다. ${range.error}`
                    : range.data
                      ? "테스트할 수 있는 데이터가 없습니다."
                      : "테스트 가능 기간을 확인하는 중…"}
                </p>
              )}
              {available && (
                <p className={styles.availablePeriod}>
                  테스트 가능 기간{" "}
                  <strong>
                    {available.start} — {available.end}
                  </strong>
                </p>
              )}
              <label className="field" htmlFor={`${formId}-capital`}>
                <span>초기자금</span>
                <div className={styles.moneyInput}>
                  <input
                    id={`${formId}-capital`}
                    type="number"
                    inputMode="numeric"
                    min="1000000"
                    max="10000000000"
                    step="1"
                    value={capital}
                    onChange={(event) => setCapital(event.target.value)}
                    aria-describedby={`${formId}-capital-help`}
                  />
                  <span>원</span>
                </div>
              </label>
              <span
                className={styles.capitalHelp}
                id={`${formId}-capital-help`}
              >
                100만 원부터 100억 원까지 입력할 수 있습니다.
              </span>
            </fieldset>
            <div className={styles.assumptions}>
              <h3>비용 및 체결 가정</h3>
              {assumptions.data ? (
                <dl>
                  <div>
                    <dt>수수료</dt>
                    <dd>체결대금의 {percentText(assumptions.data.fee.rate)}</dd>
                  </div>
                  <div>
                    <dt>슬리피지</dt>
                    <dd>
                      {assumptions.data.slippage.ticks}틱 · {assumptions.data.slippage.direction}
                    </dd>
                  </div>
                  <div>
                    <dt>체결</dt>
                    <dd>{assumptions.data.fill.on_bar}</dd>
                  </div>
                  <div>
                    <dt>증거금</dt>
                    <dd>{assumptions.data.margin}</dd>
                  </div>
                </dl>
              ) : (
                <p className="empty">
                  {assumptions.error
                    ? `가정을 불러오지 못했습니다. ${assumptions.error}`
                    : "불러오는 중…"}
                </p>
              )}
            </div>
            {error && (
              <p className={styles.error} id={`${formId}-error`} role="alert">
                {error}
              </p>
            )}
            <button
              className={`button primary ${styles.runButton}`}
              type="submit"
              disabled={busy || !available}
            >
              <Icon name={busy ? "spinner" : "play"} size={15} spin={busy} />
              {busy ? "백테스트 실행 중" : "백테스트 실행"}
            </button>
          </form>
        </section>

        <section
          className={`panel ${styles.result}`}
          aria-labelledby={`${formId}-result-title`}
          aria-busy={busy}
        >
          <div className="section-head">
            <div>
              <h2 id={`${formId}-result-title`}>백테스트 결과</h2>
            </div>
          </div>
          {active && (
            <div className={styles.progressPanel} role="status">
              <div>
                <strong>{progressLabel(liveMeta?.progress)}</strong>
                <span>{percent}%</span>
              </div>
              <progress max="100" value={percent} aria-label="백테스트 진행률" />
              <p>
                {liveMeta
                  ? `${liveMeta.strategy_name} · ${instrumentLabel(liveMeta.instrument.name)} · ${dotted(liveMeta.period.start)} — ${dotted(liveMeta.period.end)}`
                  : "실행 정보를 불러오는 중…"}
              </p>
              {live.error && <p>{live.error}</p>}
            </div>
          )}
          {!active && reportMeta && (
            <div
              className={`${styles.progressPanel} ${reportMeta.status === "completed" ? styles.done : styles.idle}`}
              role="status"
            >
              <div>
                <strong className={styles.doneTitle}>
                  {reportMeta.status === "completed" && <Icon name="check" size={16} />}
                  {reportMeta.status === "completed"
                    ? "백테스트가 완료됐어요"
                    : `백테스트가 ${statusLabel(reportMeta.status)}로 끝났어요`}
                </strong>
                <span className={styles.doneSide}>
                  {reportMeta.status === "completed" ? "100%" : statusLabel(reportMeta.status)}
                </span>
              </div>
              <progress
                max="100"
                value={reportMeta.status === "completed" ? 100 : 0}
                aria-label="백테스트 진행률"
              />
              <p>
                {formatDateTime(reportMeta.started_at)} · {reportMeta.strategy_name} ·{" "}
                {instrumentLabel(reportMeta.instrument.name)} ·{" "}
                {dotted(reportMeta.period.start)} — {dotted(reportMeta.period.end)}
              </p>
            </div>
          )}
          {!active && !reportMeta && (
            <div
              className={`${styles.progressPanel} ${styles.idle}`}
              role="status"
            >
              <div>
                <strong>
                  {report.error ? "결과를 불러오지 못했어요" : "백테스트 실행 전이에요"}
                </strong>
                <span>0%</span>
              </div>
              <progress max="100" value={0} aria-label="백테스트 진행률" />
              <p>
                {report.error ??
                  `${strategy?.name ?? "전략 선택"} · ${startDate ? dotted(startDate) : "시작일 선택"} — ${endDate ? dotted(endDate) : "종료일 선택"}`}
              </p>
            </div>
          )}
          {reportMeta && (
            <>
              <div className={styles.reportHeading}>
                <div>
                  <strong>{reportMeta.strategy_name}</strong>
                  <p>
                    {instrumentLabel(reportMeta.instrument.name)} ·{" "}
                    {dotted(reportMeta.period.start)} — {dotted(reportMeta.period.end)}
                  </p>
                </div>
              </div>
              <div className={styles.performanceCards}>
                <div>
                  <span>초기자금</span>
                  <strong>{formatMoney(reportMeta.initial_capital)}</strong>
                </div>
                <div>
                  <span>최종자산</span>
                  <strong>{result ? formatMoney(result.final_equity) : "—"}</strong>
                </div>
                <div>
                  <span>
                    순손익 <small>비용 반영</small>
                  </span>
                  <strong className={result ? pnlClass(result.net_pnl) : ""}>
                    {result ? signed(result.net_pnl, formatMoney) : "—"}
                  </strong>
                  {result && (
                    <small className={pnlClass(result.net_pnl)}>
                      {returnText(result.return_rate)}
                    </small>
                  )}
                </div>
              </div>
              <div className={styles.chartHeading}>
                <h3>자산 변화</h3>
                <span>
                  <i /> 하루마다 한 점
                </span>
              </div>
              <EquityChart id={reportMeta.run_id} result={result} />
              <div className={styles.resultFooter}>
                <span>
                  수수료 합계 <strong>{result ? formatMoney(result.fee) : "—"}</strong>
                </span>
                <span>
                  {result
                    ? `거래 ${result.trade_count}건 (승 ${result.win_count} · 패 ${result.loss_count}) · 최대 낙폭 ${formatMoney(result.max_drawdown)} (${(result.max_drawdown_rate * 100).toFixed(2)}%)`
                    : "결과가 없습니다. 상세 기록에서 원인을 확인하세요."}
                </span>
              </div>
            </>
          )}
        </section>
      </div>

      <div className={`${styles.split} ${detailOpen ? styles.splitOpen : ""}`}>
        <section
          className={`panel ${styles.history}`}
          aria-labelledby={`${formId}-history-title`}
        >
          <div className="section-head">
            <div>
              <h2 id={`${formId}-history-title`}>실행 이력</h2>
            </div>
            <span className="badge">{list.length}</span>
          </div>
          {runs.error && <p className="empty">이력을 불러오지 못했습니다. {runs.error}</p>}
          {!runs.error && runs.data === null && <p className="empty">불러오는 중…</p>}
          {runs.data !== null && list.length === 0 && (
            <p className="empty">백테스트 이력이 없습니다.</p>
          )}
          {list.length > 0 && (
            <div className="table-wrap">
              <table className={`data-table ${styles.historyTable}`}>
                <thead>
                  <tr>
                    <th>실행 일시</th>
                    <th>전략</th>
                    <th>종목</th>
                    <th>테스트 기간</th>
                    <th>초기자금</th>
                    <th>순손익</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((run) => {
                    const chosen = selected !== undefined && runKey(selected) === runKey(run);
                    return (
                      <tr
                        key={runKey(run)}
                        className={`${styles.historyRow} ${chosen ? styles.selectedRow : ""}`}
                        onClick={() => {
                          setSelectedKey(runKey(run));
                          setDetailOpen(true);
                        }}
                      >
                        <td>
                          <button
                            type="button"
                            className={styles.historyButton}
                            aria-pressed={chosen}
                            aria-label={`${formatDateTime(run.started_at)} 실행 상세 보기`}
                          >
                            {formatDateTime(run.started_at)}
                          </button>
                        </td>
                        <td>
                          <strong>{run.strategy_name}</strong>
                        </td>
                        <td>{instrumentLabel(run.instrument.name)}</td>
                        <td>
                          {run.period
                            ? `${dotted(run.period.start)} — ${dotted(run.period.end)}`
                            : "—"}
                        </td>
                        <td>
                          {run.initial_capital === undefined
                            ? "—"
                            : formatMoney(run.initial_capital)}
                        </td>
                        <td className={run.net_pnl === null ? "" : pnlClass(run.net_pnl)}>
                          {run.net_pnl === null ? "—" : signed(run.net_pnl, formatMoney)}
                        </td>
                        <td>
                          <span
                            className={run.status === "completed" ? styles.complete : undefined}
                          >
                            {statusLabel(run.status)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section
          className={`panel ${styles.detail}`}
          aria-labelledby={`${formId}-detail-title`}
          aria-hidden={!detailOpen}
          inert={!detailOpen}
        >
          <div className={styles.detailInner}>
            <div className="section-head">
              <div>
                <span className="eyebrow">
                  {reportMeta ? formatDateTime(reportMeta.started_at) : ""}
                </span>
                <h2 id={`${formId}-detail-title`}>실행 상세 기록</h2>
              </div>
              <div className={styles.detailHead}>
                <button
                  type="button"
                  className={styles.detailClose}
                  aria-label="실행 상세 기록 닫기"
                  onClick={() => setDetailOpen(false)}
                >
                  <Icon name="close" size={18} />
                </button>
              </div>
            </div>
            {reportMeta && (
              <>
                <dl className={styles.snapshot}>
                  <div>
                    <dt>테스트 기간</dt>
                    <dd>
                      {dotted(reportMeta.period.start)} — {dotted(reportMeta.period.end)}
                    </dd>
                  </div>
                  <div>
                    <dt>초기자금</dt>
                    <dd>{formatMoney(reportMeta.initial_capital)}</dd>
                  </div>
                  <div>
                    <dt>비용</dt>
                    <dd>
                      체결대금의 {percentText(reportMeta.assumptions.fee.rate)} · 슬리피지{" "}
                      {reportMeta.assumptions.slippage.ticks}틱
                      {reportMeta.assumptions.slippage.tick_size !== null &&
                        `(${formatNumber(reportMeta.assumptions.slippage.tick_size)})`}
                    </dd>
                  </div>
                  <div>
                    <dt>체결 기준</dt>
                    <dd>{reportMeta.assumptions.fill.on_bar}</dd>
                  </div>
                </dl>
                <RecordDetail meta={reportMeta} />
                <p className={styles.endNotice}>
                  <span aria-hidden="true">ⓘ</span>{" "}
                  <strong>백테스트 종료 청산</strong>은 기간이 끝났을 때 남은 보유분을
                  마지막 봉 종가에서 정리한 체결입니다. 수수료와 슬리피지는 체결가에
                  반영돼 있습니다.
                </p>
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
