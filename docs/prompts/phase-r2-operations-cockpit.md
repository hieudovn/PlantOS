# Phase R2 — Operations Cockpit

## Context

You are the Coder-Executioner for PlantOS Center UI Redesign Phase R2.

Phase R1 (Design Foundation) is complete: tokens.css, Lucide icons, version badge, DataQualityBadge. The visual foundation is in place.

Phase R2 transforms the Overview page from an admin dashboard (DB stats, CPU, RAM) into an **Industrial Operations Cockpit** — a decision-support surface for operators.

## Required Reading

```text
docs/design/center-ui-pm-decision.md              ← PM decision (Alt A layout)
docs/design/center-ui-dashboard-best-practices.md ← Best practices (5-6 cards, F-pattern)
frontend/src/features/overview/OverviewPage.tsx   ← Current Overview (to replace)
frontend/src/styles/tokens.css                     ← Design tokens (use these!)
```

## Design Rules (MANDATORY)

1. **5-6 cards max** in initial viewport
2. **F-pattern**: most critical info top-left
3. **Big bold numbers**: KPI values 28-36px
4. **Single screen**: no scroll on 1920x1080
5. **Grid layout**: CSS Grid 12-column
6. **Use tokens**: `var(--surface-card)`, `var(--text-primary)`, etc.
7. **Move DB/server stats** to a separate System page — do NOT delete, just relocate

---

## Task R2.1 — Create KpiCard Component

Create `frontend/src/components/industrial/KpiCard.tsx`:

```tsx
type KpiCardProps = {
  label: string;
  value: string | number;
  unit?: string;
  state?: "normal" | "warning" | "critical" | "offline";
  trend?: "up" | "down" | "flat";
  trendLabel?: string;
  quality?: string;
  timestamp?: string;
  onClick?: () => void;
};
```

Design:

```
┌─────────────────────┐
│ Label               │  ← text-secondary, 12px
│                     │
│ 0.32 NTU            │  ← text-primary, 28px bold (big number)
│ ● Good · 3s ago     │  ← DataQualityBadge
│ ▲ +12% vs normal    │  ← trend indicator (optional)
└─────────────────────┘
```

Use `var(--surface-card)` for background, `var(--border-default)` for border.
State colors: normal=no indicator, warning=amber left border, critical=red left border.

---

## Task R2.2 — Create WorkflowDiagram Component

Create `frontend/src/components/diagrams/WorkflowDiagram.tsx`.

