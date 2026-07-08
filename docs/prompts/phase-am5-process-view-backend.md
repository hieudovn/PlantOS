# Phase AM-5 — Process View Backend-Driven

> **Phase:** AM-5 (Asset Model Builder — Final)  
> **Depends on:** AM-4 (formulas + KPIs ready)  
> **Effort:** 2-3h  
> **Commit:** `377e161`  

---

## Objective

Process View reads workflow, bindings, and KPI from backend API. Frontend config (`config/plants/*.ts`) becomes fallback/seed only. This completes the migration from hardcoded to config-driven.

---

## Task 1: Backend — Process View Config API

**New file:** `backend/app/modules/process_view/router.py`

### `GET /api/v1/plants/{plant_id}/process-view`

Returns the full process view configuration for a plant:

```json
{
  "plant_id": "WTP-DEMO-01",
  "workflow": [
    {
      "id": "intake",
      "label": "Intake",
      "area_id": "INTAKE-AREA",
      "kpi_signal_id": "RWP-101.flow_rate",
      "kpi_unit": "m3/h",
      "kpi_type": "signal"
    }
  ],
  "areas": [
    {
      "area_id": "FILTRATION-AREA",
      "name": "Filtration Area",
      "asset_count": 4
    }
  ],
  "source": "backend"
}
```

*   **Implementation:** Initially return hardcoded config for WTP-DEMO-01 (migrate from `config/plants/wtp-demo-01.ts`). For other plants, return `{"plant_id": "...", "workflow": [], "source": "backend"}`.
*   **Future:** Read from `asset_attribute_bindings` + `kpi_definitions` to build workflow dynamically.
*   **Fallback:** Frontend checks `source` field. If "backend", use this. If API fails, fallback to local config.

### `GET /api/v1/assets/{asset_id}/condition-config`

Returns condition view config for an asset:

```json
{
  "asset_id": "FILTER-101",
  "signals": [
    {"signal_id": "FILTER-101.filter_dp", "label": "DP", "unit": "kPa"},
    {"signal_id": "FILTER-101.effluent_flow", "label": "Effluent", "unit": "m3/h"}
  ],
  "thresholds": {
    "FILTER-101.filter_dp": {"warn": 60, "crit": 80, "direction": "high"}
  },
  "kpi_ids": [],
  "source": "backend"
}
```

*   **Implementation:** First, try to read from `asset_attribute_bindings` for the asset. If bindings exist, use them. Otherwise, fallback to hardcoded WTP config (mirror current `config/plants/wtp-demo-01.ts`).
*   **Future:** Read from bindings + formula + KPI tables.

### `GET /api/v1/plants/{plant_id}/workflow-config`

Simplified endpoint returning just the workflow blocks (used by PlantOverviewView).

Register in `v1.py`:
```python
from app.modules.process_view.router import router as process_view_router
router.include_router(process_view_router, tags=["Process View"])
```

---

## Task 2: Frontend — `useProcessConfig` Hook

**New file:** `frontend/src/features/operations/hooks/useProcessConfig.ts`

```ts
import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { getPlantConfig } from "../config";

export function useProcessConfig(plantId: string) {
  return useQuery({
    queryKey: ["process-config", plantId],
    queryFn: async () => {
      const res = await fetchAPI<any>(`/api/v1/plants/${plantId}/process-view`);
      if (res?.source === "backend") return res;
      throw new Error("Backend returned fallback, using local config");
    },
    staleTime: 60000,
    // Fallback to local config if API fails
    placeholderData: () => {
      const local = getPlantConfig(plantId);
      return local ? { plant_id: plantId, workflow: local.workflow || [], source: "fallback" } : undefined;
    },
    retry: 1,
  });
}

export function useConditionConfig(assetId: string) {
  return useQuery({
    queryKey: ["condition-config", assetId],
    queryFn: () => fetchAPI<any>(`/api/v1/assets/${assetId}/condition-config`),
    staleTime: 60000,
    retry: 1,
  });
}
```

