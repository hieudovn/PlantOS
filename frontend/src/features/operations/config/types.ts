export interface ProcessBlockConfig {
  id: string;
  label: string;
  areaId: string;
  signalId: string;
  unit: string;
}

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

export interface PlantConfig {
  workflow?: ProcessBlockConfig[];
  assetSignals?: Record<string, AssetSignalConfig[]>;
  thresholds?: Record<string, ThresholdConfig>;
}
