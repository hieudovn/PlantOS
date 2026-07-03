# PlantOS Center — Frontend Design Specification

> **Version:** v0.1.0 | **Date:** 2026-07-03 | **For:** External AI Model Review  
> **Purpose:** Complete UI/UX design description for the PlantOS Center web application. Use this document to critique, suggest improvements, and propose additions.

---

## 1. Product Context

PlantOS is an **Industrial Operational Platform** for managing water treatment plants (WTP), compressor stations, and similar industrial facilities. The Center is the web-based dashboard used by operators, engineers, and managers to monitor plants, visualize time-series data, manage assets/signals, and track alarms.

**Current Scope (MVP):** Single-plant demo with 2 reference models — WTP-DEMO-01 (Water Treatment, 92 signals, 47 assets) and VF-DEMO (Compressor, 12 signals).

---

## 2. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | React | 18 |
| Routing | React Router | v7 |
| CSS | Tailwind CSS v4 (CSS-based config, no `tailwind.config.js`) | 4 |
| UI Primitives | Radix UI (select, separator, slot) | latest |
| Icons | Lucide React | latest |
| Data Fetching | TanStack React Query | v5 |
| Tables | TanStack React Table | v8 |
| Charts | Apache ECharts via `echarts-for-react` | 6 |
| Maps | Leaflet + react-leaflet | latest |
| Build | Vite | 6 |

---

## 3. Design System — Tokens & Theme

### 3.1 Color Scheme

**Dark theme only.** No light mode exists. Colors are defined in two layers:

**Layer 1 — CSS Custom Properties on `:root`** (used via `var(--token)` inline styles):
```css
:root {
  color-scheme: dark;

  /* Surfaces */
  --surface-primary: #0f172a;    /* slate-900 — sidebar bg */
  --surface-secondary: #1e293b;  /* slate-800 — topbar bg */
  --surface-card: #1e293b;       /* slate-800 — card bg */
  --surface-hover: #334155;      /* slate-700 — hover state */

  /* Text */
  --text-primary: #f1f5f9;      /* slate-100 — main text */
  --text-secondary: #94a3b8;    /* slate-400 — secondary text */
  --text-muted: #64748b;         /* slate-500 — muted/placeholder */

  /* Borders */
  --border-default: #334155;     /* slate-700 */
  --border-subtle: #1e293b;     /* slate-800 */

  /* Status — semantic colors */
  --status-normal: #22c55e;      /* green-500  — operational */
  --status-warning: #eab308;     /* yellow-500 — warning */
  --status-critical: #ef4444;    /* red-500    — critical */
  --status-offline: #6b7280;     /* gray-500   — offline */
  --status-simulated: #a855f7;   /* purple-500 — simulated data */

  /* Data Quality */
  --quality-good: #22c55e;
  --quality-uncertain: #eab308;
  --quality-bad: #ef4444;
  --quality-stale: #6b7280;

  /* Accent */
  --accent-primary: #3b82f6;     /* blue-500 */
  --accent-secondary: #06b6d4;   /* cyan-500 */
}
```

**Layer 2 — Tailwind `@theme`** (extends Tailwind utility classes):
```css
@theme {
  --color-status-normal: #22c55e;
  --color-status-running: #3b82f6;
  --color-status-warning: #f59e0b;     /* NOTE: differs from :root (#eab308) */
  --color-status-alarm: #ef4444;
  --color-status-trip: #dc2626;
  --color-status-offline: #6b7280;
  --color-status-simulated: #8b5cf6;   /* NOTE: differs from :root (#a855f7) */

  --color-severity-low: #3b82f6;
  --color-severity-medium: #f59e0b;
  --color-severity-high: #f97316;
  --color-severity-critical: #ef4444;
}
```

**Known issue:** `--status-warning` and `--status-simulated` have different hex values between `:root` CSS vars and `@theme` Tailwind classes. The `:root` value wins for inline styles, `@theme` wins for `text-status-*` utility classes.

### 3.2 Typography

**No custom font.** Uses Tailwind v4 default system font stack:
- **Sans-serif:** `ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"`
- **Monospace:** `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`

No `@font-face`, no Google Fonts, no CDN font links. No Inter, Roboto, or industry-specific fonts.

**Font sizes used across the UI:** `text-xs` (12px), `text-sm` (14px), `text-base` (16px), `text-xl` (20px), `text-2xl` (24px), `text-[28px]` (KPI values previously, now reduced to `text-xl` in compact mode).

### 3.3 Spacing & Borders

