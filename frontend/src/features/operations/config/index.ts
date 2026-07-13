import type { AssetSignalConfig, ThresholdConfig } from "./types";

/** @deprecated — use useAssetSignals() hook instead (fetches from API). */
export function getAssetSignals(_plantId: string, _assetId: string): AssetSignalConfig[] {
  return [];
}

/** @deprecated — thresholds should come from API in future. */
export function getThreshold(_plantId: string, _signalId: string): ThresholdConfig | null {
  return null;
}
