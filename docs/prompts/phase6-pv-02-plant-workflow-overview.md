# Phase 6-PV-02 — Plant Workflow Overview

> **Phase:** 6-PV-02 (Industrial Hardening — Process View)  
> **Depends on:** Phase 6-PV-01 (Workspace Foundation)  
> **Effort:** 4-5h (including collapsible sidebar)

---

## Objective

1. Make sidebar collapsible: icon-only default (56px), expand on hover (160px)
2. Create the Plant Workflow Overview — 7 process blocks for WTP-DEMO-01

---

## Task 0: Collapsible Sidebar (~1h)

**File:** `frontend/src/components/layout/Sidebar.tsx`

**Requirements:**
- Default collapsed: `w-14` (56px), icons only, no labels, no section headers
- Hover expand: `w-40` (160px, down from current 240px), show labels + headers
- Smooth transition: `transition-all duration-200`
- Collapsed state: nav items icon-only centered, section headers hidden, brand icon-only, footer version-only
- Expanded state: full labels, headers visible, brand text, role badge
- State: `useState` for `expanded`, `onMouseEnter`/`onMouseLeave`
- Accessibility: `title` attribute on icon-only nav items

---

## Task 1: Create PlantOverviewView

**File:** `frontend/src/features/operations/PlantOverviewView.tsx`

Replace the empty placeholder with the workflow diagram.

**7 Process Blocks (WTP-DEMO-01):**

```text
Intake → Dosing → Clarifier → Filters → Disinfection → Storage → Distribution
```

Each block maps to a WTP area:
| Block | Area ID | Key Signal |
|-------|---------|------------|
| Intake | `INTAKE-AREA` | `INTAKE-STRUCTURE-101.intake_flow` |
| Dosing | `CHEMICAL-DOSING-AREA` | `CHEMICAL-DOSING-SYSTEM-101.coagulant_dose_rate` |
| Clarifier | `CLARIFICATION-AREA` | `CLARIFIER-101.settled_turbidity` |
| Filters | `FILTRATION-AREA` | `FILTER-QUALITY-STATION-101.filtered_turbidity` |
| Disinfection | `DISINFECTION-AREA` | `DISINFECTION-QUALITY-STATION-101.free_chlorine` |
| Storage | `CLEAR-WATER-STORAGE-AREA` | `CLEAR-WATER-STORAGE-101.level` |
| Distribution | `DISTRIBUTION-AREA` | `HSP-101.flow_rate` |

**Layout:** Horizontal flow with arrow connectors. Each block is a `ProcessBlock` component.

```tsx
export function PlantOverviewView() {
  const { plantId } = useWorkspace();
  // Only render for WTP-DEMO-01 for now
  if (plantId !== "WTP-DEMO-01") {
    return <Placeholder plantId={plantId} />;
  }
  return (
    <div className="flex items-center justify-center gap-2 p-8 h-full overflow-x-auto">
      {WTP_WORKFLOW.map((block, i) => (
        <React.Fragment key={block.id}>
          <ProcessBlock config={block} onClick={() => navigate(`/operations/area/${block.areaId}`)} />
          {i < WTP_WORKFLOW.length - 1 && <ArrowRight className="w-6 h-6" style={{ color: 'var(--text-muted)' }} />}
        </React.Fragment>
      ))}
    </div>
  );
}
```

---

## Task 2: Create ProcessBlock Component

**File:** `frontend/src/features/operations/components/ProcessBlock.tsx`

Each block displays:
```
┌─────────────────┐
│  ✅ Intake      │  ← Status icon + name
│  12.5 m³/h      │  ← Primary KPI value
│  0 alarms       │  ← Alarm count badge
│  ● Live         │  ← Data freshness dot
└─────────────────┘
```

**Props:**
```tsx
interface ProcessBlockConfig {
  id: string;
  label: string;
  areaId: string;
  signalId: string;
  unit: string;
}
```

**Implementation:**
- Fetch current value from `/api/v1/measurements/current?signal_id={signalId}` (useQuery, refetchInterval: 10000)
- Fetch alarms from `/api/v1/alarms?state=active&asset_id=...` (or a simpler approach: just show 0 for now, wire in PV-03)
- Status derived from:
  - `normal`: value within normal range + data fresh + 0 alarms
  - `warning`: value approaching limit OR 1-2 alarms
  - `critical`: value exceeded limit OR 3+ alarms
