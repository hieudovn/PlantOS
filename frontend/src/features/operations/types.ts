/** Shared types for Operations signal configuration — single source of truth. */

export interface AssetSignalConfig {
  signalId: string;
  label: string;
  unit: string;
}

export interface ThresholdConfig {
  warn: number;
  crit: number;
  direction: "high" | "low";
}
