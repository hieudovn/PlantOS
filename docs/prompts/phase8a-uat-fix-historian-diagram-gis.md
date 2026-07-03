# Phase 8A UAT Fix — WTP Historian, Diagram & GIS

## Context

Phase 8A WTP-DEMO-01 has been deployed and accepted. UAT found 4 issues that need fixing:

| # | Issue | Severity |
|---|-------|----------|
| 2 | Historian shows ALL signals (Compressor + WTP) — no filter | Medium |
| 3 | Selecting WTP signals → graph shows no data | **Critical** |
| 4 | Diagram & GIS pages show nothing for WTP | High |

## Required Reading

```text
frontend/src/features/historian/SignalMultiSelect.tsx    ← Issue 2
frontend/src/features/historian/TrendChart.tsx            ← Issue 3
frontend/src/features/historian/HistorianPage.tsx         ← Issue 2+3
frontend/src/features/visualization/DiagramPage.tsx       ← Issue 4
frontend/src/features/visualization/GisMapPage.tsx        ← Issue 4
backend/app/modules/signals/router.py                     ← Issue 2
backend/app/modules/signals/repository.py                 ← Issue 2
```

---

## Fix 1 (Critical): Verify WTP Data in TDengine

Before any frontend fixes, confirm data is actually being ingested.

### Step 1a: Check backend logs for WTP ingestion

```bash
ssh root@103.97.132.249 "docker logs plantos-backend --tail 200 2>&1 | grep -i -E 'wtp|WTP-DEMO' | tail -30"
```

### Step 1b: Query TDengine directly

```bash
ssh root@103.97.132.249 "docker exec plantos-tdengine taos -s 'SELECT COUNT(*) FROM plantos.d_raw_water_quality_station_101_raw_turbidity;'"
```

Try a few WTP signal tables:
```sql
SELECT COUNT(*) FROM plantos.d_raw_water_quality_station_101_raw_turbidity;
SELECT COUNT(*) FROM plantos.d_clarifier_101_settled_turbidity;
SELECT COUNT(*) FROM plantos.d_plant_kpi_101_cost_per_m3;
```

### Step 1c: Query via API

```bash
curl -s "http://103.97.132.249:8000/api/v1/measurements/history?signal_id=RAW-WATER-QUALITY-STATION-101.raw_turbidity&from=2026-07-02T00:00:00Z&to=2026-07-02T23:59:59Z" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool | head -30
```

If this returns `[]` or `null` → data is NOT in TDengine. Check if VF simulator HTTP ingestion is still running.

If this returns data → problem is in `TrendChart.tsx` timezone handling (Fix 3b).

---

## Fix 2: Add plant_id Filter to Signals API (Backend)

### File: `backend/app/modules/signals/router.py`

Add `plant_id` query parameter:

```python
@router.get("/", response_model=SignalListResponse)
async def list_signals(
    asset_id: str | None = Query(None),
    signal_type: str | None = Query(None),
    data_type: str | None = Query(None),
    plant_id: str | None = Query(None),  # ← ADD THIS
    db: AsyncSession = Depends(get_db),
):
    signals = await service.list_signals(
        db, asset_id=asset_id, signal_type=signal_type,
        data_type=data_type, plant_id=plant_id,  # ← PASS IT
    )
    return SignalListResponse(signals=signals, total=len(signals))
```

### File: `backend/app/modules/signals/service.py`

Add `plant_id` to `list_signals()`:

```python
async def list_signals(
    db: AsyncSession,
    asset_id: str | None = None,
    signal_type: str | None = None,
    data_type: str | None = None,
    plant_id: str | None = None,  # ← ADD THIS
) -> list[Signal]:
    return await repo.list_all(db, asset_id=asset_id, signal_type=signal_type,
                               data_type=data_type, plant_id=plant_id)
```

### File: `backend/app/modules/signals/repository.py`

Add plant_id filter logic to `list_all()`:

```python
async def list_all(
    db: AsyncSession,
    asset_id: str | None = None,
    signal_type: str | None = None,
    data_type: str | None = None,
    plant_id: str | None = None,  # ← ADD THIS
) -> list[Signal]:
    query = select(Signal)
    
    if plant_id:
        # Join Signal → Asset → Area → Plant
        query = (
            query.join(Asset, Signal.asset_id_fk == Asset.id)
            .join(Area, Asset.area_id_fk == Area.id)
            .join(Plant, Area.plant_id_fk == Plant.id)
            .where(Plant.plant_id == plant_id)
        )
    
    if asset_id:
        query = query.join(Asset, Signal.asset_id_fk == Asset.id).where(Asset.asset_id == asset_id)
    # ... rest of existing filters
    
    result = await db.execute(query)
    return list(result.scalars().all())
```

### File: `frontend/src/shared/api/signals.ts`

Add `plant_id` to the API client:

```typescript
export async function getSignals(params?: {
  asset_id?: string;
  signal_type?: string;
  data_type?: string;
  plant_id?: string;  // ← ADD THIS
}): Promise<Signal[]> {
  const searchParams = new URLSearchParams();
  if (params?.asset_id) searchParams.set("asset_id", params.asset_id);
  if (params?.signal_type) searchParams.set("signal_type", params.signal_type);
  if (params?.data_type) searchParams.set("data_type", params.data_type);
  if (params?.plant_id) searchParams.set("plant_id", params.plant_id);  // ← ADD THIS
  const query = searchParams.toString();
  const res = await fetch(`/api/v1/signals${query ? `?${query}` : ""}`);
  return res.json();
}
```

---

## Fix 3: Add Plant Filter to Historian Signal Picker (Frontend)

### File: `frontend/src/features/historian/SignalMultiSelect.tsx`

Add a plant filter dropdown ABOVE the signal selector:

```tsx
// 1. Import useWorkspace
import { useWorkspace } from "@/shared/hooks/useWorkspace";

// 2. Inside component, get current plant
const { currentPlantId } = useWorkspace();

// 3. Add a plant filter state
const [plantFilter, setPlantFilter] = useState<string>("all");

// 4. Fetch signals with plant_id when filter is active
const { data: signals } = useQuery({
  queryKey: ["signals-all-hist", plantFilter],
  queryFn: () => getSignals(
    plantFilter !== "all" ? { plant_id: plantFilter } : {}
  ),
});

// 5. Add a <select> above the signal picker
<select 
  value={plantFilter} 
  onChange={(e) => setPlantFilter(e.target.value)}
  className="..."
>
  <option value="all">All Plants</option>
  <option value="VF-DEMO">VF-DEMO (Compressor)</option>
  <option value="WTP-DEMO-01">WTP-DEMO-01 (Water Treatment)</option>
</select>
```

---

## Fix 4: Fix TrendChart Timezone Handling (Frontend)

### File: `frontend/src/features/historian/HistorianPage.tsx`

Current code (lines ~270-280) does `new Date(from).toISOString()` which produces UTC. The `TrendChart` then does local↔UTC conversion. This double-conversion can cause offset issues.

**Fix**: Pass local ISO strings directly, let TrendChart handle conversion once.

```tsx
// In HistorianPage, when calling TrendChart:
const fromStr = from.toLocaleDateString('sv-SE') + 'T00:00:00';  // Local midnight
const toStr = to.toLocaleDateString('sv-SE') + 'T23:59:59';      // Local end of day

await getHistory({ signal_id: signal.signal_id, from: fromStr, to: toStr });
```

### File: `frontend/src/features/historian/TrendChart.tsx`

Add "no data" handling:

```tsx
// After querying data:
if (!data || data.length === 0) {
  return (
    <div className="flex items-center justify-center h-48 text-muted-foreground">
      No data found for this time range
    </div>
  );
}
```

---

## Fix 5: Make Diagram Page Plant-Aware (Frontend)