- **Border radius:** Tailwind `rounded` (4px) for inputs/buttons, `rounded-lg` (8px) for cards
- **Card padding:** `p-4` to `p-6` (16-24px)
- **Main content padding:** `p-6` (24px)
- **Gap between elements:** `gap-3` or `gap-4` (12-16px)
- **Border color:** `var(--border-default)` = `#334155`

### 3.4 Icons

**All icons from Lucide React.** No custom SVG icons. Examples:
- `LayoutDashboard`, `LineChart`, `Workflow`, `MapPin`, `Bell` (navigation)
- `CheckCircle`, `AlertTriangle`, `XCircle`, `Pause` (status)
- `Activity`, `ExternalLink`, `LogOut`, `Plus`, `X`, `Circle`
- `Database`, `Cpu`, `HardDrive` (system metrics)

All icons sized `w-4 h-4` or `w-5 h-5`. No icon scaling. No icon animations except spinner.

---

## 4. Layout Architecture

### 4.1 Shell Layout

```
┌──────────┬──────────────────────────────────────────┐
│          │  TOPBAR (h-14 = 56px)                    │
│          │  bg: surface-secondary                    │
│ SIDEBAR  ├──────────────────────────────────────────┤
│          │                                          │
│ w-60     │  MAIN CONTENT                           │
│ (240px)  │  (flex-1, overflow-auto, p-6)           │
│          │                                          │
│ bg:      │  <Outlet /> — page component             │
│ surface- │                                          │
│ primary  │                                          │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

- **Root container:** `flex h-screen overflow-hidden`
- **Sidebar:** fixed `w-60` (240px), no collapse, no responsive breakpoint
- **Right area:** `flex flex-1 flex-col overflow-hidden`
- **Main scrollable area:** `flex-1 overflow-auto p-6`

### 4.2 Routing

```
/login          → LoginPage (standalone, no shell)
/               → OverviewPage (Operations Cockpit, index route)
/assets         → AssetTable
/assets/:id     → AssetDetail
/signals        → SignalTable
/historian      → HistorianPage
/diagrams       → DiagramPage
/gis            → GisMapPage
/alarms         → AlarmPage
/edge           → EdgeFleetPage
/system         → SystemHealthPage
```

All routes except `/login` are children of `<Shell />`. Route guard: if no JWT token in localStorage, API calls receive 401 and redirect to `/login`.

---

## 5. Navigation — Sidebar

### 5.1 Structure

Two grouped sections with uppercase section headers:

| Section | Items | Route | Icon |
|---------|-------|-------|------|
| **MONITOR** | Overview | `/` | LayoutDashboard |
| | Historian | `/historian` | LineChart |
| | Diagrams | `/diagrams` | Workflow |
| | GIS Map | `/gis` | MapPin |
| | Alarms | `/alarms` | Bell |
| **PLATFORM** | Assets | `/assets` | Boxes |
| | Signals | `/signals` | Activity |
| | Edge Fleet | `/edge` | Server |
| | System | `/system` | Monitor |

### 5.2 Styling

- **Active item:** `bg-[var(--surface-hover)]` + `text-white` + border-left accent
- **Inactive item:** `text-[var(--text-secondary)]`, hover → `text-white`
- **Icon size:** `w-4 h-4`
- **Section headers:** `text-xs text-[var(--text-muted)] tracking-wide uppercase`
- **Footer:** "PlantOS v0.1.0" in `text-xs text-[var(--text-muted)]`

---

## 6. Navigation — Topbar

### 6.1 Left Side
- **"Workspace:" label** + `<select>` dropdown for plant selection
- Select styled: `bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white`
- Plants loaded from API `/api/v1/plants`, selection persisted to localStorage

### 6.2 Right Side
1. **Data Freshness indicator:** colored dot (`Circle` icon) + "Live" text
   - Green (`--status-normal`) if data age < 30s
   - Yellow (`--status-warning`) if 30-120s
   - Red (`--status-critical`) if > 120s
2. **Active Alarms badge:** bell icon + count (only shown if > 0)
3. **Username** display (from localStorage)
4. **Logout button** (clears token, redirects to `/login`)
5. **Version badge:** `v0.1.0` in mono font with border

---

## 7. Feature Pages — Detailed Description

### 7.1 Operations Cockpit (`OverviewPage`)

**Purpose:** Dashboard-style overview of a plant's current operational state.

**Layout:** Vertical stack with 3 rows

**Row 1 — KPI Cards** (5 columns, `grid grid-cols-5 gap-3`):
| Card | Content |
|------|---------|
| Plant Health | Status label + icon (CheckCircle/AlertTriangle/XCircle/Pause) |
| Production | Flow rate in m³/h, with trend arrow |
| Water Quality | Quality index, compliance status |
| Cost | VND/m³ |
| Active Alarms | Count with severity color |

All KPI cards use `compact` mode: value in `text-xl`, icon in header. Status colors applied to left border.

**Row 2 — Process + Incidents** (12-column split):
- Left 8 cols: `WorkflowDiagram` (visual process flow for WTP-DEMO-01 with 6 stages: Intake → Dosing → Clarifier → Filters → Disinfection → Distribution). Each stage shows status color and KPIs.
- Right 4 cols: "Active Incidents" panel — shows "No active incidents" when alarm count = 0.

**Row 3 — Quick Values** (2 columns):
- Left: "Water Quality" section — Raw/Settled/Filtered/Outlet Turbidity, Free Chlorine, Filter DP. Each value has status dot and deep-link to Historian via `?signal=ID`.
- Right: "Energy & Cost" section — Production Flow, Specific Energy, Energy Cost, Quality Index, Compliance.

**Data refresh:** Each signal value refreshed every 10s via `useQuery({ refetchInterval: 10000 })`.

### 7.2 Historian (`HistorianPage`)

**Purpose:** Time-series data visualization with multi-chart panels.

**Top controls:**
- **From/To:** `<input type="datetime-local">` for time range
- **Presets:** 10m, 30m, 1h, 6h, 12h (auto-refresh every 10s when preset is active)
- **Chart type:** Line, Bar, Scatter, Area (select dropdown)
- **Signal count display**
- **Live indicator** (green pulse dot) when preset is active

**Panel system:**
- Tab-based multi-chart (Add Chart button, each chart is a tab)
- Each tab has: editable label, close button
- Up to N parallel charts, each with independent signal selection

**Chart rendering:** `TrendChart` component using Apache ECharts.
- `xAxis: { type: "time" }` — time-series axis
- Series per signal with distinct colors from palette: `#3b82f6`, `#22c55e`, `#f59e0b`, `#8b5cf6`, `#ef4444`, `#06b6d4`, `#f97316`, `#ec4899`
- Good data: line/area/bar; Bad quality data: scatter overlay with opacity
- Compact mode: hides toolbox, reduces grid margins, disables slider
- Default height: 500px (configurable via `height` prop)
- `VALID_QUALITIES`: GOOD, SIMULATED, ESTIMATED