This is a **simplified block-based process flow diagram** — NOT a full P&ID. Use plain React/CSS (no React Flow yet — that's for later).

```tsx
type StageProps = {
  id: string;
  label: string;
  status: "normal" | "warning" | "critical";
  kpis: Array<{ label: string; value: string | number; unit?: string }>;
  onClick?: () => void;
};

type WorkflowDiagramProps = {
  stages: StageProps[];
  plantId: string;
};
```

Design:

```
┌──────────────────────────────────────────────────────────────┐
│                    WORKFLOW DIAGRAM                           │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │ INTAKE   │───▶│ DOSING   │───▶│ CLARIFIER│──▶ ...        │
│  │   ✅     │    │   ✅     │    │   ⚠️    │                 │
│  │ 85 NTU   │    │ 12 L/min │    │ 5.2 NTU  │               │
│  └──────────┘    └──────────┘    └──────────┘               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

For WTP, 6 stages:
```
Intake → Chemical Dosing → Clarification → Filtration → Disinfection → Distribution
```

Each stage block:
- Status indicator (green/amber/red dot)
- Stage name
- 1-2 KPI values
- Click → navigate to area/asset detail (future)

**For MVP:** Hardcode the 6 WTP stages. The component API should accept `stages` array so it's reusable for other plants later.

---

## Task R2.3 — Redesign Overview Page

Rewrite `frontend/src/features/overview/OverviewPage.tsx`.

### New Layout (Alt A — Operations Cockpit)

```
┌──────────────────────────────────────────────────────────────┐
│ ROW 1: KPI Cards (CSS Grid, 5 columns)                       │
│ ┌──────────┬──────────┬──────────┬──────────┬──────────┐    │
│ │ Health   │ Product. │ Quality  │ Energy   │ Alarms   │    │
│ │ ✅ Good  │ 8,450 m³ │ 98.2%    │ 0.38     │ 3 active │    │
│ └──────────┴──────────┴──────────┴──────────┴──────────┘    │
├────────────────────────────────────────┬─────────────────────┤
│ ROW 2: Workflow Diagram (span 8)       │ Active Incidents    │
│                                        │ (span 4)            │
│ [Intake]→[Dosing]→...→[Distribution]   │ ● Filter DP High    │
│                                        │ ● Turbidity Warn    │
├────────────────────────────────────────┴─────────────────────┤
│ ROW 3: Trend Snapshots (2 columns)                           │
│ ┌──────────────────────┬──────────────────────────────────┐  │
│ │ Quality Trend        │ Energy & Cost Trend              │  │
│ │ (mini line chart)    │ (mini line chart)                │  │
│ └──────────────────────┴──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Implementation Notes

1. **Use `useWorkspace()`** to detect current plant. Show plant-specific KPI data.
2. **For MVP with WTP**: mock KPI values from the historian API (fetch latest values for key signals).
3. **DataQualityBadge**: use it on every KPI card that has a timestamp.
4. **Alarm count**: fetch from `/api/v1/alarms?state=active`.
5. **Use tokens** for all colors — no hardcoded `bg-gray-900`.

### Fetch real data

```tsx
// Fetch key signals for KPI cards
const { data: rawTurbidity } = useQuery({
  queryKey: ["current", "RAW-WATER-QUALITY-STATION-101.raw_turbidity"],
  queryFn: () => getHistory({ signal_id: "RAW-WATER-QUALITY-STATION-101.raw_turbidity", limit: 1 }),
  refetchInterval: 10000,
});
// ... similar for other KPIs
```

### Remove from Overview (move to System page)

These sections move to a new `SystemHealthPage`:
- Database stats (PG records, TD measurements, sizes)
- Server Resources (CPU, RAM, Disk)

Create `frontend/src/features/system/SystemHealthPage.tsx` with the extracted content.

Add route in `App.tsx`:
```tsx
<Route path="/system" element={<SystemHealthPage />} />
```

Add nav item in Sidebar:
```
⚡ System
```

---

## Task R2.4 — Add AlarmBadge to Topbar

In `frontend/src/components/layout/Topbar.tsx`, add a small alarm indicator next to the workspace selector:

```tsx
// Fetch active alarm count
const { data: alarmCount } = useQuery({
  queryKey: ["alarms-active"],
  queryFn: () => getAlarms({ state: "active" }),
  refetchInterval: 15000,
});

// In the header, add:
{alarmCount && alarmCount.length > 0 && (
  <span className="flex items-center gap-1 text-xs">
    <Bell className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
    <span style={{ color: 'var(--status-critical)' }}>{alarmCount.length}</span>
  </span>
)}
```

---

## Task R2.5 — Data Freshness Indicator

In Topbar, next to the plant selector, add a data freshness indicator:

```tsx
const [dataAge, setDataAge] = useState(0);
// Update every 5s
useEffect(() => {
  const interval = setInterval(() => setDataAge(prev => prev + 5), 5000);
  return () => clearInterval(interval);
}, []);

const freshnessColor = dataAge < 30 ? 'var(--status-normal)' : 
                       dataAge < 120 ? 'var(--status-warning)' : 'var(--status-critical)';

// Display:
<span className="flex items-center gap-1 text-xs">
  <Circle className="w-2 h-2 fill-current" style={{ color: freshnessColor }} />
  <span style={{ color: 'var(--text-muted)' }}>Live</span>
</span>
```

---

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `components/industrial/KpiCard.tsx` | **New** | KPI card component |
| `components/diagrams/WorkflowDiagram.tsx` | **New** | Block-based process flow |
| `features/overview/OverviewPage.tsx` | **Replace** | Operations Cockpit |
| `features/system/SystemHealthPage.tsx` | **New** | DB/Server metrics (relocated) |
| `components/layout/Topbar.tsx` | **Update** | Add AlarmBadge + freshness |
| `components/layout/Sidebar.tsx` | **Update** | Add System nav item |
| `App.tsx` | **Update** | Add /system route |

## Files NOT to touch

- ❌ API layer, backend, edge agent
- ❌ Historian, Assets, Signals, Diagrams, GIS, Alarms, Edge Fleet pages
- ❌ Existing routes (only ADD /system, don't remove)

## Acceptance Criteria

- [ ] Overview shows 5 KPI cards with real values
- [ ] Workflow diagram shows 6 WTP stages with status
- [ ] DB/Server stats moved to /system page
- [ ] Topbar shows alarm count badge + data freshness
- [ ] All pages still accessible via navigation
- [ ] No 401 errors in console
- [ ] Uses design tokens, not hardcoded colors
