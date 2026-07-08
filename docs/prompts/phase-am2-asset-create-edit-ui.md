# Phase AM-2 — Asset Create/Edit UI

> **Phase:** AM-2 (Asset Model Builder)  
> **Depends on:** AM-1 (semantic core restored)  
> **Effort:** 2-3h  

---

## Objective

Complete asset CRUD: add DELETE endpoint to backend, create/edit modal in frontend, enhance AssetTable with actions.

---

## Task 1: Backend — DELETE Asset Endpoint

**File:** `backend/app/modules/assets/router.py`

Add soft-delete endpoint:

```python
from fastapi import HTTPException

@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str):
    """Soft-delete an asset by setting lifecycle_status='deleted'."""
    from app.modules.assets.service import AssetService
    svc = AssetService()
    asset = svc.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    svc.update(asset, {"lifecycle_status": "deleted"})
```

Also add a `get_by_id` method to `AssetService` if it doesn't exist yet:

**File:** `backend/app/modules/assets/service.py`

```python
@staticmethod
def get_by_id(asset_id: str) -> Asset | None:
    with get_session() as session:
        repo = AssetRepository(session)
        return repo.get_by_id(asset_id)
```

If `AssetService` already has `get_asset()` or similar, use that instead. Check before writing.

---

## Task 2: Backend — Asset Vocabulary Endpoint

**New file:** `backend/app/modules/assets/vocabulary.py`

```python
"""Allowed values for asset classification fields."""

ASSET_TYPES = [
    "pump", "filter", "tank", "motor", "sensor_array",
    "valve", "meter", "compressor_train", "compressor", "heat_exchanger",
    "centrifuge", "fan", "agitator", "mixer", "reactor",
    "blower", "boiler", "chiller", "cooling_tower", "generator",
    "transformer", "switchgear", "panel", "conveyor",
    "custom_equipment",
]

ASSET_ROLES = [
    "equipment", "functional_location", "subsystem", "component", "logical_group",
]

LIFECYCLE_STATUSES = ["active", "inactive", "maintenance", "retired", "deleted"]

CRITICALITY_LEVELS = ["low", "medium", "high", "critical"]
```

**New endpoint in router.py:**

```python
from app.modules.assets.vocabulary import ASSET_TYPES, ASSET_ROLES, LIFECYCLE_STATUSES, CRITICALITY_LEVELS

@router.get("/assets/vocabulary")
def get_asset_vocabulary():
    """Return allowed values for asset classification fields."""
    return {
        "asset_types": ASSET_TYPES,
        "asset_roles": ASSET_ROLES,
        "lifecycle_statuses": LIFECYCLE_STATUSES,
        "criticality_levels": CRITICALITY_LEVELS,
    }
```

Register in `backend/app/api/v1.py` (already registered via `assets_router` — no change needed).

---

## Task 3: Backend — Validate asset_id uniqueness on create

**File:** `backend/app/modules/assets/router.py`

In the `create_asset` function, add validation:

```python
@router.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(data: AssetCreate):
    """Create a new asset."""
    # Validate asset_id uniqueness
    from app.modules.assets.repository import AssetRepository
    from app.db import get_session
    with get_session() as session:
        repo = AssetRepository(session)
        existing = repo.get_by_id(data.asset_id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Asset '{data.asset_id}' already exists")
    
    # ... rest of existing create logic ...
```

Also validate `asset_code` uniqueness if provided.

---

## Task 4: Frontend — AssetForm Component

**New file:** `frontend/src/features/assets/AssetForm.tsx`

Modal form for creating/editing assets. Requirements:

### Props
```tsx
interface AssetFormProps {
  mode: "create" | "edit";
  asset?: any;           // existing asset data for edit mode
  onClose: () => void;   // close modal
  onSaved: () => void;   // refetch list after save
}
```

### Form Fields
| Field | Type | Required | Create | Edit |
|-------|------|----------|--------|------|
| `asset_id` | text | ✅ | editable | readonly |
| `asset_code` | text | ❌ | editable | editable |
| `name` | text | ✅ | editable | editable |
| `asset_type` | dropdown | ✅ | editable | editable |
| `asset_role` | dropdown | ✅ (default: equipment) | editable | editable |
| `area_id` | dropdown | ❌ | editable | editable |
| `parent_asset_id` | dropdown | ❌ | editable | editable |
| `criticality` | dropdown | ❌ (default: medium) | editable | editable |
| `lifecycle_status` | dropdown | ❌ (default: active) | editable | editable |
| `manufacturer` | text | ❌ | editable | editable |
| `model` | text | ❌ | editable | editable |

### Dropdown Data Sources
- `asset_type`: fetch from `GET /api/v1/assets/vocabulary` → `asset_types`
- `asset_role`: fetch from `GET /api/v1/assets/vocabulary` → `asset_roles`
- `criticality`: fetch from `GET /api/v1/assets/vocabulary` → `criticality_levels`
- `lifecycle_status`: fetch from `GET /api/v1/assets/vocabulary` → `lifecycle_statuses`
- `area_id`: fetch from `GET /api/v1/areas?plant_id={currentPlantId}`
- `parent_asset_id`: fetch from `GET /api/v1/assets` (all assets)

