# Phase R3 — Navigation Reorganization + Trend Bundle

## Context

Phase R1 (tokens/icons) and R2 (Operations Cockpit) are deployed and verified. Phase R3 reorganizes the sidebar navigation into logical groups and adds the TrendBundle component for pre-configured multi-signal charts.

## Design Rules

- Group nav items by user purpose: Monitor, Platform
- Keep ALL existing routes working
- TrendBundle = reusable pre-configured chart component

---

## Task R3.1 — Reorganize Sidebar Navigation

In `frontend/src/components/layout/Sidebar.tsx`, group navigation items:

```
Current (flat):
  Overview
  Assets
  Signals
  Historian
  Diagrams
  GIS Map
  Alarms
  Edge Fleet
  System

New (grouped):
  ── MONITOR ──
  Overview
  Historian
  Diagrams
  GIS Map
  Alarms

  ── PLATFORM ──
  Assets
  Signals
  Edge Fleet
  System
```

Implementation:

```tsx
const navGroups = [
  {
    label: "Monitor",
    items: [
      { path: "/", icon: LayoutDashboard, label: "Overview" },
      { path: "/historian", icon: LineChart, label: "Historian" },
      { path: "/diagrams", icon: Workflow, label: "Diagrams" },
      { path: "/gis", icon: MapPin, label: "GIS Map" },
      { path: "/alarms", icon: Bell, label: "Alarms" },
    ],
  },
  {
    label: "Platform",
    items: [
      { path: "/assets", icon: Boxes, label: "Assets" },
      { path: "/signals", icon: Activity, label: "Signals" },
      { path: "/edge", icon: Server, label: "Edge Fleet" },
      { path: "/system", icon: Monitor, label: "System" },
    ],
  },
];
```

Each group has a small uppercase label (10px, `var(--text-muted)`) above its items. Keep the same active state styling.

---

## Task R3.2 — Create TrendBundle Component

Create `frontend/src/components/industrial/TrendBundle.tsx`:

```tsx
type TrendBundleProps = {
  title: string;
  description?: string;
  signals: Array<{
    signalId: string;
    label: string;
    color?: string;
    unit?: string;
  }>;
  defaultTimeRange?: "10m" | "30m" | "1h" | "6h" | "12h";
  height?: number;
};
```

This component:
1. Renders a mini trend chart using the existing `TrendChart` component
2. Auto-fetches history data for all signals
3. Shows signal labels in the legend
4. Supports time range selector (small pill buttons)

For the Overview page bottom panels, replace `MiniTrend` with `TrendBundle`:

```tsx
<TrendBundle
  title="Water Quality Chain"
  signals={[
    { signalId: "RAW-WATER-QUALITY-STATION-101.raw_turbidity", label: "Raw", color: "#dc2626" },
    { signalId: "CLARIFIER-101.settled_turbidity", label: "Settled", color: "#f59e0b" },
    { signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", label: "Filtered", color: "#16a34a" },
    { signalId: "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity", label: "Outlet", color: "#3b82f6" },
  ]}
  defaultTimeRange="1h"
  height={200}
/>
```

---

## Task R3.3 — Wire TrendBundle into Overview

Replace the current `MiniTrend` bottom section in `OverviewPage.tsx` with TrendBundle components:

```tsx
{/* ROW 3: Trend Snapshots */}
<div className="grid grid-cols-2 gap-4">
  {isWtp && (
    <>
      <TrendBundle
        title="Water Quality Chain"
        signals={[
          { signalId: "RAW-WATER-QUALITY-STATION-101.raw_turbidity", label: "Raw", color: "#dc2626", unit: "NTU" },
          { signalId: "CLARIFIER-101.settled_turbidity", label: "Settled", color: "#f59e0b", unit: "NTU" },
          { signalId: "FILTER-QUALITY-STATION-101.filtered_turbidity", label: "Filtered", color: "#16a34a", unit: "NTU" },
          { signalId: "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity", label: "Outlet", color: "#3b82f6", unit: "NTU" },
        ]}
        height={180}
        defaultTimeRange="1h"
      />
      <TrendBundle
        title="Energy & Cost"
        signals={[
          { signalId: "ENERGY-MONITORING-STATION-101.specific_energy_consumption", label: "Energy", color: "#f97316", unit: "kWh/m³" },
          { signalId: "PLANT-KPI-101.cost_per_m3", label: "Cost/m³", color: "#1e293b", unit: "VND" },
        ]}
        height={180}
        defaultTimeRange="6h"
      />
    </>
  )}
  {!isWtp && (
    <div style={{ backgroundColor: 'var(--surface-card)' }} className="rounded-lg border p-6 col-span-2 text-center" 
         style={{ borderColor: 'var(--border-default)', color: 'var(--text-muted)' }}>
      Select a plant to view trend bundles
    </div>
  )}
</div>
```

---

## Deliverables

| File | Action | Description |
|------|--------|-------------|
| `components/layout/Sidebar.tsx` | **Update** | Group nav items into Monitor/Platform |
| `components/industrial/TrendBundle.tsx` | **New** | Pre-configured multi-signal trend chart |
| `features/overview/OverviewPage.tsx` | **Update** | Replace MiniTrend with TrendBundle |

## Files NOT to touch

- ❌ All other pages
- ❌ API layer
- ❌ Backend, Edge

## Acceptance Criteria

- [ ] Sidebar shows grouped items with "MONITOR" and "PLATFORM" labels
- [ ] All nav links still work
- [ ] TrendBundle renders mini trend chart
- [ ] Overview bottom panels use TrendBundle with real data
- [ ] Water quality chain shows 4 signals with correct colors
- [ ] Energy & Cost bundle shows 2 signals
- [ ] No console errors