- Status icon: `CheckCircle` (green), `AlertTriangle` (yellow), `XCircle` (red)
- Background: `var(--surface-card)`, border: `var(--border-default)`
- Border-left colored by status (3px)
- Width: `w-40` (160px), height: `h-32` (128px)
- `cursor-pointer hover:brightness-110 transition-all`

**Threshold config (hardcoded for demo):**
```tsx
const THRESHOLDS: Record<string, { warn: number; crit: number; direction: 'high' | 'low' }> = {
  "INTAKE-STRUCTURE-101.intake_flow": { warn: 1000, crit: 500, direction: 'low' },
  "CLARIFIER-101.settled_turbidity": { warn: 5, crit: 10, direction: 'high' },
  "FILTER-QUALITY-STATION-101.filtered_turbidity": { warn: 0.5, crit: 1, direction: 'high' },
  "DISINFECTION-QUALITY-STATION-101.free_chlorine": { warn: 0.8, crit: 0.5, direction: 'low' },
  // ... others with reasonable defaults
};
```

---

## Task 3: Create WTP Workflow Config

**File:** `frontend/src/features/operations/config/wtp-workflow.ts`

```tsx
import { ProcessBlockConfig } from "../components/ProcessBlock";

export const WTP_WORKFLOW: ProcessBlockConfig[] = [
  { id: "intake", label: "Intake", areaId: "INTAKE-AREA", signalId: "INTAKE-STRUCTURE-101.intake_flow", unit: "m³/h" },
  { id: "dosing", label: "Dosing", areaId: "CHEMICAL-DOSING-AREA", signalId: "CHEMICAL-DOSING-SYSTEM-101.coagulant_dose_rate", unit: "mg/L" },
  { id: "clarifier", label: "Clarifier", areaId: "CLARIFICATION-AREA", signalId: "CLARIFIER-101.settled_turbidity", unit: "NTU" },
  { id: "filters", label: "Filters", areaId: "FILTRATION-AREA", signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", unit: "NTU" },
  { id: "disinfection", label: "Disinfection", areaId: "DISINFECTION-AREA", signalId: "DISINFECTION-QUALITY-STATION-101.free_chlorine", unit: "mg/L" },
  { id: "storage", label: "Storage", areaId: "CLEAR-WATER-STORAGE-AREA", signalId: "CLEAR-WATER-STORAGE-101.level", unit: "%" },
  { id: "distribution", label: "Distribution", areaId: "DISTRIBUTION-AREA", signalId: "HSP-101.flow_rate", unit: "m³/h" },
];
```

**Important:** The 7 area IDs above are the canonical WTP-DEMO-01 areas. If any area_id doesn't exist in the current database, use the closest match from `/api/v1/areas?plant_id=WTP-DEMO-01`. The coder should verify area IDs by calling the API and adjusting if needed.

---

## Task 4: Wire into ProcessViewWorkspace

**File:** `frontend/src/features/operations/ProcessViewWorkspace.tsx`

Update the main canvas section:

```tsx
// In the main canvas area, replace the placeholder:
<main className="flex-1 overflow-auto">
  {!areaId && !assetId ? (
    <PlantOverviewView />
  ) : areaId ? (
    <AreaMonitoringView areaId={areaId} />
  ) : (
    <AssetConditionView assetId={assetId!} />
  )}
</main>
```

The `AreaMonitoringView` and `AssetConditionView` are still empty placeholders from Phase 6-PV-01 — they'll show "Coming in Phase 6-PV-03/04" for now.

---

## Task 5: Create Placeholder Component

**New file:** `frontend/src/features/operations/components/PlaceholderView.tsx`

Reusable placeholder for non-WTP plants and unimplemented views:

```tsx
export function PlaceholderView({ title, message }: { title: string; message: string }) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center" style={{ color: 'var(--text-muted)' }}>
        <Factory className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p className="text-lg mb-1">{title}</p>
        <p className="text-sm">{message}</p>
      </div>
    </div>
  );
}
```

---

## Validation

1. ✅ `/operations` shows 7 process blocks for WTP-DEMO-01
2. ✅ Each block shows live KPI value from current API
3. ✅ Status colors update based on threshold rules
4. ✅ Click block → URL changes to `/operations/area/:areaId`
5. ✅ Breadcrumb updates when navigating
6. ✅ Selecting VF-DEMO or other plant shows placeholder (not broken)
7. ✅ Arrow connectors between blocks
8. ✅ `npm run build` succeeds