---

## Task 3: Frontend — Update `PlantOverviewView`

**File:** `frontend/src/features/operations/PlantOverviewView.tsx`

Replace direct `getWorkflowConfig()` call with hook:

```tsx
import { useProcessConfig } from "./hooks/useProcessConfig";

export function PlantOverviewView() {
  const { plantId } = useWorkspace();
  const navigate = useNavigate();
  const { data: config } = useProcessConfig(plantId);

  const workflow = config?.workflow;

  if (!workflow || workflow.length === 0) {
    return <PlaceholderView title="Process View" message={`No workflow configured for ${plantId}.`} />;
  }

  return (
    <div className="flex items-center justify-center gap-2 p-8 h-full overflow-x-auto">
      {workflow.map((block, i) => (
        // ... same as before, using block.id, block.label, etc.
      ))}
    </div>
  );
}
```

Also show a small badge indicating the source:
```tsx
{config?.source === "backend" ? "API" : "Local"}
```

---

## Task 4: Frontend — Update `AssetConditionView`

**File:** `frontend/src/features/operations/AssetConditionView.tsx`

Use `useConditionConfig` to get signals and thresholds from API, falling back to current `getAssetSignals()` + `getThreshold()` from local config:

```tsx
import { useConditionConfig } from "./hooks/useProcessConfig";

export function AssetConditionView({ assetId }: { assetId: string }) {
  const { plantId } = useWorkspace();
  const { data: condConfig } = useConditionConfig(assetId);

  // Use API config if available, else fallback to local config
  const signalConfigs = condConfig?.signals?.length
    ? condConfig.signals.map((s: any) => ({ signalId: s.signal_id, label: s.label, unit: s.unit }))
    : getAssetSignals(plantId, assetId);

  // Rest of component unchanged...
}
```

---

## Task 5: Frontend — KPI in Process View Blocks

**File:** `frontend/src/features/operations/components/ProcessBlock.tsx`

Optionally show KPI values from API if available. Add a small KPI badge when `config.kpiType === "kpi"`:

```tsx
// If config has kpi_type === "kpi", fetch from /api/v1/kpis/current/values
const { data: kpiValue } = useQuery({
  queryKey: ["kpi-current", config.kpi_signal_id],
  queryFn: () => fetchAPI<any>(`/api/v1/kpis/current/values?scope_id=${config.area_id}`),
  enabled: config.kpi_type === "kpi",
  refetchInterval: 30000,
});
```

---

## Task 6: Frontend — Sidebar + Route for KPIs

Add KPI navigation link if not already there. Route was added in AM-4.

**File:** `frontend/src/components/layout/Sidebar.tsx`

Add under MANAGEMENT or PLATFORM section:
```tsx
<NavLink to="/kpis" icon={...}>KPIs</NavLink>
<NavLink to="/formulas" icon={...}>Formulas</NavLink>
```

---

## Validation

```bash
# 1. Process view API
curl -H "X-API-Key: ..." http://127.0.0.1:8000/api/v1/plants/WTP-DEMO-01/process-view
# → { "plant_id": "WTP-DEMO-01", "workflow": [...], "source": "backend" }

# 2. Condition config API
curl -H "X-API-Key: ..." http://127.0.0.1:8000/api/v1/assets/FILTER-101/condition-config
# → { "signals": [...], "thresholds": {...}, "source": "backend" }

# 3. Process View UI
# Navigate to /operations → 7 WTP blocks
# Check browser console for "process-config" query
# Toggle VF-DEMO → "No workflow configured"

# 4. TypeScript
cd frontend && npx tsc --noEmit

# 5. Backward compat: Kill backend → UI falls back to local config
```

---

## Out of Scope

- Dynamic workflow builder (dragging blocks)
- Real-time KPI dashboard
- Multi-plant process view comparison
- Contract YAML export of process view config
