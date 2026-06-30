# Phase 1 — Task 12-13: Frontend Product Shell + Asset/Signal Pages (Gộp)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Reason for merge:** Shell là layout, Pages là nội dung đầu tiên. Gộp để test navigation + data flow end-to-end.

## Context

Xây dựng PlantOS Frontend Product Shell và 2 page đầu tiên (Asset + Signal). Đây là frontend foundation — thiết lập toàn bộ stack, design system, và data flow pattern cho các page sau.

**Nguyên tắc cốt lõi:** UI gọi PlantOS API — không query trực tiếp PostgreSQL, TDengine, MQTT hay Kafka.

## Plan Reference

- `docs/16-frontend-ux-design.md` — Shell, navigation, design system
- `docs/30-technology-stack.md` — Stack (React, Vite, Tailwind, shadcn/ui, TanStack)
- `docs/17-visualization-binding-spec.md` — Binding model (asset_signal, asset_state)
- `docs/14-api-contract-mvp.md` — API endpoints

## Technology Stack

```text
React 18 + TypeScript
Vite 6
Tailwind CSS 4
shadcn/ui (Radix UI primitives)
TanStack Query v5
TanStack Table v8
React Router v7
Lucide React (icons)
```

## Implementation Checklist

- [ ] CREATE Vite + React + TS project in `frontend/`
- [ ] CREATE `frontend/src/app/main.tsx` — entry point
- [ ] CREATE `frontend/src/app/App.tsx` — Shell + Router
- [ ] CREATE `frontend/src/app/providers.tsx` — QueryClient + Theme
- [ ] CREATE `frontend/src/components/layout/Shell.tsx` — sidebar + topbar + main
- [ ] CREATE `frontend/src/components/layout/Sidebar.tsx` — object-first navigation
- [ ] CREATE `frontend/src/components/layout/Topbar.tsx` — workspace title
- [ ] CREATE `frontend/src/components/StatusBadge.tsx` — status indicator
- [ ] CREATE `frontend/src/components/KpiCard.tsx` — metric card
- [ ] CREATE `frontend/src/lib/api.ts` — API client
- [ ] CREATE `frontend/src/routes/index.tsx` — route definitions
- [ ] CREATE `frontend/src/styles/globals.css` — Tailwind + design tokens
- [ ] CREATE `frontend/src/features/assets/AssetTable.tsx`
- [ ] CREATE `frontend/src/features/assets/AssetDetail.tsx`
- [ ] CREATE `frontend/src/features/assets/AssetFilters.tsx`
- [ ] CREATE `frontend/src/features/signals/SignalTable.tsx`
- [ ] CREATE `frontend/src/features/overview/OverviewPage.tsx`
- [ ] CREATE placeholder pages: Historian, Diagrams, GIS, Alarms, Edge Fleet

## Detailed Instructions

### 1. Project Setup

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install tailwindcss @tailwindcss/vite
npm install @tanstack/react-query @tanstack/react-table
npm install react-router-dom
npm install lucide-react
npx shadcn@latest init  # default style, neutral color, yes to CSS variables
npx shadcn@latest add button card table badge input select separator sheet
```

### 2. Design Tokens — `frontend/src/styles/globals.css`

```css
@import "tailwindcss";

@theme {
  --color-status-normal: #22c55e;
  --color-status-running: #3b82f6;
  --color-status-warning: #f59e0b;
  --color-status-alarm: #ef4444;
  --color-status-trip: #dc2626;
  --color-status-offline: #6b7280;
  --color-status-simulated: #8b5cf6;

  --color-severity-low: #3b82f6;
  --color-severity-medium: #f59e0b;
  --color-severity-high: #f97316;
  --color-severity-critical: #ef4444;
}

/* Dark mode as default */
:root {
  color-scheme: dark;
}

body {
  @apply bg-gray-950 text-gray-100 antialiased;
}
```

### 3. API Client — `frontend/src/lib/api.ts`

```typescript
const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API ${res.status}`);
  }
  return res.json();
}

// ---- Plants ----
export const getPlants = () => fetchAPI<any[]>("/api/v1/plants");

// ---- Assets ----
export const getAssets = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/assets${qs}`);
};
export const getAsset = (id: string) => fetchAPI<any>(`/api/v1/assets/${id}`);

