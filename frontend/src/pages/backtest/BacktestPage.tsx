import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  formatMoney,
  formatNumber,
  instrumentTitle,
  strategies,
  strategyById,
  supportedInstruments,
} from "../../data/fixtures";
import { runTimestamp, sampleRecord } from "../../data/backtest";
import type { TestRecord } from "../../data/backtest";
import StrategySelect from "../../components/common/StrategySelect";
import Icon from "../../components/common/Icon";
import DateRangeCalendar from "../../components/common/DateRangeCalendar";
import Tabs from "../../components/common/Tabs";
import EquityChart from "./components/EquityChart";
import RecordDetail from "./components/RecordDetail";
import type { DetailTab } from "./components/RecordDetail";
import styles from "./BacktestPage.module.css";

type Phase = "idle" | "preparing" | "calculating";

export default function BacktestPage() {
  const [strategyId, setStrategyId] = useState(strategies[0].id);
  const strategy = strategyById(strategyId);
  const available = supportedInstruments(strategy);
  const instrument = available[0];
  const [startDate, setStartDate] = useState("2026-10-01");
  const [endDate, setEndDate] = useState("2026-10-27");
  const [capital, setCapital] = useState("50000000");
  const [error, setError] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [pending, setPending] = useState<TestRecord | null>(null);
  const [completed, setCompleted] = useState<TestRecord | null>(null);
  const [records, setRecords] = useState<TestRecord[]>(() => [
    sampleRecord(
      "sample-001",
      "2026.10.27 09:50",
      strategy,
      instrument,
      "2026-10-01",
      "2026-10-27",
      50_000_000,
    ),
    sampleRecord(
      "sample-000",
      "2026.10.26 17:40",
      strategy,
      instrument,
      "2026-09-01",
      "2026-09-30",
      30_000_000,
    ),
  ]);
  const [selectedId, setSelectedId] = useState("sample-001");
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailTab, setDetailTab] = useState<DetailTab>("decisions");
  const [announcement, setAnnouncement] = useState("");
  const runCounter = useRef(2);
  const formId = useId();
  const selected =
    records.find((record) => record.id === selectedId) ?? records[0];
  const busy = phase !== "idle";
  const progress =
    phase === "preparing" ? 30 : phase === "calculating" ? 72 : 100;

  useEffect(() => {
    if (!pending || phase === "idle") return;
    const timeout = window.setTimeout(
      () => {
        if (phase === "preparing") {
          setPhase("calculating");
          setAnnouncement(
            "샘플 데이터 준비를 마쳤습니다. 백테스트 계산 화면을 시연합니다.",
          );
        } else {
          setRecords((previous) => [pending, ...previous]);
          setSelectedId(pending.id);
          setCompleted(pending);
          setPending(null);
          setPhase("idle");
          setDetailTab("decisions");
          setAnnouncement(
            `${pending.title} 실행이 완료됐습니다. 결과와 실행 이력을 확인하세요.`,
          );
        }
      },
      phase === "preparing" ? 1100 : 1700,
    );
    return () => window.clearTimeout(timeout);
  }, [pending, phase]);

  function showRecord(record: TestRecord) {
    setSelectedId(record.id);
    setDetailOpen(true);
    setDetailTab("decisions");
    setAnnouncement(`${record.title}의 조건과 상세 기록을 표시합니다.`);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amount = Number(capital);
    const lastDate =
      instrument.dataEnd < instrument.expiry
        ? instrument.dataEnd
        : instrument.expiry;
    if (!available.length) {
      setError(
        "선택한 전략이 지원하는 샘플 종목이 없습니다. 다른 전략을 선택해 주세요.",
      );
      return;
    }
    if (!startDate || !endDate || startDate > endDate) {
      setError(
        "시작일과 종료일을 확인해 주세요. 시작일은 종료일보다 늦을 수 없습니다.",
      );
      return;
    }
    if (startDate < instrument.dataStart || endDate > lastDate) {
      setError(
        `테스트 기간은 데이터가 있는 ${instrument.dataStart}부터 ${lastDate}까지 선택해 주세요.`,
      );
      return;
    }
    if (
      !Number.isSafeInteger(amount) ||
      amount < 1_000_000 ||
      amount > 10_000_000_000
    ) {
      setError(
        "초기자금은 1,000,000원부터 10,000,000,000원까지 정수로 입력해 주세요.",
      );
      return;
    }
    const id = `demo-${runCounter.current++}`;
    setCompleted(null);
    setPending(
      sampleRecord(
        id,
        runTimestamp(),
        strategy,
        instrument,
        startDate,
        endDate,
        amount,
      ),
    );
    setPhase("preparing");
    setError("");
    setAnnouncement("백테스트 시연을 시작합니다. 과거 데이터 준비 화면입니다.");
  }

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
            <StrategySelect
              id={`${formId}-strategy`}
              items={strategies}
              selectedId={strategy.id}
              disabled={busy}
              onChange={setStrategyId}
            />
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
                    <strong>{instrument.name}</strong>
                    <span className="badge">{instrument.contract}</span>
                  </div>
                  <small>
                    {instrument.code} · 만기 {instrument.expiry}
                  </small>
                </div>
              </div>
              <DateRangeCalendar
                start={startDate}
                end={endDate}
                min={instrument.dataStart}
                max={
                  instrument.dataEnd < instrument.expiry
                    ? instrument.dataEnd
                    : instrument.expiry
                }
                onChange={(start, end) => {
                  setStartDate(start);
                  setEndDate(end);
                  setError("");
                }}
              />
              <p className={styles.availablePeriod}>
                테스트 가능 기간{" "}
                <strong>
                  {instrument.dataStart} —{" "}
                  {instrument.dataEnd < instrument.expiry
                    ? instrument.dataEnd
                    : instrument.expiry}
                </strong>
              </p>
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
              <dl>
                <div>
                  <dt>수수료</dt>
                  <dd>편도 2,500원 / 계약</dd>
                </div>
              </dl>
            </div>
            {error && (
              <p className={styles.error} id={`${formId}-error`} role="alert">
                {error}
              </p>
            )}
            <button
              className={`button primary ${styles.runButton}`}
              type="submit"
              disabled={busy || !available.length}
            >
              <Icon name={busy ? "spinner" : "play"} size={15} spin={busy} />
              {busy ? "백테스트 시연 중" : "백테스트 실행"}
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
          {busy && pending && (
            <div className={styles.progressPanel} role="status">
              <div>
                <strong>
                  {phase === "preparing"
                    ? "과거 데이터를 준비하고 있어요"
                    : "백테스트 계산 화면을 시연하고 있어요"}
                </strong>
                <span>{progress}%</span>
              </div>
              <progress
                max="100"
                value={progress}
                aria-label="백테스트 시연 진행률"
              />
              <p>
                {pending.strategyName} · {instrumentTitle(pending.instrument)} ·{" "}
                {pending.startDate} — {pending.endDate}
              </p>
            </div>
          )}
          {!busy && completed && (
            <div
              className={`${styles.progressPanel} ${styles.done}`}
              role="status"
            >
              <div>
                <strong className={styles.doneTitle}>
                  <Icon name="check" size={16} />
                  백테스트가 완료됐어요
                </strong>
                <span className={styles.doneSide}>100%</span>
              </div>
              <progress
                max="100"
                value={100}
                aria-label="백테스트 시연 진행률"
              />
              <p>
                {completed.title} · {completed.strategyName} ·{" "}
                {instrumentTitle(completed.instrument)} · {completed.startDate}{" "}
                — {completed.endDate}
              </p>
            </div>
          )}
          {!busy && !completed && (
            <div
              className={`${styles.progressPanel} ${styles.idle}`}
              role="status"
            >
              <div>
                <strong>백테스트 실행 전이에요</strong>
                <span>0%</span>
              </div>
              <progress max="100" value={0} aria-label="백테스트 시연 진행률" />
              <p>
                {strategy.name} · {instrumentTitle(instrument)} ·{" "}
                {startDate || "시작일 선택"} — {endDate || "종료일 선택"}
              </p>
            </div>
          )}
          <div className={styles.reportHeading}>
            <div>
              <strong>{selected.strategyName}</strong>
              <p>
                {instrumentTitle(selected.instrument)} · {selected.startDate} —{" "}
                {selected.endDate}
              </p>
            </div>
          </div>
          <div className={styles.performanceCards}>
            <div>
              <span>초기자금</span>
              <strong>{formatMoney(selected.capital)}</strong>
            </div>
            <div>
              <span>최종자산</span>
              <strong>{formatMoney(selected.capital + selected.profit)}</strong>
            </div>
            <div>
              <span>
                순손익 <small>비용 반영</small>
              </span>
              <strong className="positive">
                +{formatMoney(selected.profit)}
              </strong>
              <small className="positive">
                +{((selected.profit / selected.capital) * 100).toFixed(2)}%
              </small>
            </div>
          </div>
          <div className={styles.chartHeading}>
            <h3>자산 변화</h3>
            <span>
              <i /> 선택한 실행의 샘플 자산
            </span>
          </div>
          <EquityChart record={selected} />
          <div className={styles.resultFooter}>
            <span>
              수수료 합계 <strong>{formatMoney(selected.cost)}</strong>
            </span>
            <span>슬리피지는 체결가에 반영 · 화면 확인용 예시</span>
          </div>
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
            <span className="badge">{records.length}</span>
          </div>
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
                {records.map((record) => (
                  <tr
                    key={record.id}
                    className={`${styles.historyRow} ${record.id === selectedId ? styles.selectedRow : ""}`}
                    onClick={() => showRecord(record)}
                  >
                    <td>
                      <button
                        type="button"
                        className={styles.historyButton}
                        aria-pressed={record.id === selectedId}
                        aria-label={`${record.title} 상세 보기`}
                      >
                        {record.title}
                      </button>
                    </td>
                    <td>
                      <strong>{record.strategyName}</strong>
                    </td>
                    <td>{instrumentTitle(record.instrument)}</td>
                    <td>
                      {record.startDate} — {record.endDate}
                    </td>
                    <td>{formatMoney(record.capital)}</td>
                    <td className="positive">+{formatMoney(record.profit)}</td>
                    <td>
                      <span className={styles.complete}>완료 · 샘플</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
                <span className="eyebrow">{selected.title}</span>
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
            <dl className={styles.snapshot}>
              <div>
                <dt>테스트 기간</dt>
                <dd>
                  {selected.startDate} — {selected.endDate}
                </dd>
              </div>
              <div>
                <dt>초기자금</dt>
                <dd>{formatMoney(selected.capital)}</dd>
              </div>
              <div>
                <dt>비용</dt>
                <dd>
                  편도 {formatMoney(selected.feePerContract)} / 계약 · 슬리피지
                  1틱(
                  {formatNumber(selected.tickSize)})
                </dd>
              </div>
              <div>
                <dt>샘플 수량·승수</dt>
                <dd>
                  {selected.quantity}계약 · 가격 1단위당{" "}
                  {formatMoney(selected.multiplier)} / 계약
                </dd>
              </div>
            </dl>
            <Tabs
              idPrefix={formId}
              label="백테스트 상세 내역"
              value={detailTab}
              onChange={setDetailTab}
              tabs={[
                { id: "decisions", label: "매매 판단", count: 3 },
                { id: "fills", label: "체결", count: 2 },
              ]}
            />
            {(["decisions", "fills"] as const).map((tab) => (
              <div
                key={tab}
                id={`${formId}-${tab}-panel`}
                role="tabpanel"
                aria-labelledby={`${formId}-${tab}-tab`}
                tabIndex={0}
                hidden={detailTab !== tab}
              >
                <RecordDetail record={selected} tab={tab} />
              </div>
            ))}
            <p className={styles.endNotice}>
              <span aria-hidden="true">ⓘ</span>{" "}
              <strong>백테스트 종료 청산</strong>은 마지막 봉 종가에서 매도
              슬리피지 1틱을 반영한 예시입니다. 진입·청산 수수료 각{" "}
              {formatMoney(selected.cost / 2)}를 순손익에서 차감했습니다.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