**Signal selector:** `SignalMultiSelect` — combobox with search, filtered by plant selection.

**State persistence:** Time range, presets, panels, chart type saved to `localStorage`.

**Deep-link:** URL parameter `?signal=ID` auto-adds signal to active panel.

### 7.3 Diagrams (`DiagramPage`)

**Purpose:** SVG-based P&ID and process diagrams with live value binding.

**Current diagrams:**
- VF-DEMO: P&ID Process Line 01, One-Line Electrical
- WTP-DEMO-01: WTP Process Flow

**How it works:**
- Static SVG loaded from `/diagrams/{id}.svg`
- Binding YAML file at `/diagrams/{id}.binding.yaml` maps SVG elements to signal values
- Binding format: `signals` (asset_id + signal_name + format + unit), `states`, `state_styles`, `refresh_interval_ms`
- Plant detection via `useWorkspace()` context

**Rendering:** `SvgDiagram` component parses SVG DOM, injects live values into bound elements, applies state colors.

### 7.4 GIS Map (`GisMapPage`)

**Purpose:** Geographic visualization of plant/assets on a map.

**Technology:** Leaflet + react-leaflet. OpenStreetMap tiles.

**Current state:** Basic map rendering. No asset markers, no signal overlay. Placeholder.

### 7.5 Alarms (`AlarmPage`)

**Purpose:** Alarm management — list, filter, acknowledge.

**Current state:** Basic alarm list from `/api/v1/alarms`. Filter by state (active/acknowledged/cleared). Table view.

### 7.6 Assets (`AssetTable` + `AssetDetail`)

**Purpose:** Browse plant asset hierarchy.

**AssetTable:** TanStack React Table with columns: Name, Asset Type, Area, Status. Filterable, sortable.

**AssetDetail:** Single asset view with metadata, linked signals, status history.

**AssetTree:** Hierarchical tree view showing parent-child asset relationships.

### 7.7 Signals (`SignalTable`)

**Purpose:** Browse and search all signals across the plant.

**Columns:** Signal ID, Name, Asset, Unit, Current Value, Quality, Last Update. Filterable by plant, asset, search text. TanStack React Table.

