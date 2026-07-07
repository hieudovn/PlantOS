# Phase 6-PV-05 — Config-Driven Architecture & De-Hardcode

> **Phase:** 6-PV-05 (Industrial Hardening — Process View)  
> **Depends on:** Phase 6-PV-01/02/03 (all existing Process View components)  
> **Effort:** 3-4h  
> **Priority:** HIGH — blocks PV-04 and all future plant extensions

---

## Objective

Eliminate all hardcoded WTP-specific configs. Create a plant-level config system so adding a new plant (VF-DEMO, future plants) requires only a config file, not code changes.

---

## Problem: Current Hardcoding

| File | What's hardcoded |
|------|-----------------|
| `PlantOverviewView.tsx` | `plantId !== "WTP-DEMO-01"` check |
| `config/wtp-workflow.ts` | 7 process blocks, each with fixed areaId + signalId |
| `ProcessBlock.tsx` | `THRESHOLDS` map with 7 WTP signal IDs |
| `AssetCard.tsx` | `ASSET_SIGNALS` map for 4 WTP assets |
| `AssetCard.tsx` | `FILTER_THRESHOLDS` map for 3 WTP signal IDs |

## Solution: Plant Config System

```
src/features/operations/config/
├── types.ts              ← shared TypeScript types
├── index.ts              ← getPlantConfig(plantId) loader
├── defaults.ts           ← fallback thresholds/values
└── plants/
    ├── wtp-demo-01.ts    ← WTP plant config (extracted from hardcoded data)
    └── vf-demo.ts        ← VF plant config (stub for future)
```

---

## Task 1: Create Config Types

**New file:** `src/features/operations/config/types.ts`

```ts
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
```

---

## Task 2: Create Config Loader

**New file:** `src/features/operations/config/index.ts`

```ts
import { PlantConfig } from "./types";
import { wtpDemo01Config } from "./plants/wtp-demo-01";
import { vfDemoConfig } from "./plants/vf-demo";

const PLANT_CONFIGS: Record<string, PlantConfig> = {
  "WTP-DEMO-01": wtpDemo01Config,
  "VF-DEMO": vfDemoConfig,
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
```

---

## Task 3: Create WTP Config File

**New file:** `src/features/operations/config/plants/wtp-demo-01.ts`

Extract all hardcoded data from current components into one config file:

```ts
import { PlantConfig } from "../types";

export const wtpDemo01Config: PlantConfig = {
  workflow: [
    { id: "intake", label: "Intake", areaId: "INTAKE-AREA", signalId: "INTAKE-STRUCTURE-101.intake_flow", unit: "m³/h" },
    { id: "dosing", label: "Dosing", areaId: "CHEMICAL-DOSING-AREA", signalId: "CHEMICAL-DOSING-SYSTEM-101.coagulant_dose_rate", unit: "mg/L" },
    { id: "clarifier", label: "Clarifier", areaId: "CLARIFICATION-AREA", signalId: "CLARIFIER-101.settled_turbidity", unit: "NTU" },
    { id: "filters", label: "Filters", areaId: "FILTRATION-AREA", signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", unit: "NTU" },
    { id: "disinfection", label: "Disinfection", areaId: "DISINFECTION-AREA", signalId: "DISINFECTION-QUALITY-STATION-101.free_chlorine", unit: "mg/L" },
    { id: "storage", label: "Storage", areaId: "CLEAR-WATER-STORAGE-AREA", signalId: "CLEAR-WATER-STORAGE-101.level", unit: "%" },
    { id: "distribution", label: "Distribution", areaId: "DISTRIBUTION-AREA", signalId: "HSP-101.flow_rate", unit: "m³/h" },
  ],
  assetSignals: {
    "FILTER-101": [
      { signalId: "FILTER-101.filter_dp", label: "DP", unit: "kPa" },
      { signalId: "FILTER-101.effluent_flow", label: "Effluent", unit: "m³/h" },
    ],
    "FILTER-102": [
      { signalId: "FILTER-102.filter_dp", label: "DP", unit: "kPa" },
      { signalId: "FILTER-102.effluent_flow", label: "Effluent", unit: "m³/h" },
    ],
    "BACKWASH-PUMP-101": [
      { signalId: "BACKWASH-PUMP-101.running_status", label: "Status", unit: "" },
    ],
    "FILTER-QUALITY-STATION-101": [
      { signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", label: "Turbidity", unit: "NTU" },
      { signalId: "FILTER-QUALITY-STATION-101.filter_run_quality_index", label: "Quality", unit: "" },
    ],
  },
  thresholds: {
    "INTAKE-STRUCTURE-101.intake_flow": { warn: 400, crit: 200, direction: "low" },
    "CHEMICAL-DOSING-SYSTEM-101.coagulant_dose_rate": { warn: 50, crit: 80, direction: "high" },
    "CLARIFIER-101.settled_turbidity": { warn: 5, crit: 10, direction: "high" },
    "FILTER-QUALITY-STATION-101.filtered_turbidity": { warn: 0.5, crit: 1, direction: "high" },
    "DISINFECTION-QUALITY-STATION-101.free_chlorine": { warn: 0.8, crit: 0.5, direction: "low" },
    "FILTER-101.filter_dp": { warn: 60, crit: 80, direction: "high" },
    "FILTER-102.filter_dp": { warn: 60, crit: 80, direction: "high" },
    "CLEAR-WATER-STORAGE-101.level": { warn: 30, crit: 15, direction: "low" },
    "HSP-101.flow_rate": { warn: 300, crit: 150, direction: "low" },
  },
};
```

