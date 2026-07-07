# Phase 6-PV-04 — Asset Condition View

> **Phase:** 6-PV-04 (Industrial Hardening — Process View)  
> **Depends on:** Phase 6-PV-05 (Config-Driven — MUST be done first)  
> **Effort:** 3-4h

---

## Objective

Create the Asset Condition View — a detailed monitoring panel for individual assets, showing condition score, key signals, trend bundle, and alarm timeline.

---

## Task 1: Implement AssetConditionView

**File:** `src/features/operations/AssetConditionView.tsx`

Replace placeholder with full implementation.

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ FILTER-101                           Status: ⚠️ Warning  │
│ filter | equipment | Filtration Area                     │
├──────────────────────────┬──────────────────────────────┤
│ Condition Score          │ Trend Bundle                 │
│      72/100              │ [FILTER-101.filter_dp]       │
│   ⚠️ Degrading           │ [FILTER-101.effluent_flow]   │
│                          │ (last 24h, compact mode)     │
│ Key Signals              │                              │
│  DP: 62.3 kPa  ⚠️        │                              │
│  Effluent: 228 m³/h ✅   │                              │
├──────────────────────────┴──────────────────────────────┤
│ Alarm Timeline (last 48h)                               │
│  Jul 6 12:00 ⚠️ DP High    Jul 6 13:30 ✅ DP Normal     │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
```tsx
import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { getAssetSignals } from "./config";
import { TrendChart } from "@/features/historian/TrendChart";

export function AssetConditionView({ assetId }: { assetId: string }) {
  const { plantId } = useWorkspace();

  // Fetch asset details
  const { data: asset } = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => fetchAPI<any>(`/api/v1/assets/${assetId}`),
  });

  // Get signal mapping from plant config
  const signalConfigs = getAssetSignals(plantId, assetId);
  const signalIds = signalConfigs.map(s => s.signalId);

  // Condition score: heuristic based on signal thresholds
  // Simple rule: count signals in normal/warning/critical state
  // Score = (normal_signals / total_signals) * 100

  return (
    <div className="p-6 overflow-auto h-full">
      {/* Asset Header */}
      <div className="mb-4">
        <h2 className="text-xl font-bold">{asset?.name || assetId}</h2>
        <p className="text-sm">{asset?.asset_type} | {asset?.asset_role} | {asset?.area_id}</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Left: Condition Score + Key Signals */}
        <div className="space-y-4">
          <ConditionScoreCard assetId={assetId} signalIds={signalIds} />
          <KeySignalsCard signalConfigs={signalConfigs} />
        </div>

        {/* Right: Trend Bundle */}
        <div>
          <TrendBundle signalIds={signalIds} compact height={300} />
        </div>
      </div>

      {/* Bottom: Alarm Timeline */}
      <div className="mt-4">
        <AlarmTimeline assetId={assetId} />
      </div>
    </div>
  );
}
```

---

## Task 2: Create ConditionScoreCard

**New file:** `src/features/operations/components/ConditionScoreCard.tsx`

```tsx
interface Props {
  assetId: string;
  signalIds: string[];
}

export function ConditionScoreCard({ assetId, signalIds }: Props) {
  // Fetch current values for all signals
  // Use useQueries for batch
  // Compute: normal count / total count * 100
  // Display: circular gauge or big number
  // Status: Normal (>80), Warning (50-80), Critical (<50)

  const score = ...; // computed
  const status = score > 80 ? "normal" : score > 50 ? "warning" : "critical";

  return (
    <div className="rounded-lg border p-4" style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}>
      <h3 className="text-sm font-semibold mb-2">Condition Score</h3>
      <div className="text-3xl font-bold" style={{ color: STATUS_COLORS[status] }}>{score}/100</div>
      <div className="text-xs mt-1">{status === "normal" ? "Healthy" : status === "warning" ? "Degrading" : "Critical"}</div>
    </div>
  );
}
```

**Condition formula (MVP, transparent, rule-based):**
```
For each signal:
  - Fetch current value
  - Get threshold from plant config (getThreshold)
  - If value within normal range → +1 normal
  - If value in warning range → +0
  - If value in critical range → -1

Score = clamp(((normals * 100) / total), 0, 100)
```

---

## Task 3: Create KeySignalsCard

**New file:** `src/features/operations/components/KeySignalsCard.tsx`

Reuses the signal value display from AssetCard but in a vertical list format:

```
┌──────────────────────────────┐
│ Key Signals                  │
│                              │
│ DP              62.3 kPa ⚠️  │
│ Effluent Flow   228 m³/h ✅  │
│ Turbidity       0.59 NTU ✅  │
└──────────────────────────────┘
```

Each row: label (left), value + unit (right), status dot (rightmost).

---

## Task 4: Create AlarmTimeline

**New file:** `src/features/operations/components/AlarmTimeline.tsx`

Simple timeline visualization of alarms for this asset:

```tsx
export function AlarmTimeline({ assetId }: { assetId: string }) {
  const { data: alarms } = useQuery({
    queryKey: ["alarms-timeline", assetId],
    queryFn: () => fetchAPI<any[]>(`/api/v1/alarms?asset_id=${assetId}`),
    refetchInterval: 30000,
  });

  if (!alarms?.length) {
    return <div className="text-sm">No alarm history for this asset.</div>;
  }

  return (
    <div className="rounded-lg border p-4">
      <h3 className="text-sm font-semibold mb-2">Alarm Timeline (last 48h)</h3>
      <div className="space-y-1">
        {alarms.slice(0, 20).map(alarm => (
          <div key={alarm.id} className="flex items-center gap-2 text-xs">
            <span>{alarm.timestamp?.slice(0, 16)}</span>
            <span>{alarm.state === "raised" ? "⚠️" : "✅"}</span>
            <span>{alarm.alarm_code}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Task 5: Wire into ContextPanel

**File:** `src/features/operations/components/ContextPanel.tsx`

Update to show asset condition summary when an asset is selected:

```tsx
// When object.type === "asset":
// Fetch asset data
// Show mini ConditionScore + 2 key signals
// Link to full AssetConditionView
```

---

## Validation

1. ✅ Click asset in Area View → navigates to `/operations/asset/:assetId`
2. ✅ Asset Condition View shows: header, condition score, key signals, trend, alarms
3. ✅ Condition score computed from signal thresholds in plant config
4. ✅ Trend bundle renders (reuses existing TrendChart component)
5. ✅ Alarm timeline shows alarm history (or placeholder if no API)
6. ✅ Context panel shows mini condition summary when asset selected
7. ✅ Works for WTP-DEMO-01 assets (FILTER-101, etc.)
8. ✅ `npm run build` succeeds
