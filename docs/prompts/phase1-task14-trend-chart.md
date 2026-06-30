# Phase 1 — Task 14: Trend Chart Mở Rộng (Multi-Signal + Search)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Historian page đầy đủ: multi-chart tab panels, multi-signal trên 1 chart, signal selector searchable, search cho Asset/Signal tables.

## Implementation Checklist

- [ ] INSTALL `echarts` + `echarts-for-react`
- [ ] CREATE `frontend/src/features/historian/SignalMultiSelect.tsx`
- [ ] CREATE `frontend/src/features/historian/TrendChart.tsx`
- [ ] CREATE `frontend/src/features/historian/HistorianPage.tsx`
- [ ] MODIFY `frontend/src/lib/api.ts` — add `getHistory()`
- [ ] MODIFY `frontend/src/routes/index.tsx` — replace Historian placeholder
- [ ] MODIFY `frontend/src/features/assets/AssetTable.tsx` — add search input
- [ ] MODIFY `frontend/src/features/signals/SignalTable.tsx` — add search input

## Detailed Instructions

### 1. Install

```bash
cd frontend && npm install echarts echarts-for-react
```

### 2. `frontend/src/lib/api.ts` — Add

```typescript
export const getHistory = (params: Record<string, string>) => {
  const qs = "?" + new URLSearchParams(params).toString();
  return fetchAPI<any>(`/api/v1/measurements/history${qs}`);
};
```

### 3. `frontend/src/features/historian/SignalMultiSelect.tsx`

Searchable multi-select: gõ tên signal, asset_id, hoặc display_name để filter. Chọn nhiều signal bằng checkbox.

```tsx
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSignals } from "@/lib/api";
import { X, Search } from "lucide-react";

type Props = { selected: string[]; onChange: (ids: string[]) => void };

export function SignalMultiSelect({ selected, onChange }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const { data: signals } = useQuery({ queryKey: ["signals-all"], queryFn: () => getSignals() });

  const filtered = useMemo(() => {
    if (!signals) return [];
    const q = search.toLowerCase();
    return signals.filter((s: any) =>
      s.signal_id.toLowerCase().includes(q) ||
      (s.display_name || s.signal_name).toLowerCase().includes(q) ||
      s.asset_id.toLowerCase().includes(q)
    );
  }, [signals, search]);

  const toggle = (id: string) => {
    selected.includes(id) ? onChange(selected.filter(x => x !== id)) : onChange([...selected, id]);
  };
  const remove = (id: string) => onChange(selected.filter(x => x !== id));

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-1 mb-2">
        {selected.map(id => (
          <span key={id} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded text-xs">
            {id} <button onClick={() => remove(id)}><X className="w-3 h-3"/></button>
          </span>
        ))}
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"/>
        <input type="text" placeholder="Search signals by name, asset..." value={search}
          onChange={e => { setSearch(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          className="w-full bg-gray-900 border border-gray-700 rounded pl-10 pr-3 py-2 text-sm"/>
      </div>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-gray-900 border border-gray-700 rounded-lg shadow-xl max-h-64 overflow-auto">
          {filtered.length === 0
            ? <div className="px-3 py-4 text-sm text-gray-500 text-center">No signals found</div>
            : filtered.map((s: any) => (
              <label key={s.signal_id} className="flex items-center gap-3 px-3 py-2 hover:bg-gray-800 cursor-pointer text-sm">
                <input type="checkbox" checked={selected.includes(s.signal_id)} onChange={() => toggle(s.signal_id)} className="rounded"/>
                <span className="font-mono text-xs text-gray-400">{s.asset_id}</span>
                <span>{s.display_name || s.signal_name}</span>
                <span className="text-gray-600 text-xs ml-auto">{s.engineering_unit || "—"}</span>
              </label>
            ))}
        </div>
      )}
      {open && <div className="fixed inset-0 z-40" onClick={() => setOpen(false)}/>}
    </div>
  );
}
```

### 4. `frontend/src/features/historian/TrendChart.tsx`

Multi-series ECharts: mỗi signal 1 line với màu riêng. Bad quality points marked red scatter.