---

## Task 4: Create VF Config Stub

**New file:** `src/features/operations/config/plants/vf-demo.ts`

```ts
import { PlantConfig } from "../types";

export const vfDemoConfig: PlantConfig = {
  // VF-DEMO uses a different structure — single compressor train
  // Config will be populated when VF workflow is designed
  workflow: [],
  assetSignals: {},
  thresholds: {},
};
```

---

## Task 5: De-Hardcode PlantOverviewView

**File:** `src/features/operations/PlantOverviewView.tsx`

Change from:
```tsx
if (plantId !== "WTP-DEMO-01") { return <PlaceholderView ... /> }
// ... WTP_WORKFLOW.map(...)
```

To:
```tsx
import { getWorkflowConfig } from "./config";

const workflow = getWorkflowConfig(plantId);
if (!workflow || workflow.length === 0) {
  return <PlaceholderView title="Process View" message={`No workflow configured for ${plantId}.`} />;
}
// ... workflow.map(...)
```

Remove import of `WTP_WORKFLOW` from `./config/wtp-workflow`.

---

## Task 6: De-Hardcode ProcessBlock

**File:** `src/features/operations/components/ProcessBlock.tsx`

Replace the local `THRESHOLDS` constant with:
```tsx
import { useWorkspace } from "@/lib/WorkspaceContext";
import { getThreshold } from "../config";

// Inside component:
const { plantId } = useWorkspace();
const threshold = getThreshold(plantId, config.signalId);

// In deriveStatus:
function deriveStatus(signalId: string, value: number | null | undefined, threshold: ThresholdConfig | null): Status {
  if (value === null || value === undefined) return "normal";
  if (!threshold) return "normal";
  // ... same logic using threshold
}
```

---

## Task 7: De-Hardcode AssetCard

**File:** `src/features/operations/components/AssetCard.tsx`

Replace local `ASSET_SIGNALS` and `FILTER_THRESHOLDS` with:
```tsx
import { useWorkspace } from "@/lib/WorkspaceContext";
import { getAssetSignals, getThreshold } from "../config";

// Inside component:
const { plantId } = useWorkspace();
const signals = getAssetSignals(plantId, asset.asset_id);

// For thresholds:
const threshold = getThreshold(plantId, sv.signalId);
```

Remove the local `ASSET_SIGNALS` and `FILTER_THRESHOLDS` constants entirely.

---

## Task 8: Clean Up Old Files

- Delete `src/features/operations/config/wtp-workflow.ts` (merged into `plants/wtp-demo-01.ts`)
- Verify no remaining imports of old file

---

## Task 9: Create Default Thresholds

**New file:** `src/features/operations/config/defaults.ts`

```ts
import { ThresholdConfig } from "./types";

// Default thresholds for common signal patterns — used when no plant-specific threshold exists
export const DEFAULT_THRESHOLDS: Record<string, ThresholdConfig> = {
  // Generic: most flow/pressure signals warn at ±50% of typical
  // These are intentionally conservative
};

export function getDefaultThreshold(signalId: string): ThresholdConfig | null {
  return DEFAULT_THRESHOLDS[signalId] || null;
}
```

---

## Validation

1. ✅ WTP-DEMO-01: Plant Overview → 7 process blocks render correctly
2. ✅ WTP-DEMO-01: Filtration Area → 4 asset cards with signals
3. ✅ WTP-DEMO-01: ProcessBlock thresholds work (status colors)
4. ✅ VF-DEMO: Plant Overview → shows "No workflow configured" placeholder
5. ✅ VF-DEMO: Compressor Area → shows asset cards (even without signal configs)
6. ✅ No TypeScript errors: `npm run build`
7. ✅ All old hardcoded constants removed from components
8. ✅ New plant can be added by creating one config file