### 7.8 Edge Fleet (`EdgeFleetPage`)

**Purpose:** Monitor Edge Agent health and connectivity.

**Content:** List of edge nodes with: hostname, IP, signal count, last heartbeat, status. Data from `/api/v1/edge-nodes`. Node detail panel on click.

### 7.9 System Health (`SystemHealthPage`)

**Purpose:** Infrastructure monitoring dashboard.

**Section 1 — Database:**
- Total DB Size (PG + Historian in MB)
- PG Records (breakdown by table: plants, areas, assets, signals, alarms, events, edge_nodes)
- Historian Records (measurement count from TDengine)
- Historian DB (health status: Connected/No data)

**Section 2 — Server Resources:**
- CPU (% + core count)
- RAM (% + used/total in GB)
- Disk (% + used/total in GB)

**Refresh:** Every 30s. Cards use colored icon backgrounds (cyan, teal, orange, yellow, red).

### 7.10 Login (`LoginPage`)

**Purpose:** Authentication.

**Layout:** Centered card with PlantOS branding, Username + Password fields, Login button. Hardcoded users (admin/engineer) with bcrypt hashed passwords stored in backend code.

---

## 8. Reusable Components

### 8.1 `KpiCard`

```tsx
Props: {
  label: string;           // Card title
  value: string | number;  // Main value
  unit?: string;           // Unit suffix
  state?: "normal" | "warning" | "critical" | "offline";
  trend?: "up" | "down";
  trendLabel?: string;
  quality?: string;         // Data quality indicator
  timestamp?: string;
  icon?: JSX.Element;       // Header icon (Lucide)
  compact?: boolean;        // Compact mode: text-xl instead of text-[28px]
}
```

**Visual:** Card with label (top-left, muted text), icon (top-right), large value, unit, sub-line with quality/timestamp/trend. Left border colored by state.

### 8.2 `TrendChart`

ECharts wrapper. Props: `signalIds`, `from`, `to`, `chartType`, `showLegend`, `showToolbox`, `refetchInterval`, `height`, `compact`.

### 8.3 `TrendBundle`

Groups multiple `TrendChart` instances. Passes `compact` and `height` props.

### 8.4 `WorkflowDiagram`

Visual process flow diagram showing stages with status colors and KPI overlays.

### 8.5 `StatusBadge`

Colored badge pill for status values (normal/running/warning/critical/offline/simulated).

---

## 9. Data Flow & State Management

### 9.1 Authentication
- JWT token stored in `localStorage.plantos_token`
- API key fallback: `VITE_API_KEY` env var sent as `X-API-Key` header when no JWT
- Token refresh via `X-New-Token` response header
- 401 → clear token → redirect `/login`

### 9.2 Plant/Workspace
- `WorkspaceContext` provider wraps entire app
- Plant list fetched from `/api/v1/plants` once on mount
- Selected plant persisted to `localStorage.plantos_plant_id`
- Re-fetched on custom `auth-login` DOM event

### 9.3 Server State (React Query)
- Default: `staleTime: 5000ms`, `retry: 1`
- Per-component `refetchInterval` for live data (5s to 30s depending on component)
- No global cache invalidation strategy

### 9.4 Client State (localStorage)
- Historian state: time range, presets, panels, chart type
- Plant selection
- Auth token, username

---

## 10. Known Issues & Gaps

### 10.1 Design System
- **No typography scale** — font sizes chosen ad-hoc per component (text-xs, text-sm, text-base, text-xl, text-2xl, text-[28px]).
- **Inconsistent token values** — `--status-warning` and `--status-simulated` differ between `:root` and `@theme`.
- **`tokens.css` is dead code** — not imported anywhere, duplicate of `globals.css`.
- **No spacing/sizing token system** — no `--space-*`, `--size-*`, `--radius-*` tokens.
- **No light theme** — `color-scheme: dark` only. No media query support.
- **No component library** — KpiCard, StatusBadge are inline-defined, not documented via Storybook (storybook folder exists but appears unused).

### 10.2 Accessibility
- No ARIA labels on icon-only buttons
- No keyboard navigation for sidebar
- No focus visible indicators on most interactive elements
- No screen reader support for chart content

### 10.3 Responsive Design
- **None.** No mobile/tablet breakpoints. Sidebar fixed at 240px. Grids hardcoded (grid-cols-5, grid-cols-12). No responsive menu. On narrow screens, content overflows.

