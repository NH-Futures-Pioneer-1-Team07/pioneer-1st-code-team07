export interface Strategy {
  id: string;
  name: string;
  description: string;
  symbols: string[];
  score: number;
  indicators: string[];
}

export interface Instrument {
  id: string;
  name: string;
  code: string;
  contract: string;
  expiry: string;
  dataStart: string;
  dataEnd: string;
  price: number;
  change: number;
  volume: number;
}

// Synthetic fixtures for UI review, not market data or validated strategy rules.
export const strategies: Strategy[] = [
  {
    id: "samsung-score",
    name: "삼성전자 수급 전략",
    description: "외국인·기관 수급과 추세를 점수로 판단합니다.",
    symbols: ["samsung"],
    score: 78,
    indicators: ["외국인 순매수", "기관 순매수", "이동평균 추세"],
  },
  {
    id: "momentum",
    name: "추세 모멘텀 전략",
    description: "가격의 흐름과 거래량으로 추세를 포착합니다.",
    symbols: ["samsung", "kospi"],
    score: 64,
    indicators: ["가격 모멘텀", "거래량", "추세 강도"],
  },
  {
    id: "mean-reversion",
    name: "평균 회귀 전략",
    description: "단기 가격 이탈과 평균 회귀 구간을 탐색합니다.",
    symbols: ["kospi"],
    score: 42,
    indicators: ["평균 이격도", "변동성", "RSI"],
  },
  {
    id: "breakout",
    name: "변동성 돌파 전략",
    description: "전일 변동폭을 넘어서는 돌파 구간에서 진입을 판단합니다.",
    symbols: ["samsung", "kospi"],
    score: 71,
    indicators: ["전일 변동폭", "돌파 가격", "거래량"],
  },
  {
    id: "opening-range",
    name: "시가 범위 돌파 전략",
    description: "장 초반 가격 범위를 벗어나는 방향을 따라갑니다.",
    symbols: ["kospi"],
    score: 58,
    indicators: ["시가 범위", "초반 거래량", "방향 강도"],
  },
  {
    id: "ma-cross",
    name: "이동평균 교차 전략",
    description: "단기와 장기 이동평균의 교차로 추세 전환을 판단합니다.",
    symbols: ["samsung", "kospi"],
    score: 66,
    indicators: ["단기 이동평균", "장기 이동평균", "교차 시점"],
  },
  {
    id: "rsi-reversal",
    name: "RSI 반전 전략",
    description: "과매수·과매도 구간에서 반전 신호를 탐색합니다.",
    symbols: ["kospi"],
    score: 49,
    indicators: ["RSI", "과매도 구간", "반등 확인"],
  },
  {
    id: "bollinger",
    name: "볼린저 밴드 전략",
    description: "밴드 상·하단 이탈과 복귀를 기준으로 판단합니다.",
    symbols: ["samsung", "kospi"],
    score: 55,
    indicators: ["밴드 폭", "상·하단 이탈", "복귀 속도"],
  },
  {
    id: "volume-spike",
    name: "거래량 급증 전략",
    description: "평소보다 거래량이 급증한 구간의 가격 방향을 따릅니다.",
    symbols: ["samsung"],
    score: 61,
    indicators: ["거래량 비율", "체결 강도", "가격 방향"],
  },
  {
    id: "foreign-flow",
    name: "외국인 수급 추종 전략",
    description: "외국인 순매수 흐름이 이어지는 방향으로 판단합니다.",
    symbols: ["samsung"],
    score: 74,
    indicators: ["외국인 순매수", "누적 수급", "추세 일치"],
  },
];

export const instruments: Instrument[] = [
  {
    id: "samsung",
    name: "삼성전자 선물",
    code: "SAMSUNG-202612",
    contract: "2026.12",
    expiry: "2026-12-10",
    dataStart: "2026-09-01",
    dataEnd: "2026-10-27",
    price: 72400,
    change: 1.26,
    volume: 18246,
  },
  {
    id: "kospi",
    name: "KOSPI 200 선물",
    code: "KOSPI200-202612",
    contract: "2026.12",
    expiry: "2026-12-10",
    dataStart: "2026-09-01",
    dataEnd: "2026-10-27",
    price: 348.65,
    change: -0.42,
    volume: 128504,
  },
];

export const strategyById = (id: string) =>
  strategies.find((item) => item.id === id) ?? strategies[0];

export const supportedInstruments = (strategy: Strategy) =>
  instruments.filter((item) => strategy.symbols.includes(item.id));

// A futures instrument is the product plus its contract month.
export const instrumentTitle = (item: { name: string; contract: string }) =>
  `${item.name} · ${item.contract}`;

export const sampleTime = "2026.10.27 10:32:08";
export const formatNumber = (value: number) =>
  value.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
export const formatMoney = (value: number) => `${formatNumber(value)}원`;
