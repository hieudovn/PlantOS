# Phase 2 — Task 2-01: UX Polish (State Persistence + Chart Rename + Chart Type)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

3 small UX fixes, frontend-only, 1 session:
1. **State persistence** — Historian setups survive navigation
2. **Chart rename** — double-click tab to edit label
3. **Chart type selector** — dropdown Line/Bar/Scatter/Area

## Implementation Checklist

- [ ] MODIFY `frontend/src/features/historian/HistorianPage.tsx` — localStorage + rename + type selector
- [ ] MODIFY `frontend/src/features/historian/TrendChart.tsx` — support chartType prop

## Detailed Instructions

### 1. State Persistence via localStorage

Lưu `panels`, `from`, `to`, `active` vào `localStorage` key `"plantos-historian-state"`.

```tsx
const STORAGE_KEY = "plantos-historian-state";

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

function saveState(state: any) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {}
}
```

Khởi tạo state từ localStorage (nếu có), fallback về default. Mỗi khi state thay đổi → `saveState`.

```tsx
const saved = loadState();
const [from, setFrom] = useState(saved?.from || fmt(today));
const [to, setTo] = useState(saved?.to || fmt(now));
const [panels, setPanels] = useState<Panel[]>(saved?.panels || [...]);
const [active, setActive] = useState(saved?.active || 0);

// Auto-save on change
useEffect(() => {
  saveState({ from, to, panels, active });
}, [from, to, panels, active]);
```

### 2. Chart Tab Rename

Thêm state `editingTab: number | null`. Double-click tab → set `editingTab = index`. Hiển thị input thay vì text.

```tsx
const [editingTab, setEditingTab] = useState<number | null>(null);
const [editValue, setEditValue] = useState("");

// In tab button:
{editingTab === i ? (
  <input
    value={editValue}
    onChange={e => setEditValue(e.target.value)}
    onBlur={() => {
      if (editValue.trim()) {
        const np = [...panels]; np[i].label = editValue.trim(); setPanels(np);
      }
      setEditingTab(null);
    }}
    onKeyDown={e => { if (e.key === "Enter") e.currentTarget.blur(); }}
    className="bg-gray-800 px-1 py-0 text-sm w-24 outline-none"
    autoFocus
    onClick={e => e.stopPropagation()}
  />
) : (
  <span onDoubleClick={() => { setEditingTab(i); setEditValue(p.label); }}>
    {p.label}
  </span>
)}
```

### 3. Chart Type Selector

Thêm state `chartType: string` (per panel hoặc global). Dropdown bên cạnh time range.

```tsx
const [chartType, setChartType] = useState(saved?.chartType || "line");

// In JSX, next to time range:
<select value={chartType} onChange={e => setChartType(e.target.value)}
  className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm">
  <option value="line">Line</option>
  <option value="bar">Bar</option>
  <option value="scatter">Scatter</option>
  <option value="area">Area</option>
</select>

// Save chartType to localStorage too:
useEffect(() => {
  saveState({ from, to, panels, active, chartType });
}, [from, to, panels, active, chartType]);
```

Pass `chartType` to TrendChart:

```tsx
<TrendChart signalIds={...} from={...} to={...} chartType={chartType} />
```

### 4. TrendChart — Support chartType

```tsx
type Props = { signalIds: string[]; from: string; to: string; chartType?: string };

// In series push, use chartType:
series.push({
  name: sid,
  type: chartType === "area" ? "line" : chartType,  // area = line + areaStyle
  data: good.map((p: any) => [p.timestamp, p.value]),
  smooth: false,
  symbol: chartType === "scatter" ? "circle" : chartType === "bar" ? "none" : "circle",
  symbolSize: chartType === "scatter" ? 8 : 4,
  lineStyle: chartType === "scatter" ? undefined : { color: COLORS[i % COLORS.length], width: 1.5 },
  itemStyle: { color: COLORS[i % COLORS.length] },
  areaStyle: chartType === "area" ? { color: COLORS[i % COLORS.length] + "18", opacity: 0.3 } : undefined,
});
```

## Validation

```bash
# 1. Open Historian, add chart, select signals, set time range
# 2. Change chart type → verify chart updates
# 3. Double-click tab → rename
# 4. Navigate to Diagrams, then back to Historian
# 5. Verify all settings preserved
```

## Files Modified

| # | File | Change |
|---|------|--------|
| 1 | `HistorianPage.tsx` | localStorage, rename, chart type selector |
| 2 | `TrendChart.tsx` | chartType prop support |