### 10.4 Feature Gaps
- **GIS:** Placeholder only — no asset markers
- **Alarms:** Basic list — no acknowledge workflow, no notification, no alarm rules UI
- **Diagrams:** Only 1 diagram per plant, no zoom/pan, no interaction beyond value binding
- **Edge Fleet:** Read-only display, no remote management
- **Historian:** No data export, no annotation, no threshold lines on chart, no comparison mode
- **System:** No alerting on resource thresholds, no log viewer

### 10.5 UX Polish
- No loading skeletons — only text "Loading..."
- No empty states designed for most pages
- No error boundaries
- No confirmation dialogs for destructive actions
- No toast/notification system
- Chart tooltip uses ECharts default (no custom formatting)
- No breadcrumb navigation
- No page transition animations

---

## 11. File Inventory

```
frontend/
├── index.html                          # Shell HTML, no external fonts/resources
├── package.json                        # Dependencies
├── vite.config.ts                      # Build config, proxy
├── tsconfig.json                       # TypeScript config
├── src/
│   ├── app/
│   │   ├── main.tsx                    # Entry point
│   │   ├── App.tsx                     # Root component
│   │   └── providers.tsx              # QueryClient + Workspace providers
│   ├── styles/
│   │   ├── globals.css                 # Active stylesheet — all design tokens
│   │   └── tokens.css                  # Dead file — duplicate of globals.css
│   ├── routes/
│   │   └── index.tsx                   # Route definitions
│   ├── lib/
│   │   ├── api.ts                      # fetchAPI wrapper + endpoint functions
│   │   └── WorkspaceContext.tsx        # Plant selection context
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Shell.tsx              # App shell layout
│   │   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   │   └── Topbar.tsx             # Top bar with workspace selector
│   │   ├── industrial/
│   │   │   ├── KpiCard.tsx            # KPI metric card
│   │   │   └── TrendBundle.tsx        # Trend chart wrapper
│   │   ├── diagrams/
│   │   │   └── WorkflowDiagram.tsx    # Process flow diagram
│   │   └── StatusBadge.tsx            # Status badge component
│   └── features/
│       ├── auth/
│       │   └── LoginPage.tsx          # Login page
│       ├── overview/
│       │   └── OverviewPage.tsx       # Operations Cockpit
│       ├── historian/
│       │   ├── HistorianPage.tsx      # Historian page
│       │   ├── TrendChart.tsx         # ECharts chart component
│       │   └── SignalMultiSelect.tsx  # Signal selector
│       ├── visualization/
│       │   ├── DiagramPage.tsx        # Diagram viewer
│       │   ├── SvgDiagram.tsx         # SVG renderer with binding
│       │   └── GisMapPage.tsx         # GIS map (Leaflet)
│       ├── assets/
│       │   ├── AssetTable.tsx         # Asset list
│       │   ├── AssetDetail.tsx        # Asset detail view
│       │   └── AssetTree.tsx          # Asset hierarchy tree
│       ├── signals/
│       │   └── SignalTable.tsx        # Signal list
│       ├── alarms/
│       │   └── AlarmPage.tsx          # Alarm management
│       ├── edge-fleet/
│       │   └── EdgeFleetPage.tsx      # Edge fleet status
│       └── system/
│           └── SystemHealthPage.tsx   # System health metrics
```

---

## 12. Appendix: Color Palette Reference

```
Slate Scale (surfaces + text):
  #0f172a  slate-900   — sidebar, body bg
  #1e293b  slate-800   — topbar, cards
  #334155  slate-700   — borders, hover
  #475569  slate-600   — (unused)
  #64748b  slate-500   — text-muted
  #94a3b8  slate-400   — text-secondary
  #cbd5e1  slate-300   — (unused)
  #f1f5f9  slate-100   — text-primary

Accent:
  #3b82f6  blue-500    — accent-primary (links, active states)
  #06b6d4  cyan-500    — accent-secondary

Status:
  #22c55e  green-500   — normal, good, operational
  #eab308  yellow-500  — warning (CSS var)
  #f59e0b  amber-500   — warning (Tailwind)
  #ef4444  red-500     — critical, alarm
  #6b7280  gray-500    — offline
  #a855f7  purple-500  — simulated (CSS var)
  #8b5cf6  violet-500  — simulated (Tailwind)

Severity:
  #3b82f6  blue-500    — low
  #f59e0b  amber-500   — medium
  #f97316  orange-500  — high
  #ef4444  red-500     — critical

Chart Series Colors:
  #3b82f6, #22c55e, #f59e0b, #8b5cf6, #ef4444, #06b6d4, #f97316, #ec4899
```
