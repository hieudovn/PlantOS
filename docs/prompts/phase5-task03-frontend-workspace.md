# Phase 5 — Task 5-03: Frontend Multi-Workspace + VF-DEMO Data Visibility

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-07-01

## Context

PlantOS Backend có đầy đủ dữ liệu VF-DEMO (7 assets, 26 signals, measurements từ OPC UA), nhưng Frontend hiện hardcode `"DEMO-PLANT"` trong Topbar, không có workspace switcher, dẫn đến:

- Overview: 0 assets, 0 signals
- AssetTree/AssetTable: không thấy COMP01
- Historian SignalMultiSelect: không search được signal VF-DEMO
- Area filter dropdown: chỉ có Process Area / Electrical Area

Cần thêm **Workspace Switcher** để chọn giữa DEMO-PLANT và VF-DEMO, tự động filter tất cả API calls.

## Implementation Checklist

- [ ] CREATE `frontend/src/lib/WorkspaceContext.tsx` — React context + provider
- [ ] MODIFY `frontend/src/app/providers.tsx` — wrap with WorkspaceProvider
- [ ] MODIFY `frontend/src/components/layout/Topbar.tsx` — dropdown workspace
- [ ] MODIFY `frontend/src/features/overview/OverviewPage.tsx` — filter by workspace
- [ ] MODIFY `frontend/src/features/assets/AssetTable.tsx` — filter by workspace
- [ ] MODIFY `frontend/src/features/assets/AssetTree.tsx` — filter by workspace
- [ ] MODIFY `frontend/src/features/signals/SignalTable.tsx` — filter by workspace
- [ ] MODIFY `frontend/src/features/historian/SignalMultiSelect.tsx` — filter by workspace
- [ ] MODIFY `frontend/src/features/alarms/AlarmPage.tsx` — filter by workspace (if applicable)

## Detailed Instructions

### 1. `frontend/src/lib/WorkspaceContext.tsx` (CREATE)

```tsx
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getPlants } from "./api";

interface WorkspaceContextType {
  plantId: string;
  setPlantId: (id: string) => void;
  plants: string[];
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  plantId: "DEMO-PLANT",
  setPlantId: () => {},
  plants: [],
});

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [plantId, setPlantId] = useState("DEMO-PLANT");
  const [plants, setPlants] = useState<string[]>(["DEMO-PLANT"]);

  useEffect(() => {
    getPlants()
      .then((data) => {
        const ids = data.map((p: any) => p.plant_id);
        if (ids.length > 0) {
          setPlants(ids);
          // Auto-select first plant if current not in list
          if (!ids.includes(plantId)) {
            setPlantId(ids[0]);
          }
        }
      })
      .catch(() => {});
  }, []);

  return (
    <WorkspaceContext.Provider value={{ plantId, setPlantId, plants }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
```

### 2. `frontend/src/app/providers.tsx` (MODIFY)

Thêm `WorkspaceProvider` bọc ngoài:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WorkspaceProvider } from "@/lib/WorkspaceContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5000, retry: 1 },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceProvider>
        {children}
      </WorkspaceProvider>
    </QueryClientProvider>
  );
}
```

### 3. `frontend/src/components/layout/Topbar.tsx` (MODIFY)

Thay `<span>DEMO-PLANT</span>` bằng dropdown:

```tsx
import { useWorkspace } from "@/lib/WorkspaceContext";