// ---- Signals ----
export const getSignals = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/api/v1/signals${qs}`);
};

// ---- Measurements ----
export const getCurrentValues = (params: Record<string, string>) => {
  const qs = "?" + new URLSearchParams(params).toString();
  return fetchAPI<any[]>(`/api/v1/measurements/current${qs}`);
};
```

### 4. Shell Layout — `frontend/src/components/layout/Shell.tsx`

```tsx
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function Shell() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

### 5. Sidebar — Object-first Navigation

```tsx
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Wrench, Radio, ChartLine, MapPin,
  GitBranch, Bell, Plug, Settings
} from "lucide-react";

const navItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/assets", label: "Assets", icon: Wrench },
  { to: "/signals", label: "Signals", icon: Radio },
  { to: "/historian", label: "Historian", icon: ChartLine },
  { to: "/diagrams", label: "Diagrams", icon: GitBranch },
  { to: "/gis", label: "GIS Map", icon: MapPin },
  { to: "/alarms", label: "Alarms", icon: Bell },
  { to: "/edge", label: "Edge Fleet", icon: Plug },
];

export function Sidebar() {
  return (
    <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="h-14 flex items-center px-4 border-b border-gray-800">
        <span className="text-lg font-bold tracking-tight">🏭 PlantOS</span>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800/50"
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-gray-800 text-xs text-gray-600">
        PlantOS v0.1.0
      </div>
    </aside>
  );
}
```

### 6. Topbar

```tsx
export function Topbar() {
  return (
    <header className="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-gray-900/50">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Workspace:</span>
        <span className="text-sm font-medium">DEMO-PLANT</span>
      </div>
      <div className="text-xs text-gray-600">MVP Preview</div>
    </header>
  );
}
```

### 7. StatusBadge Component

```tsx
const statusColors: Record<string, string> = {
  active: "bg-status-normal/20 text-status-normal",
  running: "bg-status-running/20 text-status-running",
  warning: "bg-status-warning/20 text-status-warning",
  alarm: "bg-status-alarm/20 text-status-alarm",
  offline: "bg-status-offline/20 text-status-offline",
  simulated: "bg-status-simulated/20 text-status-simulated",
  inactive: "bg-gray-800 text-gray-500",
};

export function StatusBadge({ status }: { status: string }) {
  const color = statusColors[status] || statusColors.inactive;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}
```

### 8. Asset Table Page

```tsx
// features/assets/AssetTable.tsx
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getAssets } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { AssetFilters } from "./AssetFilters";

