import type { BacktestController } from "../useBacktestPage";
import StrategySelect from "../../../components/common/StrategySelect";
import Icon from "../../../components/common/Icon";
import DateRangeCalendar from "../../../components/common/DateRangeCalendar";
import { formatNumber } from "../../../data/format";
import { koreanAmount, percentText } from "../../../data/backtestView";
import { instrumentLabel } from "../../../data/tradingView";
import styles from "./ConfigPanel.module.css";

export default function ConfigPanel({ ctl }: { ctl: BacktestController }) {
  const {
    setSelectedStrategy,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    capital,
    setCapital,
    slippage,
    setSlippage,
    error,
    setError,
    formId,
    strategies,
    items,
    strategy,
    strategyId,
    range,
    assumptions,
    busy,
    available,
    submit,
  } = ctl;
  return (
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
              sparse={available.sparse_days}
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
            <span className={styles.labelRow}>
              초기자금
              <span
                className={styles.info}
                tabIndex={0}
                role="img"
                aria-label="초기자금 입력 범위 안내"
                aria-describedby={`${formId}-capital-help`}
              >
                <Icon name="info" size={14} />
                <span role="tooltip" id={`${formId}-capital-help`} className={styles.tip}>
                  100만 원부터 100억 원까지 입력할 수 있습니다.
                </span>
              </span>
            </span>
            <div className={styles.moneyInput}>
              <input
                id={`${formId}-capital`}
                type="text"
                inputMode="numeric"
                autoComplete="off"
                value={capital ? formatNumber(Number(capital)) : ""}
                onChange={(event) => setCapital(event.target.value.replace(/\D/g, "").slice(0, 11).replace(/^0+/, ""))}
                aria-describedby={`${formId}-capital-amount`}
              />
              <span>원</span>
            </div>
          </label>
          <span className={styles.capitalAmount} id={`${formId}-capital-amount`}>
            {capital ? koreanAmount(Number(capital)) : ""}
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
                  <input
                    className={styles.tickInput}
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    aria-label="슬리피지(틱)"
                    value={slippage}
                    onChange={(event) => setSlippage(event.target.value.replace(/\D/g, "").slice(0, 2).replace(/^0+(?=\d)/, ""))}
                  />
                  틱
                  <span className={styles.info} tabIndex={0} role="img" aria-label="슬리피지 자세히">
                    <Icon name="info" size={13} />
                    <span role="tooltip" className={`${styles.tip} ${styles.tipWrap}`}>
                      {assumptions.data.slippage.direction}. 0틱부터 20틱까지 정할 수 있습니다.
                    </span>
                  </span>
                </dd>
              </div>
              <div>
                <dt>체결</dt>
                <dd>
                  다음 봉 시가에 전량 체결
                  <span className={styles.info} tabIndex={0} role="img" aria-label="체결 가정 자세히">
                    <Icon name="info" size={13} />
                    <span role="tooltip" className={`${styles.tip} ${styles.tipWrap}`}>
                      {assumptions.data.fill.on_bar}
                    </span>
                  </span>
                </dd>
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
  );
}