### API Calls
- **Create:** `POST /api/v1/assets` with AssetCreate body
- **Update:** `PATCH /api/v1/assets/{asset_id}` with AssetUpdate body

### Validation
- Required fields: asset_id, name, asset_type
- asset_id: max 128 chars, no spaces (or replace spaces with underscores client-side)
- On submit error (409 conflict): show inline error "Asset ID already exists"
- On submit error (other): show toast/alert with error detail

### UI
- Modal overlay with white/dark background
- Title: "Create Asset" or "Edit Asset"
- Cancel + Save buttons
- Form layout: 2-column grid for compact fields
- Loading state on submit button

### Styling
Use CSS custom properties (not hardcoded colors):
```
backgroundColor: 'var(--surface-card)'
borderColor: 'var(--border-default)'
color: 'var(--text-primary)'
```

---

## Task 5: Frontend — AssetTable Enhancements

**File:** `frontend/src/features/assets/AssetTable.tsx`

### Add Create Button
```tsx
import { Plus } from "lucide-react";

// In the header area:
<button onClick={() => setShowForm(true)} className="...">
  <Plus className="w-4 h-4" />
  Create Asset
</button>
```

### Add Edit Action
Each row gets an edit icon/button that opens AssetForm in edit mode:
```tsx
import { Pencil, Trash2 } from "lucide-react";

// In each row:
<button onClick={() => { setEditAsset(row); setShowForm(true); }}>
  <Pencil className="w-4 h-4" />
</button>
```

### Add Delete Action
```tsx
<button onClick={() => handleDelete(row.asset_id)}>
  <Trash2 className="w-4 h-4" style={{ color: 'var(--status-critical)' }} />
</button>
```

Delete handler:
```tsx
async function handleDelete(assetId: string) {
  if (!confirm(`Delete asset "${assetId}"?`)) return;
  const res = await fetchAPI(`/api/v1/assets/${assetId}`, { method: 'DELETE' });
  if (res.status === 204) {
    // refetch
  }
}
```

### State Management
```tsx
const [showForm, setShowForm] = useState(false);
const [editAsset, setEditAsset] = useState<any | null>(null);
// Pass to AssetForm: mode={editAsset ? "edit" : "create"} asset={editAsset}
```

### Action Column
Add an "Actions" column at the end of the table with edit + delete icons.

---

## Task 6: Frontend — AssetDetail Delete Button

**File:** `frontend/src/features/assets/AssetDetail.tsx`

Add a delete button in the header area:
```tsx
import { Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { fetchAPI } from "@/lib/api";

// Delete handler
async function handleDelete() {
  if (!confirm(`Delete asset "${assetId}"?`)) return;
  await fetchAPI(`/api/v1/assets/${assetId}`, { method: 'DELETE' });
  navigate('/assets');
}
```

---

## Task 7: Backend — PATCH /areas/{area_id}

**File:** `backend/app/modules/assets/router.py`

Add area update endpoint (needed for future AM phases, useful now):
```python
from app.modules.assets.schemas import AreaUpdate  # Need to create this

@router.patch("/areas/{area_id}", response_model=AreaResponse)
def update_area(area_id: str, data: AreaUpdate):
    """Update area metadata."""
    ...
```

**File:** `backend/app/modules/assets/schemas.py`

Add `AreaUpdate`:
```python
class AreaUpdate(BaseModel):
    name: Optional[str] = None
    area_type: Optional[str] = None
    status: Optional[str] = None
```

---

## Validation

```bash
# 1. Backend vocabulary
curl http://127.0.0.1:8000/api/v1/assets/vocabulary | python3 -m json.tool
# Expected: { "asset_types": [...], "asset_roles": [...], ... }

# 2. Create asset
curl -X POST http://127.0.0.1:8000/api/v1/assets \
  -H "Content-Type: application/json" \
  -H "X-API-Key: plantos-edge-8db46bd13a6a1e50b75f854b" \
  -d '{"asset_id":"TEST-001","name":"Test Asset","asset_type":"pump","plant_id":"WTP-DEMO-01","area_id":"INTAKE-AREA"}'
# Expected: 201 + AssetResponse with asset_role="equipment"

# 3. Duplicate check
curl -X POST ... -d '{"asset_id":"TEST-001",...}'
# Expected: 409

# 4. Delete
curl -X DELETE .../api/v1/assets/TEST-001
# Expected: 204

# 5. TypeScript
cd frontend && npx tsc --noEmit
# Expected: 0 errors
```

---

## Out of Scope

- Signal binding UI (AM-3)
- Template selector (AM-3)
- Batch import/export
- Bulk operations
- Soft-delete undo/restore
