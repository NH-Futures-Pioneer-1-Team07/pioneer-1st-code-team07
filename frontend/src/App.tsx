import { useState } from "react";
import Icon from "./components/common/Icon";
import TradingPage from "./pages/trading/TradingPage";
import BacktestPage from "./pages/backtest/BacktestPage";
import styles from "./App.module.css";

export default function App() {
  const [page, setPage] = useState<"trading" | "backtest">("trading");

  return (
    <div className={styles.shell}>
      <a href="#main-content" className={styles.skip}>
        본문으로 이동
      </a>
      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <div className={styles.topbarStart}>
            <a
              className={styles.brand}
              href="#"
              onClick={(event) => {
                event.preventDefault();
                setPage("trading");
              }}
              aria-label="MissingLinker 모의매매 홈"
            >
              <span className={styles.brandMark} aria-hidden="true">
                M<span>L</span>
              </span>
              <span>
                Missing<strong>Linker</strong>
              </span>
            </a>
          </div>
          <div className={styles.topbarRight}>
            <span className={styles.samplePill}>
              <i />
              {page === "trading" ? "NH 모의계좌" : "샘플 데이터"}
            </span>
            <span className={styles.marketLabel}>국내선물 · KST</span>
          </div>
        </header>
        <main id="main-content" className={styles.main} tabIndex={-1}>
          <div className={styles.demoNotice}>
            <span>
              {page === "trading"
                ? "NH 모의계좌 연동 · 운용 시작과 정리는 모의계좌에 실제로 주문을 전송합니다"
                : "샘플 데이터 · 실제 주문 및 API 호출 없음 · 새로고침 시 초기화"}
            </span>
          </div>
          <div hidden={page !== "trading"}>
            <TradingPage />
          </div>
          <div hidden={page !== "backtest"}>
            <BacktestPage />
          </div>
        </main>
      </div>

      <aside className={styles.rail} aria-label="워크스페이스 메뉴바">
        <nav className={styles.navigation} aria-label="공통 메뉴">
          <button
            className={page === "trading" ? styles.activeNav : ""}
            aria-current={page === "trading" ? "page" : undefined}
            aria-label="모의매매"
            title="모의매매"
            onClick={() => setPage("trading")}
          >
            <Icon name="chart" size={22} />
          </button>
          <button
            className={page === "backtest" ? styles.activeNav : ""}
            aria-current={page === "backtest" ? "page" : undefined}
            aria-label="백테스트"
            title="백테스트"
            onClick={() => setPage("backtest")}
          >
            <Icon name="flask" size={22} />
          </button>
        </nav>
        <div className={styles.railFooter}>
          <span
            className={styles.avatar}
            role="img"
            aria-label="NH선물 모의계좌"
            title="NH선물 모의계좌"
          >
            NH
          </span>
        </div>
      </aside>

      <nav className={styles.mobileNav} aria-label="모바일 공통 메뉴">
        <button
          className={page === "trading" ? styles.activeNav : ""}
          aria-current={page === "trading" ? "page" : undefined}
          onClick={() => setPage("trading")}
        >
          <Icon name="chart" size={22} />
          <span>모의매매</span>
        </button>
        <button
          className={page === "backtest" ? styles.activeNav : ""}
          aria-current={page === "backtest" ? "page" : undefined}
          onClick={() => setPage("backtest")}
        >
          <Icon name="flask" size={22} />
          <span>백테스트</span>
        </button>
      </nav>
    </div>
  );
}
