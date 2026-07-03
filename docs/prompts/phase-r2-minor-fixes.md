# Phase R2.5 — Minor Fixes (Wire Real Data)

## Context

Phase R2 deployed successfully. The Operations Cockpit layout is correct but has minor data issues that need fixing before R3. All changes are in `frontend/src/features/overview/OverviewPage.tsx`.

## Current Issues

| # | Issue | Root Cause |
|---|-------|-----------|
| 1 | Water Quality shows unit "NTU" | Should be "% compliance" for WTP |
| 2 | Workflow diagram values hardcoded | WTP_STAGES has static mock values |
| 3 | Bottom trend panels show "No data" | TrendBundle not wired |
| 4 | Production KPI may use wrong signal ID | `raw_flow_rate` might not exist |

## Fixes

### Fix 1: Water Quality KPI → Outlet Compliance

Replace raw turbidity display with **outlet compliance rate**:

```tsx
// Replace turbidity fetch with:
const outletCompliance = useLatestValue(isWtp ? "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status" : "");
const outletQuality = useLatestValue(isWtp ? "PLANT-KPI-101.outlet_quality_index" : "");

// In KPI card:
<KpiCard
  label="Water Quality"
  value={isWtp && outletQuality.data ? formatNum(outletQuality.data.value) : "98.2"}
  unit={isWtp ? "index" : "%"}
  quality="GOOD"
  timestamp={outletQuality.data?.timestamp || undefined}
  state={outletCompliance.data?.value === false ? "critical" : "normal"}
/>
```

### Fix 2: Wire Real Data into Workflow Diagram

Replace hardcoded WTP_STAGES with values fetched from the API:

```tsx
// Fetch key signals for each stage
const rawTurb = useLatestValue("RAW-WATER-QUALITY-STATION-101.raw_turbidity");
const rwpFlow = useLatestValue("OUTLET-MANIFOLD-101.manifold_flow"); // total plant flow
const settTurb = useLatestValue("CLARIFIER-101.settled_turbidity");
const filtTurb = useLatestValue("FILTER-QUALITY-STATION-101.filtered_turbidity");
const filtDp = useLatestValue("FILTER-101.filter_dp");
const freeCl = useLatestValue("DISINFECTION-QUALITY-STATION-101.free_chlorine");
const outletFlow = useLatestValue("HSP-101.flow_rate");

// Build stages dynamically from API data
const stages = [
  {
    id: "intake", label: "Intake", status: rawTurb.data?.value > 80 ? "warning" : "normal",
    kpis: [
      { label: "Turbidity", value: rawTurb.data?.value ? formatNum(rawTurb.data.value) : "—", unit: "NTU" },
    ],
  },
  {
    id: "dosing", label: "Dosing", status: "normal",
    kpis: [
      { label: "Cl₂ Residual", value: freeCl.data?.value ? formatNum(freeCl.data.value, 1) : "—", unit: "mg/L" },
    ],
  },
  {
    id: "clarification", label: "Clarifier", status: settTurb.data?.value > 10 ? "warning" : "normal",
    kpis: [
      { label: "Turbidity", value: settTurb.data?.value ? formatNum(settTurb.data.value) : "—", unit: "NTU" },
    ],
  },
  {
    id: "filtration", label: "Filters", status: filtDp.data?.value > 80 ? "critical" : filtDp.data?.value > 60 ? "warning" : "normal",
    kpis: [
      { label: "Turbidity", value: filtTurb.data?.value ? formatNum(filtTurb.data.value) : "—", unit: "NTU" },
      { label: "DP", value: filtDp.data?.value ? formatNum(filtDp.data.value) : "—", unit: "kPa" },
    ],
  },
  {
    id: "disinfection", label: "Disinfection", status: freeCl.data?.value < 0.5 ? "critical" : freeCl.data?.value < 0.8 ? "warning" : "normal",
    kpis: [
      { label: "Free Cl₂", value: freeCl.data?.value ? formatNum(freeCl.data.value, 1) : "—", unit: "mg/L" },
    ],
  },
  {
    id: "distribution", label: "Distribution", status: "normal",
    kpis: [
      { label: "Flow", value: outletFlow.data?.value ? formatNum(outletFlow.data.value, 0) : "—", unit: "m³/h" },
    ],
  },
];
```

Remove the hardcoded `WTP_STAGES` constant and use the dynamic `stages` variable.

Also set status colors based on actual thresholds:
- raw_turbidity > 80 → warning
- settled_turbidity > 10 → warning
- filter_dp > 60 → warning, > 80 → critical
- free_chlorine < 0.8 → warning, < 0.5 → critical

### Fix 3: Wire Bottom Trend Panels

Replace "No data" placeholders with mini trend charts fetching real historical data. The simplest approach: create a `MiniTrend` sub-component that shows a tiny line:

```tsx
function MiniTrend({ title, signalIds }: { title: string; signalIds: string[] }) {
  return (
    <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-4 col-span-6">
      <h3 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: 'var(--text-secondary)' }}>
        {title}
      </h3>
      {signalIds.map(sid => {
        const { data } = useLatestValue(sid);
        return (
          <div key={sid} className="flex items-center justify-between text-sm">
            <span style={{ color: 'var(--text-muted)' }}>{sid.split(".").pop()}</span>
            <span style={{ color: 'var(--text-primary)' }} className="font-mono font-bold">
              {data?.value ? formatNum(data.value, 1) : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
```

Then in the bottom row:
```tsx
<div className="grid grid-cols-2 gap-4">
  <MiniTrend title="Water Quality" signalIds={[
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "CLARIFIER-101.settled_turbidity",
    "FILTER-QUALITY-STATION-101.filtered_turbidity",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
  ]} />
  <MiniTrend title="Energy & Cost" signalIds={[
    "ENERGY-MONITORING-STATION-101.specific_energy_consumption",
    "PLANT-KPI-101.cost_per_m3",
  ]} />
</div>
```

### Fix 4: Fix Production KPI Signal

The production throughput should use outlet manifold flow, not raw_flow_rate:

```tsx
// Replace:
const flow = useLatestValue(isWtp ? "RAW-WATER-QUALITY-STATION-101.raw_flow_rate" : "");
// With:
const flow = useLatestValue(isWtp ? "OUTLET-MANIFOLD-101.manifold_flow" : "");
```

Also add cost KPI (5th card or replace Assets card):

```tsx
const costPerM3 = useLatestValue(isWtp ? "PLANT-KPI-101.cost_per_m3" : "");
```

---

## Deliverables

Single file changed: `frontend/src/features/overview/OverviewPage.tsx`

Changes:
1. Water Quality → outlet compliance rate
2. WTP_STAGES → dynamic from API with real thresholds
3. Bottom panels → MiniTrend with real values
4. Production → correct signal ID

## Acceptance Criteria

- [ ] Water Quality shows "% compliance" or "index" (not NTU)
- [ ] Workflow diagram values come from real API data
- [ ] Workflow status colors change based on actual thresholds
- [ ] Bottom panels show real signal values
- [ ] Production KPI fetches correct signal
- [ ] No console errors