```tsx
import ReactECharts from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getHistory } from "@/lib/api";

const COLORS = ["#3b82f6","#22c55e","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#f97316","#ec4899"];

type Props = { signalIds: string[]; from: string; to: string };

export function TrendChart({ signalIds, from, to }: Props) {
  const queries = useQueries({
    queries: signalIds.map(sid => ({
      queryKey: ["history", sid, from, to],
      queryFn: () => getHistory({ signal_id: sid, from, to }),
      enabled: !!sid && !!from && !!to,
    })),
  });

  if (signalIds.length === 0) return <div className="text-gray-600 text-center py-16">Add signals to view trends</div>;
  if (!queries.every(q => !q.isLoading)) return <div className="text-gray-500 py-8">Loading...</div>;

  const series: any[] = [];
  signalIds.forEach((sid, i) => {
    const data = queries[i]?.data;
    const points = data?.data || [];
    if (points.length === 0) return;
    const good = points.filter((p: any) => !p.quality || p.quality === "GOOD");
    const bad = points.filter((p: any) => p.quality && p.quality !== "GOOD");
    series.push({ name: sid, type: "line", data: good.map((p: any) => [p.timestamp, p.value]), smooth: false, symbol: "none", lineStyle: { color: COLORS[i % COLORS.length], width: 1.5 } });
    if (bad.length > 0) series.push({ name: `${sid} (bad)`, type: "scatter", data: bad.map((p: any) => [p.timestamp, p.value]), symbolSize: 8, itemStyle: { color: COLORS[i % COLORS.length], opacity: 0.4 } });
  });

  const total = queries.reduce((s, q) => s + (q.data?.data?.length || 0), 0);

  const option = {
    backgroundColor: "transparent",
    legend: { data: signalIds, bottom: 0, textStyle: { color: "#9ca3af", fontSize: 11 } },
    grid: { top: 20, right: 40, bottom: 40, left: 70 },
    xAxis: { type: "time", axisLine: { lineStyle: { color: "#374151" } }, axisLabel: { color: "#9ca3af", fontSize: 11 } },
    yAxis: { type: "value", axisLine: { lineStyle: { color: "#374151" } }, axisLabel: { color: "#9ca3af", fontSize: 11 }, splitLine: { lineStyle: { color: "#1f2937" } } },
    tooltip: { trigger: "axis", backgroundColor: "#1f2937", borderColor: "#374151", textStyle: { color: "#e5e7eb", fontSize: 12 } },
    series,
  };

  return (
    <div>
      <div className="text-xs text-gray-500 mb-2">{total} data points</div>
      <ReactECharts option={option} style={{ height: 400 }} notMerge />
    </div>
  );
}
```

### 5. `frontend/src/features/historian/HistorianPage.tsx`

Tab layout: mỗi tab là 1 chart panel. Nút "+" thêm chart mới. Time range dùng chung.

