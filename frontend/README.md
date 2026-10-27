# 프론트엔드

## 기술 스택

| 구분 | 기술 | 역할 |
| --- | --- | --- |
| 화면 | React | 컴포넌트 기반 화면 구성 |
| 언어 | TypeScript | 데이터 구조 정의와 타입 검사 |
| 개발 도구 | Vite | 로컬 개발 서버와 빌드 |
| 패키지 관리 | npm | 의존성 설치와 스크립트 실행 |
| HTTP 통신 | Axios | FastAPI에 조회·실행 요청 |
| 스타일 | CSS Modules | 컴포넌트별 스타일 관리 |

- 의존성은 `package.json`과 `package-lock.json`으로 관리한다.
- 실시간 시세는 WebSocket으로 수신한다.

## 폴더 구조

아래 구조를 기준으로 필요한 파일과 폴더부터 만든다.

```text
src/
├── main.tsx
├── App.tsx
├── pages/
│   ├── trading/
│   │   ├── TradingPage.tsx
│   │   ├── TradingPage.module.css
│   │   └── components/
│   └── backtest/
│       ├── BacktestPage.tsx
│       ├── BacktestPage.module.css
│       └── components/
├── components/
│   └── common/
├── apis/
│   ├── axiosInstance.ts
│   ├── trading.ts
│   └── backtest.ts
├── styles/
│   ├── global.css
│   ├── colors.css
│   └── fonts.css
└── assets/
    └── fonts/
```

| 위치 | 관리할 내용 |
| --- | --- |
| `pages/trading` | 모의매매 페이지 |
| `pages/backtest` | 백테스트 페이지 |
| `pages/*/components` | 해당 페이지에서만 사용하는 컴포넌트 |
| `components/common` | 여러 페이지에서 공유하는 컴포넌트 |
| `apis/axiosInstance.ts` | FastAPI 주소·타임아웃 등 공통 HTTP 설정 |
| `apis/trading.ts` | 모의매매 API 호출 함수 |
| `apis/backtest.ts` | 백테스트 API 호출 함수 |
| `styles/global.css` | 전역 기본 스타일 |
| `styles/colors.css` | 공통 색상 변수 |
| `styles/fonts.css` | 글꼴 선언 |
| `assets/fonts` | 로컬에서 사용하는 폰트 파일 |

- 컴포넌트의 CSS Module은 해당 컴포넌트 파일 옆에 둔다.
- `OrderTable.tsx`의 스타일 파일은 `OrderTable.module.css`로 작성한다.
- 추가 라이브러리는 필요한 기능이 생길 때 검토한다.