export function Topbar() {
  const { plantId, setPlantId, plants } = useWorkspace();

  return (
    <header className="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-gray-900/50">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Workspace:</span>
        <select
          value={plantId}
          onChange={(e) => setPlantId(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm font-medium text-white focus:outline-none focus:border-blue-500"
        >
          {plants.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>
      <div className="text-xs text-gray-600">MVP Preview</div>
    </header>
  );
}
```

### 4. `frontend/src/features/overview/OverviewPage.tsx` (MODIFY)

Thêm filter plant_id vào API calls:

```tsx
import { useWorkspace } from "@/lib/WorkspaceContext";

export function OverviewPage() {
  const { plantId } = useWorkspace();
  const { data: assets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => getAssets({ plant_id: plantId }),
  });
  const { data: signals } = useQuery({
    queryKey: ["signals-all", plantId],
    queryFn: () => getSignals({ asset_id__like: "" }), // get all, filter in UI if needed
  });

  // ... rest unchanged
}
```

### 5. `frontend/src/features/assets/AssetTable.tsx` (MODIFY)

Tìm dòng gọi `getAssets()` và thêm `plant_id`:

```tsx
const { plantId } = useWorkspace();
const { data: assets } = useQuery({
  queryKey: ["assets", plantId],
  queryFn: () => getAssets({ plant_id: plantId }),
});
```

Tương tự cho area filter dropdown — lấy areas từ API thay vì hardcode.

### 6. `frontend/src/features/assets/AssetTree.tsx` (MODIFY)

Thêm import `useWorkspace` và filter:

```tsx
import { useWorkspace } from "@/lib/WorkspaceContext";

// Trong component:
const { plantId } = useWorkspace();
const { data: assets } = useQuery({
  queryKey: ["assets-tree", plantId],
  queryFn: () => getAssets({ plant_id: plantId }),
});
```

### 7. `frontend/src/features/signals/SignalTable.tsx` (MODIFY)

Thêm filter plant_id:

```tsx
const { plantId } = useWorkspace();
const { data: signals } = useQuery({
  queryKey: ["signals", plantId],
  queryFn: () => getSignals({ asset_id__like: "" }), // fetch all signals for the plant
});
```

### 8. `frontend/src/features/historian/SignalMultiSelect.tsx` (MODIFY)

Filter tín hiệu theo plant_id hiện tại:

```tsx
import { useWorkspace } from "@/lib/WorkspaceContext";

// Trong component:
const { plantId } = useWorkspace();
const { data: signals } = useQuery({
  queryKey: ["signals-all", plantId],
  queryFn: () => getSignals(),
});

// Filter by plant_id in the filtered memo:
const filtered = useMemo(() => {
  if (!signals) return [];
  const q = search.toLowerCase();
  return signals.filter((s: any) => {
    // Filter by current workspace
    const matchesPlant = !plantId || s.asset_id?.startsWith(plantId.toLowerCase().replace(/-/g, "")) || true;
    const matchesSearch =
      s.signal_id.toLowerCase().includes(q) ||
      (s.display_name || s.signal_name).toLowerCase().includes(q) ||
      s.asset_id.toLowerCase().includes(q);
    return matchesPlant && matchesSearch;
  });
}, [signals, search, plantId]);
```

**Lưu ý:** Backend API `/api/v1/signals` không có filter `plant_id` trực tiếp. Cần dùng pattern match qua `asset_id` hoặc gọi signals API rồi filter ở frontend. Tốt nhất: gọi `getSignals()` không filter, hiển thị tất cả signal từ tất cả plants (vì SignalMultiSelect dùng cho chart — user muốn chọn bất kỳ signal nào).

**→ Thiết kế lại:** SignalMultiSelect hiển thị TẤT CẢ signals từ mọi plant. Workspace chỉ filter Assets/Signals tables. Historian chart không bị giới hạn bởi workspace.

### 9. Area Filter Dynamic

Thay vì hardcode "Process Area" / "Electrical Area" trong AssetTable, gọi API areas:

```tsx
import { getPlants } from "@/lib/api"; // thêm getAreas nếu chưa có
// API: GET /api/v1/areas?plant_id={plantId}
```

Nếu backend chưa có `/api/v1/areas` endpoint riêng, có thể extract unique `area_id` từ danh sách assets.

---

## Constraints

- [x] Không thay đổi backend API
- [x] Workspace mặc định: plant đầu tiên từ API
- [x] Historian SignalMultiSelect hiển thị TẤT CẢ signals (cross-workspace)
- [x] Assets/Signals tables filter theo workspace đang chọn
- [x] Overview KPIs filter theo workspace

## Validation

```bash
# 1. Frontend load
open http://localhost:5173
# Expected: Topbar hiển thị dropdown với DEMO-PLANT và VF-DEMO

# 2. Switch to VF-DEMO
# Expected: Overview hiển thị 7 assets, 26 signals

# 3. Assets page
open http://localhost:5173/assets
# Expected: Asset tree hiển thị COMP01 → COMP01-MOTOR, COMP01-CORE, ...

# 4. Historian
open http://localhost:5173/historian
# Expected: Search "COMP01" → hiển thị 26 signals
# Add COMP01-CORE.flow_rate → chart hiển thị trend từ TDengine
```

---

## Files Summary

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `frontend/src/lib/WorkspaceContext.tsx` | CREATE | React context + provider |
| 2 | `frontend/src/app/providers.tsx` | MODIFY | Wrap with WorkspaceProvider |
| 3 | `frontend/src/components/layout/Topbar.tsx` | MODIFY | Dropdown workspace |
| 4 | `frontend/src/features/overview/OverviewPage.tsx` | MODIFY | Filter KPIs by workspace |
| 5 | `frontend/src/features/assets/AssetTable.tsx` | MODIFY | Filter assets by workspace |
| 6 | `frontend/src/features/assets/AssetTree.tsx` | MODIFY | Filter tree by workspace |
| 7 | `frontend/src/features/signals/SignalTable.tsx` | MODIFY | Filter signals by workspace |
| 8 | `frontend/src/features/historian/SignalMultiSelect.tsx` | MODIFY | Show all signals (cross-workspace) |

## Handoff to Coder

```
Đọc prompt: docs/prompts/phase5-task03-frontend-workspace.md
8 files (1 CREATE, 7 MODIFY).
Thêm WorkspaceContext + dropdown chọn plant.
Assets/Signals/Overview filter theo workspace.
Historian SignalMultiSelect hiển thị TẤT CẢ signals (không giới hạn workspace).
Validate: chọn VF-DEMO → thấy COMP01 assets, search COMP01 signal trên Historian.
```
