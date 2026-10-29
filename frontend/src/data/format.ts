export const formatNumber = (value: number) =>
  value.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
export const formatMoney = (value: number) => `${formatNumber(Math.round(value))}원`;

/** `2026-10-29` 형태의 날짜를 `2026.10.29`로 바꾼다. 빈 값은 그대로 빈 값이다. */
export const dotted = (day: string) => (day ? day.replaceAll("-", ".") : "");

/** 손익 값에 맞는 색상 클래스. 이익은 `positive`, 손실은 `negative`, 0이나 값이 없으면 빈 문자열이다. */
export const pnlClass = (value: number | null | undefined) =>
  value === null || value === undefined || value === 0 ? "" : value > 0 ? "positive" : "negative";

/** 값이 없을 때 대신 보여 주는 표시. */
export const dash = "—";

/** 값이 없으면 `—`, 있으면 천 단위로 끊은 숫자. */
export const won = (value: number | null | undefined) =>
  value === null || value === undefined ? dash : formatNumber(value);
