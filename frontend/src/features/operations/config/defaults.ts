import { ThresholdConfig } from "./types";

export const DEFAULT_THRESHOLDS: Record<string, ThresholdConfig> = {};

export function getDefaultThreshold(_signalId: string): ThresholdConfig | null {
  return null;
}
