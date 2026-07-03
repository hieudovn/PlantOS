# PlantOS Center UI/UX Redesign Plan — PM Review & Proposal

**Date:** 2026-07-03 | **Status:** Planning (not for implementation yet)

---

## 1. Design Principles Review — PM Assessment

### What the principles get RIGHT

| Principle | Assessment |
|-----------|-----------|
| Object-first, not tag-first | ✅ Core PlantOS philosophy — we already have Asset/Signal binding |
| Dark-first, not dark-only | ✅ Matches industrial monitoring use case |
| Read-only diagrams (not SCADA) | ✅ Aligned with constitution: "PlantOS is not a SCADA replacement" |
| Drill-down navigation | ✅ Essential for complex plant data |
| Trend bundles over raw tags | ✅ We already prototyped this with WTP bundles |
| Semantic color tokens | ✅ Critical for maintainability |
| Multiple user views | ✅ PlantOS serves operators, engineers, managers |

### Where current UI violates the principles

| # | Violation | Severity | Current Behavior |
|---|-----------|----------|-----------------|
| V1 | Emoji icons in sidebar (🏭, 📋, 🚧) | Medium | Used throughout navigation |
| V2 | Hardcoded colors (`bg-gray-900`, `text-gray-400`) | High | Every component, making theming impossible |
| V3 | "MVP Preview" label in topbar | Low | Unprofessional for industrial product |
| V4 | Overview shows DB stats, CPU, RAM — not operational | High | Admin-focused, not operator-focused |
| V5 | Missing data quality indicators | Medium | No freshness/quality badges on values |
| V6 | Missing unit display consistency | Medium | Some values show units, some don't |
| V7 | No alarm lifecycle visualization | Medium | Alarms page exists but basic |
| V8 | Hardcoded plant IDs in components | High | WTP/VF-DEMO hardcoded in 4 files |
| V9 | No theme token system | Critical | All colors inline, no design system |

---

## 2. Current UI State — Baseline

```
PlantOS Center v0.1.0
├── Sidebar
│   ├── 🏭 Overview      (emoji icon)
│   ├── 📋 Assets         (emoji icon)
│   ├── 📡 Signals        (emoji icon)
│   ├── 📈 Historian      (emoji icon)
│   ├── 🗺️ Diagrams       (emoji icon)
│   ├── 🌍 GIS Map        (emoji icon)
│   ├── 🚨 Alarms         (emoji icon)
│   └── 🖥️ Edge Fleet     (emoji icon)
├── Topbar
│   ├── Workspace dropdown (functional)
│   └── MVP Preview badge
├── Overview Page
│   ├── Assets count card
│   ├── Signals count card
│   ├── Edge Nodes card
│   ├── Database stats (PG records, TD measurements, sizes)
│   └── Server Resources (CPU, RAM, Disk)
├── Assets Page (table, tree, detail)
├── Signals Page (table)
├── Historian (trend chart, signal picker, time presets)
├── Diagrams (SVG viewer)
├── GIS Map
├── Alarms (table)
└── Edge Fleet (table)
```

---

## 3. Proposed Redesign — Phase Plan

### Phase R1: Foundation (Design Tokens + Icons) — 1 sprint

**Goal:** Establish the visual foundation before touching any page.

| Task | Description |
|------|-------------|
| R1.1 | Create `tokens.css` with semantic CSS variables |
| R1.2 | Replace all emoji icons with Lucide icons |
| R1.3 | Replace "MVP Preview" with version badge |
| R1.4 | Add data quality/freshness badge component |

**Design Tokens to create:**

```css
:root {
  /* Surfaces */
  --surface-primary: #0f172a;
  --surface-secondary: #1e293b;
  --surface-card: #1e293b;
  --surface-hover: #334155;

  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  /* Borders */
  --border-default: #334155;
  --border-subtle: #1e293b;

  /* Status */
  --status-normal: #22c55e;
  --status-warning: #eab308;
  --status-critical: #ef4444;
  --status-offline: #6b7280;
  --status-simulated: #a855f7;

  /* Accent */
  --accent-primary: #3b82f6;
  --accent-secondary: #06b6d4;

  /* Data Quality */
  --quality-good: #22c55e;
  --quality-uncertain: #eab308;
  --quality-bad: #ef4444;
  --quality-stale: #6b7280;
}
```

**Icon mapping (emoji → Lucide):**

| Current | Replace with |
|---------|-------------|
| 🏭 Overview | `LayoutDashboard` |
| 📋 Assets | `Boxes` |
| 📡 Signals | `Activity` |
| 📈 Historian | `LineChart` |
| 🗺️ Diagrams | `Workflow` |
| 🌍 GIS Map | `MapPin` |
| 🚨 Alarms | `Bell` |
| 🖥️ Edge Fleet | `Server` |

---

### Phase R2: Operational Overview — 1 sprint

**Goal:** Replace admin-focused Overview with operator-focused Plant Overview.

**New Overview layout:**

```
┌─────────────────────────────────────────────────────┐
│ Plant Health Bar                                    │
│ [✅ Normal] 3 areas OK | 1 warning | 0 critical     │
├──────────┬──────────┬──────────┬────────────────────┤
│ Production│ Quality  │ Energy   │ Active Alarms       │
│ 8,450 m³ │ 98.2%    │ 0.38     │ 2 (1 high, 1 med)  │
│ ▲ 2.1%   │ compliant│ kWh/m³   │                     │
├──────────┴──────────┴──────────┴────────────────────┤
│ Workflow / Process Units Diagram                     │
│ [Intake] → [Treatment] → [Distribution] → [Outlet]   │
│   ✅         ⚠️           ✅              ✅          │
├─────────────────────────────────────────────────────┤
│ Recent Alarms & Events                               │
│ 10:30 Filter-101 DP High         ⚠️ High             │
│ 10:15 Outlet Turbidity Warning   ⚠️ Medium           │
├─────────────────────────────────────────────────────┤
│ Trend Snapshot: Turbidity Chain (last 1h)            │
│ [mini trend chart]                                    │
└─────────────────────────────────────────────────────┘
```