```tsx
import { useState } from "react";
import { SignalMultiSelect } from "./SignalMultiSelect";
import { TrendChart } from "./TrendChart";
import { Plus, X } from "lucide-react";

function fmt(iso: string) { return iso.substring(0, 16); }

interface Panel { id: number; signalIds: string[]; label: string }

export function HistorianPage() {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const [from, setFrom] = useState(fmt(today.toISOString()));
  const [to, setTo] = useState(fmt(now.toISOString()));
  const [panels, setPanels] = useState<Panel[]>([{ id: 1, signalIds: [], label: "Chart 1" }]);
  const [active, setActive] = useState(0);

  const addPanel = () => {
    const id = Math.max(0, ...panels.map(p => p.id)) + 1;
    setPanels([...panels, { id, signalIds: [], label: `Chart ${id}` }]);
    setActive(panels.length);
  };
  const removePanel = (i: number) => {
    if (panels.length <= 1) return;
    const np = panels.filter((_, j) => j !== i);
    setPanels(np); setActive(Math.min(active, np.length - 1));
  };
  const updateSignals = (i: number, ids: string[]) => {
    const np = [...panels];
    np[i] = { ...np[i], signalIds: ids, label: ids.length > 0 ? ids[0].split(".").pop() || ids[0] : np[i].label };
    setPanels(np);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Historian</h1>
        <button onClick={addPanel} className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm"><Plus className="w-4 h-4"/> Add Chart</button>
      </div>
      <div className="flex gap-4 items-end">
        <div><label className="block text-xs text-gray-500 mb-1">From</label><input type="datetime-local" value={from} onChange={e => setFrom(e.target.value)} className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"/></div>
        <div><label className="block text-xs text-gray-500 mb-1">To</label><input type="datetime-local" value={to} onChange={e => setTo(e.target.value)} className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"/></div>
        <span className="text-xs text-gray-600">{panels.reduce((s,p) => s + p.signalIds.length, 0)} signals</span>
      </div>
      <div className="flex border-b border-gray-800 gap-1">
        {panels.map((p, i) => (
          <button key={p.id} onClick={() => setActive(i)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t ${i === active ? "bg-gray-900 border border-gray-800 border-b-transparent text-white" : "text-gray-500 hover:text-gray-300"}`}>
            {p.label}
            {panels.length > 1 && <span onClick={e => { e.stopPropagation(); removePanel(i); }} className="hover:text-red-400"><X className="w-3 h-3"/></span>}
          </button>
        ))}
      </div>
      <SignalMultiSelect selected={panels[active]?.signalIds || []} onChange={ids => updateSignals(active, ids)} />
      <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-4">
        <TrendChart signalIds={panels[active]?.signalIds || []} from={new Date(from).toISOString()} to={new Date(to).toISOString()} />
      </div>
    </div>
  );
}
```

### 6. Routes — Replace placeholder

```tsx
import { HistorianPage } from "@/features/historian/HistorianPage";
{ path: "historian", element: <HistorianPage /> },
```

### 7. AssetTable — Add search

Thêm `import { Search } from "lucide-react"` và input search trước filters:

```tsx
const [search, setSearch] = useState("");
// Before AssetFilters:
<div className="relative">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
  <input type="text" placeholder="Search by name or ID..." value={search}
    onChange={e => setSearch(e.target.value)}
    className="w-64 bg-gray-900 border border-gray-700 rounded pl-10 pr-3 py-2 text-sm" />
</div>
// Filter:
const filtered = assets?.filter((a: any) => !search ||
  a.name.toLowerCase().includes(search.toLowerCase()) ||
  a.asset_id.toLowerCase().includes(search.toLowerCase()));
// Use `filtered` instead of `assets` in the table
```

### 8. SignalTable — Add search

Tương tự AssetTable, thêm search input và filter local.

## UI Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Historian                                      [+ Add Chart]│
│  From: [2026-06-30 00:00]  To: [now]         3 signals      │
│                                                              │
│  ┌ PUMP pressure ×┐ ┌ Motor current ×┐ ┌ Tank level  ×┐    │
│  ├─────────────────┴─────────────────┴────────────────┴────┤
│  │ 🔍 Search signals...                                     │
│  │ ☑ PUMP-101  discharge_pressure  bar                     │
│  │ ☐ PUMP-101  flow_rate            m³/h                   │
│  │ ☑ MOTOR-101 motor_current        A                       │
│  ├──────────────────────────────────────────────────────────┤
│  │  7.5 ┤     ╭─╮  ← discharge_pressure (blue)              │
│  │  7.0 ┤╭────╯ ╰──╮                                        │
│  │      ┤──────────────  ← motor_current (green)            │
│  │  55  ┤   ╭──╮   ╭──                                      │
│  │  50  ┤───╯  ╰───╯                                        │
│  │      └──────────────────────────                          │
│  │  ██ discharge_pressure  ██ motor_current                 │
│  │  120 data points                                         │
│  └──────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

## Constraints

- [x] Tất cả data qua API
- [x] Dark mode ECharts theme
- [x] Multi-signal 1 chart với màu riêng (8 màu palette)
- [x] Search filter local (client-side)
- [x] Tab layout cho multi-chart panels
- [x] Bad quality points marked

## Validation

```bash
cd edge/simulator && python simulator.py --duration 30
open http://localhost:5173/historian
# Verify: search signals, select multiple, chart renders with multi-series
# Verify: Add Chart button creates new tab
# Verify: Search on Assets + Signals pages works
```
