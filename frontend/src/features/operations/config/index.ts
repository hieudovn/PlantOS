import { PlantConfig } from "./types";
import { wtpDemo01Config } from "./plants/wtp-demo-01";
import { vfDemoConfig } from "./plants/vf-demo";
import type { AssetSignalConfig, ThresholdConfig } from "./types";

const PLANT_CONFIGS: Record<string, PlantConfig> = {
  "WTP-DEMO-01": wtpDemo01Config,
  "VF-DEMO": vfDemoConfig,
  "DEMO-PLANT": wtpDemo01Config,
  "EDGEV2-DEMO": wtpDemo01Config,
};

export function getPlantConfig(plantId: string): PlantConfig | null {
  return PLANT_CONFIGS[plantId] || null;
}

export function getWorkflowConfig(plantId: string) {
  return getPlantConfig(plantId)?.workflow || null;
}

export function getAssetSignals(plantId: string, assetId: string): AssetSignalConfig[] {
  return getPlantConfig(plantId)?.assetSignals?.[assetId] || [];
}

export function getThreshold(plantId: string, signalId: string): ThresholdConfig | null {
  return getPlantConfig(plantId)?.thresholds?.[signalId] || null;
}
