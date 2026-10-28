export const formatNumber = (value: number) =>
  value.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
export const formatMoney = (value: number) => `${formatNumber(Math.round(value))}원`;