**Remove from Overview:**
- Database stats → move to Data Foundation view
- Server resources → move to System Health page

---

### Phase R3: Navigation Redesign — 1 sprint

**Goal:** Organize pages by user role, not by data type.

**Proposed new navigation:**

```
┌─────────────────────┐
│ 🏭 PlantOS          │
├─────────────────────┤
│ 📊 Overview         │  ← operational overview
│ 🏗️ Operations       │  ← workflow diagram, area cockpit
│ ⚙️ Assets           │  ← asset registry + health
│ 📈 Trends           │  ← historian + trend bundles
│ 🚨 Alarms           │  ← active + history
├─────────────────────┤
│ 🧠 Intelligence     │  ← traceability, energy, cost
│ 📋 Reports          │  ← (future)
├─────────────────────┤
│ 🗄️ Data Foundation  │  ← signals, UNS, bindings
│ 🖥️ Edge & Sources   │  ← edge fleet, source health
│ ⚡ System           │  ← DB stats, server resources
├─────────────────────┤
│ ⚙️ Settings          │
└─────────────────────┘
```

**MVP simplification:** Keep current flat structure but reorganize into 3 groups:
1. **Monitor** — Overview, Operations (new), Trends, Alarms, GIS
2. **Assets** — Asset Registry, Diagrams
3. **Platform** — Data Foundation (signals), Edge Fleet, System

---

### Phase R4: Industrial Components — 1 sprint

**Goal:** Build reusable industrial widgets.

| Component | Description | Replaces |
|-----------|-------------|----------|
| `KpiCard` | Value + unit + trend + quality badge | Current stat cards |
| `StatusBadge` | Already exists — enhance with tooltip | Current badge |
| `DataQualityBadge` | Freshness + quality indicator | — |
| `AssetHealthBar` | Color-coded health summary | — |
| `WorkflowDiagram` | Block-based process flow | — |
| `TrendBundle` | Pre-configured multi-signal trend | Current manual picker |
| `AlarmTimeline` | Time-based alarm list | Current table |

---

### Phase R5: Page Refactoring — 2 sprints

Apply tokens + components to each page:

| Page | Changes |
|------|---------|
| Overview | Replace with operational layout (Phase R2 design) |
| Operations | New page: workflow diagram + area cockpit |
| Assets | Add health column, status colors |
| Trends | Add trend bundles, reduce raw picker prominence |
| Alarms | Add timeline view, severity colors |
| Diagrams | Keep current, add WTP workflow diagram |
| Edge Fleet | Done in recent fix — add hostname/IP |
| Data Foundation | New page: signal registry table (from current Signals page) |

---

## 4. What to NOT Change (Keep Working)

| Component | Reason |
|-----------|--------|
| Historian (TrendChart) | Functional, just fixed timezone/quality bugs |
| Workspace selector | Works correctly |
| Asset tree/table | Functional |
| Diagram SVG viewer | Works, just needs WTP diagram |
| Edge Fleet table | Just fixed |
| API layer (`api.ts`) | Clean, auth working |

---

## 5. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Breaking existing functionality | Phase approach — fix foundation first, pages last |
| Over-engineering for MVP | Keep navigation flat for now, skip Reports/Intelligence pages |
| Losing current users' familiarity | Keep all current pages accessible, add new views alongside |
| Token migration breaking colors | Use CSS variables with fallback values during transition |

---

## 6. Implementation Recommendation

**Start with Phase R1 only** (1 sprint, ~3-4 tasks):

```
R1.1: Create tokens.css with CSS variables
R1.2: Replace emoji icons with Lucide icons
R1.3: Add DataQualityBadge component
R1.4: Replace "MVP Preview" → version badge
```

This gives immediate visual improvement with zero functional risk. All other phases come after R1 is deployed and stable.

---

## 7. Prompt for Coder

When ready to implement, use this structure:

```markdown
# Phase R1 — Design Foundation

## Task R1.1 — CSS Design Tokens
Create `frontend/src/styles/tokens.css` with semantic variables.
Replace hardcoded Tailwind classes in Topbar, Sidebar, and Overview with tokens.

## Task R1.2 — Icon Replacement
Replace all emoji in Sidebar with Lucide icons.
Mapping: 🏭→LayoutDashboard, 📋→Boxes, 📡→Activity, etc.

## Task R1.3 — Data Quality Badge
Create `<DataQualityBadge quality={q} timestamp={ts} />` component.
Shows: green dot + "Good · 3s ago" or amber dot + "Stale · 5m ago"

## Task R1.4 — Header Cleanup
Replace "MVP Preview" text with version badge: "v0.1.0"
```

---

## 8. Summary

| Current State | Target State |
|---------------|-------------|
| Emoji icons | Lucide line icons |
| Hardcoded gray-900/800 | CSS tokens |
| Admin-focused Overview | Operator-focused Plant Overview |
| MVP Preview label | Version badge v0.1.0 |
| No data quality | Quality badges on values |
| Flat navigation | Grouped by role (later phases) |

**Recommendation:** Start Phase R1 now (low risk, high visual impact). Defer R2-R5 until after Phase 6 backlog and security hardening are fully validated.
