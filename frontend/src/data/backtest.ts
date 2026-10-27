import type { Instrument, Strategy } from "./fixtures.ts";

export type TestRecord = {
  id: string;
  title: string;
  strategyName: string;
  instrument: Instrument;
  startDate: string;
  endDate: string;
  capital: number;
  profit: number;
  score: number;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  multiplier: number;
  tickSize: number;
  feePerContract: number;
  cost: number;
};

export function sampleRecord(
  id: string,
  title: string,
  strategy: Strategy,
  instrument: Instrument,
  startDate: string,
  endDate: string,
  capital: number,
): TestRecord {
  // One synthetic round trip. Prices already include one tick of adverse slippage.
  // These are display fixtures, not a strategy or a historical-data calculation.
  const tickSize = instrument.id === "samsung" ? 100 : 0.05;
  const multiplier = instrument.id === "samsung" ? 10 : 250_000;
  const entryPrice = Math.round((instrument.price + tickSize) * 100) / 100;
  const exitPrice = Math.round((instrument.price + tickSize * 31) * 100) / 100;
  const quantity = 2;
  const feePerContract = 2500;
  const cost = quantity * feePerContract * 2;
  const profit = Math.round(
    (exitPrice - entryPrice) * multiplier * quantity - cost,
  );
  return {
    id,
    title,
    strategyName: strategy.name,
    instrument,
    startDate,
    endDate,
    capital,
    profit,
    score: strategy.score,
    entryPrice,
    exitPrice,
    quantity,
    multiplier,
    tickSize,
    feePerContract,
    cost,
  };
}

export const runTimestamp = () => {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}.${pad(now.getMonth() + 1)}.${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
};
