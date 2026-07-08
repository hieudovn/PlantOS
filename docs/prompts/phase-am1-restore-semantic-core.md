# Phase AM-1 — Restore Semantic Core

> **Phase:** AM-1 (Asset Model Builder)  
> **Effort:** 2-3h  
> **Priority:** HIGH — SA required for all subsequent AM phases  

---

## Objective

Expose `asset_role`, `signal_category`, and `external_refs` in API schemas. These fields exist in DB and ORM models but are missing from Pydantic request/response schemas.

---

## Task 1: Add asset_role to Asset Schemas

**File:** `backend/app/modules/assets/schemas.py`

1. Add to `AssetCreate`:
```python
asset_role: str = Field("equipment", max_length=32,
    description="Semantic role: equipment, functional_location, subsystem, component, logical_group")
```

2. Add to `AssetUpdate`:
```python
asset_role: Optional[str] = Field(None, max_length=32)
```

3. Add to `AssetResponse`:
```python
asset_role: str
```

4. In `backend/app/modules/assets/service.py`, update `_asset_to_response()` to include:
```python
asset_role=asset.asset_role,
```

---

## Task 2: Add signal_category + external_refs to Signal Schemas

**File:** `backend/app/modules/signals/schemas.py`

1. Add to `SignalCreate`:
```python
signal_category: str = Field("measurement", max_length=32)
external_refs: Optional[dict] = Field(None, description="Opaque external references metadata")
```

2. Add to `SignalUpdate`:
```python
signal_category: Optional[str] = Field(None, max_length=32)
external_refs: Optional[dict] = None
```

3. Add to `SignalResponse`:
```python
signal_category: str
external_refs: Optional[dict] = None
```

4. In `backend/app/modules/signals/service.py`, check if `_signal_to_response()` exists. If it does, add `signal_category` and `external_refs`. If the schemas are used directly (schema.model_validate(orm_obj)), the fields should be picked up automatically.

---

## Task 3: Regenerate Contract Schema

**File:** `schemas/plantos-integration-contract.schema.json`

Check that `asset_role` is in the asset schema definition and `signal_category` in the signal schema. If missing, add them:

```json
"asset_role": { "type": "string", "maxLength": 32, "description": "Semantic role" }
"signal_category": { "type": "string", "maxLength": 32, "description": "Signal category" }
"external_refs": { "type": "object", "description": "External references metadata" }
```

---

## Task 4: Regression Tests

**New file:** `backend/tests/test_regression_am1.py`

```python
"""Regression tests for AM-1: Restore Semantic Core."""

from app.modules.assets.schemas import AssetResponse, AssetCreate
from app.modules.signals.schemas import SignalResponse, SignalCreate


def test_asset_create_schema_has_asset_role():
    """AssetCreate must include asset_role field."""
    schema = AssetCreate.model_json_schema()
    assert "asset_role" in schema["properties"]
    assert schema["properties"]["asset_role"]["default"] == "equipment"


def test_asset_response_schema_has_asset_role():
    """AssetResponse must include asset_role field."""
    schema = AssetResponse.model_json_schema()
    assert "asset_role" in schema["properties"]


def test_signal_create_schema_has_signal_category():
    """SignalCreate must include signal_category field."""
    schema = SignalCreate.model_json_schema()
    assert "signal_category" in schema["properties"]


def test_signal_response_schema_has_signal_category():
    """SignalResponse must include signal_category and external_refs."""
    schema = SignalResponse.model_json_schema()
    assert "signal_category" in schema["properties"]
    assert "external_refs" in schema["properties"]


def test_frontend_operations_asset_role_not_broken():
    """Quick check that AssetCard still builds with asset_role field present."""
    # Import the resolver to verify it can read asset_role
    from app.modules.events.resolver import resolve_asset_info
    info = resolve_asset_info("FILTER-101")  # known WTP asset
    assert info is not None
    assert "asset_role" in info
    assert info["asset_role"] in ("equipment", "functional_location", "subsystem", "component", "logical_group")
```

Run: `python -m pytest backend/tests/test_regression_am1.py -v`

---

## Task 5: Frontend Update

**File:** `frontend/src/features/assets/AssetTable.tsx`

In the columns definition, add an `asset_role` column after the `asset_type` column:

```tsx
{
  key: "asset_role",
  header: "Role",
  render: (row: any) => (
    <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--surface-hover)' }}>
      {row.asset_role}
    </span>
  ),
}
```

**File:** `frontend/src/features/assets/AssetDetail.tsx`

Add asset_role badge next to the existing type badge:

```tsx
<div className="flex gap-2 mt-1">
  <span className="..."> {asset.asset_type} </span>
  <span className="..."> {asset.asset_role} </span>
</div>
```

---

## Task 6: Verify ProcessView Not Broken

After deploying, verify:
1. Navigate to `/operations` — 7 WTP blocks still render
2. Navigate to `/operations/area/FILTRATION-AREA` — 4 asset cards with data
3. Asset cards show `asset_role` (it was previously from `getattr` fallback — now from API)

---

## Validation

```bash
# 1. Schema test
cd backend && python -m pytest tests/test_regression_am1.py -v

# 2. API test
curl http://103.97.132.249/api/v1/assets/FILTER-101 | jq .asset_role
# Expected: "equipment"

curl http://103.97.132.249/api/v1/signals/RWP-101.flow_rate | jq .signal_category
# Expected: "measurement"

# 3. Build check
cd frontend && npm run build  # must pass
```
