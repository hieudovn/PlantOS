# Phase 6-PV-03 — Area Monitoring View

> **Phase:** 6-PV-03 (Industrial Hardening — Process View)  
> **Depends on:** Phase 6-PV-02 (Plant Workflow Overview)  
> **Effort:** 2-3h

---

## Objective

Create the Area Monitoring View — a simplified process diagram for a specific area, showing key assets with their primary signals, alarm overlays, and drill-down to Asset Condition View.

Target area: **Filtration Area** (first implementation). Extensible to other areas via config.

---

## Task 1: Implement AreaMonitoringView

**File:** `frontend/src/features/operations/AreaMonitoringView.tsx`

Replace empty placeholder.

**Layout for Filtration Area:**
```
┌─────────────────────────────────────────────────────┐
│ Filtration Area                          ⚠️ 2 alarms │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Clarifier Outlet]                                 │
│       │                                             │
│       ▼                                             │
│  ┌─────────┐    ┌─────────┐                        │
│  │FILTER-101│    │FILTER-102│   ← Asset cards        │
│  │ 0.3 NTU  │    │ 0.4 NTU  │                        │
│  │ DP: 45kPa│    │ DP: 52kPa│                        │
│  │ ⚠️ 1 alarm│   │ ✅ OK    │                        │
│  └─────────┘    └─────────┘                        │
│       │              │                              │
│       ▼              ▼                              │
│  [Filtered Water Header]                            │
│       │                                             │
│       ▼                                             │
│  [Backwash System]                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Implementation approach:**

1. Fetch all assets in the area: `fetchAPI(\`/api/v1/assets?area_id=${areaId}\`)`
2. Filter to `asset_role = equipment` (skip functional_location, subsystem for now)
3. Render each equipment asset as an `AssetCard` in a flow layout
4. Use simple CSS grid/flex layout — no complex SVG for Phase 6-PV-03
5. "Flow" connections can be simple arrows between cards (CSS borders/pseudo-elements)

```tsx
export function AreaMonitoringView({ areaId }: { areaId: string }) {
  const { data: assets } = useQuery({
    queryKey: ["assets", areaId],
    queryFn: () => fetchAPI(`/api/v1/assets?area_id=${areaId}`),
  });
  const { data: area } = useQuery({
    queryKey: ["area", areaId],
    queryFn: () => fetchAPI(`/api/v1/areas`).then((areas: any[]) => areas.find(a => a.area_id === areaId)),
  });

  const equipmentAssets = (assets || []).filter(a => a.asset_role === 'equipment');

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{area?.name || areaId}</h2>
        {/* Alarm count badge — wire to real alarm API */}
        <span className="text-sm" style={{ color: 'var(--status-warning)' }}>⚠️ 2 alarms</span>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {equipmentAssets.map(asset => (
          <AssetCard key={asset.asset_id} asset={asset} onClick={() => navigate(`/operations/asset/${asset.asset_id}`)} />
        ))}
      </div>
    </div>
  );
}
```

---

## Task 2: Create AssetCard Component

**New file:** `frontend/src/features/operations/components/AssetCard.tsx`

```
┌─────────────────────┐
│ FILTER-101          │  ← asset name
│ filter | equipment  │  ← asset_type + asset_role badge
├─────────────────────┤
│ 0.32 NTU            │  ← primary KPI
│ Filter DP: 45 kPa   │  ← secondary KPI
├─────────────────────┤
│ ⚠️ 1 alarm  ● Live  │  ← alarm + freshness
└─────────────────────┘
```

**Props:**
```tsx
interface Props {
  asset: { asset_id: string; name: string; asset_type: string; asset_role: string };
  onClick: () => void;
}
```

**Implementation:**
- Width: full (fills grid cell), min-height: 180px
- Background: `var(--surface-card)`, border: `var(--border-default)`, rounded-lg
- Top section: asset name + type/role badges
- Middle: 2 key signals with current values (hardcode signal mapping per asset for now)
- Bottom: alarm count + freshness dot
- `cursor-pointer hover:brightness-110`
- Border-left colored by worst signal status (3px)

**Signal mapping (hardcoded for demo):**
```tsx
const AREA_SIGNALS: Record<string, string[]> = {
  "FILTER-101": ["FILTER-101.filter_dp", "FILTER-101.filtered_turbidity"],
  "FILTER-102": ["FILTER-102.filter_dp", "FILTER-102.filtered_turbidity"],
  "FILTER-QUALITY-STATION-101": ["FILTER-QUALITY-STATION-101.filtered_turbidity"],
  "BACKWASH-SYSTEM-101": ["BACKWASH-SYSTEM-101.backwash_flow"],
};
```

Use `useQueries` to batch-fetch current values for each signal.

---

## Task 3: Wire Alarm Count

For the alarm count badge on each AssetCard, use the alarms API:

```tsx
const { data: alarms } = useQuery({
  queryKey: ["alarms", asset.asset_id],
  queryFn: () => fetchAPI(`/api/v1/alarms?asset_id=${asset.asset_id}&state=active`),
  refetchInterval: 15000,
});
const activeAlarms = (alarms || []).length;
```

If the alarms API doesn't support `asset_id` filter, fetch all active alarms and filter client-side.

---

## Task 4: Update ProcessViewWorkspace Wiring

The wiring from Phase 6-PV-02 should already handle this:
```tsx
{areaId ? <AreaMonitoringView areaId={areaId} /> : ...}
```

No changes needed — just verify it works with the implemented AreaMonitoringView.

---

## Validation

1. ✅ Click "Filters" block on Plant Overview → navigates to `/operations/area/FILTRATION-AREA`
2. ✅ Area view shows asset cards for FILTER-101, FILTER-102, etc.
3. ✅ Each asset card shows 2 key signals with live values
4. ✅ Alarm count badge updates every 15s
5. ✅ Click asset card → navigates to `/operations/asset/:assetId`
6. ✅ Breadcrumb updates: WTP-DEMO-01 > Filtration Area
7. ✅ Other areas show placeholder "Coming in Phase 6-PV-04"
8. ✅ `npm run build` succeeds
