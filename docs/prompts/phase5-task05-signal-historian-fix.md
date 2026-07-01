# Phase 5 — Task 5-05: Frontend Signal Real-time + Historian Fix

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-07-01

## Context

2 bug trên PlantOS Center UI cần fix:

1. **SignalTable** — 26 signals hiển thị metadata nhưng thiếu cột "Current Value" (realtime)
2. **Historian** — chọn signal nhưng chart hiển thị "0 data points", workspace bị reset về DEMO-PLANT khi navigate

## Implementation Checklist

- [ ] MODIFY `frontend/src/features/signals/SignalTable.tsx` — thêm cột Current Value
- [ ] MODIFY `frontend/src/features/historian/SignalMultiSelect.tsx` — hiển thị all signals cross-workspace
- [ ] BUILD frontend trên VPS
- [ ] DEPLOY dist lên nginx

## Detailed Instructions

### 1. `SignalTable.tsx` — Thêm Current Value Column

Thêm cột "Current Value" vào bảng signal, fetch từ API `/api/v1/measurements/current`.

```tsx
import { useQueries } from "@tanstack/react-query";
import { getSignals, getCurrentValues } from "@/lib/api";

export function SignalTable() {
  const { plantId } = useWorkspace();
  
  // Fetch all signals
  const { data: signals } = useQuery({
    queryKey: ["signals", plantId],
    queryFn: () => getSignals(),
  });

  // Filter by plant
  const assetIds = new Set((assets || []).map((a: any) => a.asset_id));
  const plantSignals = (signals || []).filter((s: any) => 
    !plantId || assetIds.has(s.asset_id)
  );

  // Fetch current values for displayed signals
  const currentQueries = useQueries({
    queries: (plantSignals || []).map((s: any) => ({
      queryKey: ["current", s.signal_id],
      queryFn: () => getCurrentValues({ signal_id: s.signal_id }),
      enabled: !!s.signal_id,
    })),
  });

  // Build lookup: signal_id → current value
  const currentMap: Record<string, any> = {};
  currentQueries.forEach((q, i) => {
    const sid = plantSignals[i]?.signal_id;
    if (sid && q.data) {
      const val = Array.isArray(q.data) ? q.data[0] : q.data;
      if (val) currentMap[sid] = val;
    }
  });

  // Table with extra column
  return (
    <table>
      <thead>
        <tr>
          <th>Signal ID</th>
          <th>Name</th>
          <th>Asset</th>
          <th>Type</th>
          <th>Unit</th>
          <th>Current Value</th>   {/* NEW */}
          <th>UNS Path</th>
        </tr>
      </thead>
      <tbody>
        {(filteredSignals || plantSignals).map((s: any) => {
          const cv = currentMap[s.signal_id];
          return (
            <tr key={s.signal_id}>
              <td>{s.signal_id}</td>
              <td>{s.display_name || s.signal_name}</td>
              <td>{s.asset_id}</td>
              <td>{s.data_type}</td>
              <td>{s.engineering_unit || '—'}</td>
              <td>
                {cv ? (
                  <span>
                    <span className="font-mono">{typeof cv.value === 'number' ? cv.value.toFixed(2) : String(cv.value)}</span>
                    <span className={`badge ${(cv.quality || 'GOOD').toLowerCase()}`}>{(cv.quality || 'GOOD')}</span>
                  </span>
                ) : (
                  <span className="text-gray-600">—</span>
                )}
              </td>
              <td>{s.uns_path || '—'}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
```

**Key changes:**
- Import `useQueries` + `getCurrentValues`
- Fetch current values in parallel via `useQueries`
- Render "Current Value" column with value + quality badge
- Show "—" if no current value yet

### 2. `SignalMultiSelect.tsx` — Cross-Workspace Signals

SignalMultiSelect hiện đang filter signals theo `plantId`, nhưng Historian cần hiển thị TẤT CẢ signals từ mọi plant.

```tsx
export function SignalMultiSelect({ selected, onChange }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  
  // Fetch ALL signals — no plantId filter
  const { data: signals } = useQuery({ 
    queryKey: ["signals-all-hist"], 
    queryFn: () => getSignals(),
    staleTime: 30000, // Signals rarely change
  });

  const filtered = useMemo(() => {
    if (!signals) return [];
    const q = search.toLowerCase();
    return signals.filter((s: any) =>
      s.signal_id.toLowerCase().includes(q) ||
      (s.display_name || s.signal_name).toLowerCase().includes(q) ||
      s.asset_id.toLowerCase().includes(q)
    );
  }, [signals, search]);

  // ... rest unchanged
```

**Key change:** Bỏ `plantId` khỏi filter. Historian là cross-workspace tool — user có thể chart bất kỳ signal nào.

### 3. Build & Deploy

```bash
cd /opt/plantos/frontend
npm run build
sudo cp -r dist/* /var/www/html/  # or wherever nginx serves from
sudo nginx -s reload
```

Nếu dùng nginx config hiện tại (root `/opt/plantos/frontend/dist`):

```bash
cd /opt/plantos/frontend
npm run build
sudo nginx -s reload
```

---

## Validation

```bash
# 1. Signal Table — current values
open http://103.97.132.249/signals
# Expected: cột "Current Value" hiển thị giá trị realtime + quality badge

# 2. Historian — chart
open http://103.97.132.249/historian
# Search "COMP01-CORE.flow_rate" → select → chart hiển thị trend line
# Expected: 176+ data points trên chart
```

---

## Files Summary

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `frontend/src/features/signals/SignalTable.tsx` | MODIFY | Thêm cột Current Value |
| 2 | `frontend/src/features/historian/SignalMultiSelect.tsx` | MODIFY | Cross-workspace signals |

## Handoff to Coder

```
Đọc: docs/prompts/phase5-task05-signal-historian-fix.md
2 files MODIFY. SignalTable thêm cột current value. SignalMultiSelect cross-workspace.
Build & deploy lên VPS: npm run build + nginx reload.
Validate: /signals có cột Current Value, /historian chart hiển thị dữ liệu.
```
