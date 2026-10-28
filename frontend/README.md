# 프론트엔드

## 로컬 실행

- Node.js 22.12 이상을 사용한다.
- 프로젝트 루트에서 다음 명령을 실행한다.

```bash
cd frontend
npm ci
npm run dev
```

- 브라우저에서 개발 서버가 출력한 주소에 접속한다.
- 기본 주소는 `http://127.0.0.1:5173`이다.

| 명령 | 확인할 내용 |
| --- | --- |
| `npm run typecheck` | TypeScript 타입 검사 |
| `npm test` | 화면 변환(차트 배치·상태 문장·종목 이름·진행률·입력 검증·자산 곡선과 체결 묶기) 검증 |
| `npm run build` | 타입 검사와 배포용 정적 파일 생성 |
| `npm run preview` | 빌드한 `dist/` 로컬 미리보기 |

## 기술 스택

| 구분 | 기술 | 역할 |
| --- | --- | --- |
| 화면 | React | 컴포넌트 기반 화면 구성 |
| 언어 | TypeScript | 데이터 구조 정의와 타입 검사 |
| 개발 도구 | Vite | 로컬 개발 서버와 빌드 |
| 패키지 관리 | npm | 의존성 설치와 스크립트 실행 |
| HTTP 통신 | Axios | FastAPI에 조회·실행 요청 |
| 차트 | Recharts | 백테스트 자산 변화 차트(가격 일봉·거래 막대·호버 상세) |
| 스타일 | CSS Modules | 컴포넌트별 스타일 관리 |

- 의존성은 `package.json`과 `package-lock.json`으로 관리한다.
- 두 화면은 FastAPI를 폴링하고, 실시간 시세는 WebSocket(`/ws/market`)으로 수신한다.
- 개발 서버는 `/api`·`/ws`를 백엔드(기본 `http://127.0.0.1:8000`, `BACKEND_URL`로 변경)로 프록시한다.

## 폴더 구조

아래 구조를 기준으로 필요한 파일과 폴더부터 만든다.
`data/`에는 숫자 서식과 API 응답을 화면용으로 바꾸는 함수를 둔다.
두 화면 모두 `apis/`로 백엔드에 연결한다.

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
│           ├── EquityChart.tsx
│           └── RecordDetail.tsx
├── components/
│   └── common/
├── data/
│   ├── fixtures.ts
│   ├── trading.ts
│   ├── backtest.ts
│   ├── trading.test.ts
│   └── backtest.test.ts
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
| `apis/client.ts` | 공통 Axios 설정과 오류 문구 |
| `apis/trading.ts` | 전략·모의매매·시세·이력 API 호출 함수 |
| `apis/backtest.ts` | 백테스트 실행·가능 기간·가정·실행 상세 API 호출 함수 |
| `apis/polling.ts` | 주기적 조회 훅 |
| `apis/marketStream.ts` | 실시간 시세 WebSocket 훅 |
| `apis/types.ts` | API 응답 타입 |
| `styles/global.css` | 전역 기본 스타일 |
| `styles/colors.css` | 공통 색상 변수 |
| `styles/fonts.css` | 글꼴 선언 |
| `assets/fonts` | 로컬에서 사용하는 폰트 파일 |

- 컴포넌트의 CSS Module은 해당 컴포넌트 파일 옆에 둔다.
- `OrderTable.tsx`의 스타일 파일은 `OrderTable.module.css`로 작성한다.
- 추가 라이브러리는 필요한 기능이 생길 때 검토한다.