### File: `frontend/src/features/visualization/DiagramPage.tsx`

Refactor to support per-plant diagrams:

```tsx
import { useWorkspace } from "@/shared/hooks/useWorkspace";

// Define available diagrams per plant
const PLANT_DIAGRAMS: Record<string, Array<{id: string, name: string, svg: string, binding: string}>> = {
  "VF-DEMO": [
    { id: "pid-process", name: "P&ID Process Line 01", svg: "/diagrams/pid-process.svg", binding: "/diagrams/pid-process.binding.yaml" },
    { id: "one-line-electrical", name: "One-Line Electrical", svg: "/diagrams/one-line-electrical.svg", binding: "/diagrams/one-line-electrical.binding.yaml" },
  ],
  "WTP-DEMO-01": [
    { id: "wtp-process", name: "WTP Process Flow", svg: "/diagrams/wtp-demo-01-process.svg", binding: "/diagrams/wtp-demo-01-process.binding.yaml" },
  ],
};

export function DiagramPage() {
  const { currentPlantId } = useWorkspace();
  const diagrams = PLANT_DIAGRAMS[currentPlantId || ""] || [];
  
  if (diagrams.length === 0) {
    return <div>No diagrams configured for this plant.</div>;
  }
  
  // ... render diagram selector + SvgDiagram with plant-specific SVG/binding
}
```

### Step: Copy WTP diagram files to frontend public folder

```bash
# Copy SVG + binding to frontend public dir
cp examples/diagrams/wtp-demo-01-process.svg frontend/public/diagrams/
cp examples/diagrams/wtp-demo-01-process.binding.yaml frontend/public/diagrams/
```

---

## Fix 6: Make GIS Page Plant-Aware (Frontend)

### File: `frontend/src/features/visualization/GisMapPage.tsx`

One-line fix:

```tsx
import { useWorkspace } from "@/shared/hooks/useWorkspace";

// In component:
const { currentPlantId } = useWorkspace();

// Change:
const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: () => getAssets() });
// To:
const { data: assets } = useQuery({ 
  queryKey: ["assets", currentPlantId], 
  queryFn: () => getAssets(currentPlantId ? { plant_id: currentPlantId } : undefined),
});
```

---

## Implementation Order

```
1. Fix 1  → Verify TDengine data (operational check)
2. Fix 2  → Backend plant_id filter (signals API)
3. Fix 4  → TrendChart timezone + "no data" message
4. Fix 3  → SignalMultiSelect plant filter dropdown
5. Fix 5  → Diagram page per-plant + copy WTP SVG
6. Fix 6  → GIS page plant filter
```

## Verification After Fixes

```bash
# 1. Test plant-filtered signals
curl "http://103.97.132.249:8000/api/v1/signals?plant_id=WTP-DEMO-01" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(len(json.load(sys.stdin)['signals']))"
# Expected: 92

# 2. Test historian query for WTP
curl "http://103.97.132.249:8000/api/v1/measurements/history?signal_id=RAW-WATER-QUALITY-STATION-101.raw_turbidity&from=2026-07-02T00:00:00Z&to=2026-07-02T23:59:59Z" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'Points: {len(d) if isinstance(d,list) else d}')"

# 3. Verify frontend rebuild works
cd frontend && npm run build
```

## Deliverables

- Fixed `backend/app/modules/signals/router.py`
- Fixed `backend/app/modules/signals/service.py`
- Fixed `backend/app/modules/signals/repository.py`
- Fixed `frontend/src/shared/api/signals.ts`
- Fixed `frontend/src/features/historian/SignalMultiSelect.tsx`
- Fixed `frontend/src/features/historian/TrendChart.tsx`
- Fixed `frontend/src/features/historian/HistorianPage.tsx`
- Fixed `frontend/src/features/visualization/DiagramPage.tsx`
- Fixed `frontend/src/features/visualization/GisMapPage.tsx`
- Copied WTP diagram files to `frontend/public/diagrams/`