export function AssetTable() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const params: Record<string, string> = {};
  searchParams.forEach((v, k) => { params[k] = v; });

  const { data: assets, isLoading } = useQuery({
    queryKey: ["assets", params],
    queryFn: () => getAssets(params),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Assets</h1>
        <span className="text-sm text-gray-500">{assets?.length || 0} assets</span>
      </div>

      <AssetFilters />

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Asset ID</th>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Area</th>
                <th className="text-left px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {assets?.map((a: any) => (
                <tr
                  key={a.asset_id}
                  className="hover:bg-gray-800/50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/assets/${a.asset_id}`)}
                >
                  <td className="px-4 py-3 font-mono text-xs">{a.asset_id}</td>
                  <td className="px-4 py-3">{a.name}</td>
                  <td className="px-4 py-3 text-gray-400">{a.asset_type}</td>
                  <td className="px-4 py-3 text-gray-400">{a.area_id || "—"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={a.lifecycle_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### 9. Asset Filters

```tsx
// features/assets/AssetFilters.tsx
import { useSearchParams } from "react-router-dom";

export function AssetFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const setFilter = (key: string, value: string) => {
    if (value) searchParams.set(key, value);
    else searchParams.delete(key);
    setSearchParams(searchParams);
  };

  return (
    <div className="flex gap-3">
      <select
        className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm"
        onChange={(e) => setFilter("asset_type", e.target.value)}
        value={searchParams.get("asset_type") || ""}
      >
        <option value="">All Types</option>
        <option value="pump">Pump</option>
        <option value="motor">Motor</option>
        <option value="tank">Tank</option>
        <option value="valve">Valve</option>
        <option value="transformer">Transformer</option>
        <option value="feeder">Feeder</option>
        <option value="breaker">Breaker</option>
      </select>
      <select
        className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm"
        onChange={(e) => setFilter("area_id", e.target.value)}
        value={searchParams.get("area_id") || ""}
      >
        <option value="">All Areas</option>
        <option value="PROCESS-AREA">Process Area</option>
        <option value="ELECTRICAL-AREA">Electrical Area</option>
      </select>
    </div>
  );
}
```

### 10. Asset Detail Page

```tsx
// features/assets/AssetDetail.tsx
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAsset, getSignals, getCurrentValues } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export function AssetDetail() {
  const { assetId } = useParams<{ assetId: string }>();

  const { data: asset } = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => getAsset(assetId!),
    enabled: !!assetId,
  });

  const { data: signals } = useQuery({
    queryKey: ["signals", assetId],
    queryFn: () => getSignals({ asset_id: assetId! }),
    enabled: !!assetId,
  });

  const { data: currentValues } = useQuery({
    queryKey: ["current", assetId],
    queryFn: () => getCurrentValues({ asset_id: assetId! }),
    enabled: !!assetId,
    refetchInterval: 5000, // refresh every 5s
  });

  if (!asset) return <div className="text-gray-500">Loading...</div>;

  const currentMap = new Map(currentValues?.map((c: any) => [c.signal_id, c]) || []);

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Link to="/assets" className="text-gray-500 hover:text-white text-sm">← Assets</Link>
        <h1 className="text-2xl font-bold">{asset.name}</h1>
        <StatusBadge status={asset.lifecycle_status} />
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Asset ID</div>
          <div className="font-mono text-sm mt-1">{asset.asset_id}</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Type</div>
          <div className="text-sm mt-1 capitalize">{asset.asset_type}</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Area</div>
          <div className="text-sm mt-1">{asset.area_id || "—"}</div>
        </div>
      </div>

      {/* Current Values */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Current Values</h2>
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-2">Signal</th>
                <th className="text-right px-4 py-2">Value</th>
                <th className="text-left px-4 py-2">Quality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {signals?.map((s: any) => {
                const cv = currentMap.get(s.signal_id);
                return (
                  <tr key={s.signal_id}>
                    <td className="px-4 py-2 font-mono text-xs">{s.signal_name}</td>
                    <td className="px-4 py-2 text-right">
                      {cv ? (
                        <span>
                          {cv.value} {s.engineering_unit && <span className="text-gray-500">{s.engineering_unit}</span>}
                        </span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      {cv && <StatusBadge status={cv.quality?.toLowerCase()} />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Signals List */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Signals ({signals?.length || 0})</h2>
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-2">Signal ID</th>
                <th className="text-left px-4 py-2">Name</th>
                <th className="text-left px-4 py-2">Type</th>
                <th className="text-left px-4 py-2">Unit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {signals?.map((s: any) => (
                <tr key={s.signal_id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-2 font-mono text-xs">{s.signal_id}</td>
                  <td className="px-4 py-2">{s.display_name || s.signal_name}</td>
                  <td className="px-4 py-2 text-gray-400">{s.data_type}</td>
                  <td className="px-4 py-2 text-gray-400">{s.engineering_unit || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
```

### 11. Signal Table Page

```tsx
// features/signals/SignalTable.tsx
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { getSignals } from "@/lib/api";

export function SignalTable() {
  const [searchParams] = useSearchParams();
  const params: Record<string, string> = {};
  searchParams.forEach((v, k) => { params[k] = v; });

  const { data: signals, isLoading } = useQuery({
    queryKey: ["signals-all", params],
    queryFn: () => getSignals(params),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Signals</h1>
        <span className="text-sm text-gray-500">{signals?.length || 0} signals</span>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Signal ID</th>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Asset</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Unit</th>
                <th className="text-left px-4 py-3">UNS Path</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {signals?.map((s: any) => (
                <tr key={s.signal_id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-mono text-xs">{s.signal_id}</td>
                  <td className="px-4 py-3">{s.display_name || s.signal_name}</td>
                  <td className="px-4 py-3 text-gray-400">{s.asset_id}</td>
                  <td className="px-4 py-3 text-gray-400">{s.data_type}</td>
                  <td className="px-4 py-3 text-gray-400">{s.engineering_unit || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.uns_path || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### 12. Overview Dashboard

```tsx
// features/overview/OverviewPage.tsx
import { useQuery } from "@tanstack/react-query";
import { getAssets, getSignals } from "@/lib/api";
import { Wrench, Radio, Plug } from "lucide-react";

function KpiCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}

export function OverviewPage() {
  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: () => getAssets() });
  const { data: signals } = useQuery({ queryKey: ["signals-all"], queryFn: () => getSignals() });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Overview</h1>
      <div className="grid grid-cols-3 gap-4">
        <KpiCard icon={Wrench} label="Assets" value={assets?.length || 0} color="bg-blue-500/20 text-blue-400" />
        <KpiCard icon={Radio} label="Signals" value={signals?.length || 0} color="bg-purple-500/20 text-purple-400" />
        <KpiCard icon={Plug} label="Edge Nodes" value="1" color="bg-green-500/20 text-green-400" />
      </div>
    </div>
  );
}
```

### 13. Routes — `frontend/src/routes/index.tsx`

```tsx
import { createBrowserRouter } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { OverviewPage } from "@/features/overview/OverviewPage";
import { AssetTable } from "@/features/assets/AssetTable";
import { AssetDetail } from "@/features/assets/AssetDetail";
import { SignalTable } from "@/features/signals/SignalTable";

// Placeholder pages (skeleton)
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-gray-600">
      <div className="text-center">
        <div className="text-4xl mb-3">🚧</div>
        <div className="text-lg">{title}</div>
        <div className="text-sm mt-1">Coming in next phase</div>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Shell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "assets", element: <AssetTable /> },
      { path: "assets/:assetId", element: <AssetDetail /> },
      { path: "signals", element: <SignalTable /> },
      { path: "historian", element: <PlaceholderPage title="Historian" /> },
      { path: "diagrams", element: <PlaceholderPage title="Diagrams" /> },
      { path: "gis", element: <PlaceholderPage title="GIS Map" /> },
      { path: "alarms", element: <PlaceholderPage title="Alarms" /> },
      { path: "edge", element: <PlaceholderPage title="Edge Fleet" /> },
    ],
  },
]);
```

### 14. App & Providers

`frontend/src/app/providers.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5000, retry: 1 },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

`frontend/src/app/App.tsx`:
```tsx
import { RouterProvider } from "react-router-dom";
import { router } from "@/routes";
import { Providers } from "./providers";

export function App() {
  return (
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  );
}
```

`frontend/src/app/main.tsx`:
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "@/styles/globals.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### 15. Vite Config

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

### 16. Update `frontend/package.json`

```json
{
  "name": "plantos-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

### 17. Update `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS development
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

## Constraints

- [x] UI KHÔNG query trực tiếp PostgreSQL, TDengine, MQTT, Kafka — tất cả qua `/api/v1`
- [x] Navigation object-first (Assets, Signals, Historian...) — không có mục TDengine, MQTT
- [x] Dark mode mặc định (industrial calm)
- [x] Không hardcode asset/signal names trong UI code — đọc từ API
- [x] Không business logic trong component — chỉ fetch + render
- [x] Vite proxy `/api` → backend (dev mode)

## Validation

```bash
# 1. Start backend + PostgreSQL
docker compose -f deployment/docker-compose.yml up -d postgres
cd backend && alembic upgrade head && uvicorn app.main:app --port 8000 &

# 2. Seed data
python scripts/seed_demo_plant.py

# 3. Start frontend
cd frontend && npm install && npm run dev

# 4. Open http://localhost:5173
# Verify: sidebar shows 8 nav items
# Verify: Overview shows KPI cards with counts
# Verify: Assets page shows 9 assets with filters
# Verify: Click asset → detail page with current values + signals
# Verify: Signals page shows 15 signals
```

## Expected Output Format

```
Standard — như các task trước.
Đặc biệt: screenshot xác nhận UI hiển thị đúng + không bypass API.
```
