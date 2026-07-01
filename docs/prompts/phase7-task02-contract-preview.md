# Phase 7 — Task 7-02: Import Preview / Diff (Phase C)

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P1  
> **Depends on:** Phase 7-01 (Contract Validator) ✅

## Context

Sau khi contract được validate, bước tiếp theo là **preview**: so sánh contract với dữ liệu hiện có trong PostgreSQL để biết chính xác những gì sẽ thay đổi nếu import.

```
Contract YAML → Validate (7-01) → Preview/Diff (7-02) → Apply (7-03, future)
```

## Architecture

```
POST /api/v1/contracts/preview
        │
        ▼
ContractValidator (reuse from 7-01)
        │
        ▼
Compare against PostgreSQL
  ├─ plants table
  ├─ areas table
  ├─ assets table
  └─ signals table
        │
        ▼
Return diff: {creates, updates, conflicts, orphans}
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/contracts/preview.py` — preview logic
- [ ] MODIFY `backend/app/modules/contracts/router.py` — add POST /api/v1/contracts/preview
- [ ] CREATE `backend/tests/test_contracts_preview.py` — preview tests
- [ ] VERIFY: preview against empty DB → all entities are "create"
- [ ] VERIFY: preview against existing VF-DEMO → detects existing (conflict/skip)
- [ ] VERIFY: preview does NOT write to database

## Non-Negotiable Constraints

1. **Do NOT write to PostgreSQL** — preview is read-only
2. **Do NOT modify existing Asset/Signal/Measurement modules**
3. **Do NOT access TDengine**
4. **Reuse** existing AssetRepository and SignalRepository for comparison
5. **Do NOT change** the validate endpoint (7-01)

## Detailed Instructions

### 1. File: `backend/app/modules/contracts/preview.py`

```python
"""Contract preview — compare against current PostgreSQL state."""

from dataclasses import dataclass, field
from app.db import get_session
from app.modules.assets.repository import AssetRepository
from app.modules.signals.repository import SignalRepository


@dataclass
class PreviewChanges:
    creates: list[str] = field(default_factory=list)
    updates: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)


@dataclass
class PreviewResult:
    valid: bool
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    plants: PreviewChanges = field(default_factory=PreviewChanges)
    areas: PreviewChanges = field(default_factory=PreviewChanges)
    assets: PreviewChanges = field(default_factory=PreviewChanges)
    signals: PreviewChanges = field(default_factory=PreviewChanges)


def preview_contract(contract_dict: dict) -> PreviewResult:
    """Compare contract against current DB state. Returns diff without writing."""
    result = PreviewResult(valid=True)

    plant_id = contract_dict["plant"]["plant_id"]

    with get_session() as session:
        asset_repo = AssetRepository(session)
        signal_repo = SignalRepository(session)

        # ---- Plants ----
        existing_plant = _get_plant(session, plant_id)
        if existing_plant:
            result.plants.conflicts.append(plant_id)
        else:
            result.plants.creates.append(plant_id)

        # ---- Areas ----
        existing_areas = _get_areas(session, plant_id)
        existing_area_ids = {a.area_id for a in existing_areas}
        contract_area_ids = {a["area_id"] for a in contract_dict["areas"]}

        for area_id in contract_area_ids - existing_area_ids:
            result.areas.creates.append(area_id)
        for area_id in contract_area_ids & existing_area_ids:
            result.areas.conflicts.append(area_id)
        for area_id in existing_area_ids - contract_area_ids:
            result.areas.orphans.append(area_id)

        # ---- Assets ----
        existing_assets = _get_assets(session, plant_id)
        existing_asset_ids = {a.asset_id for a in existing_assets}
        contract_asset_ids = {a["asset_id"] for a in contract_dict["assets"]}

        for asset_id in contract_asset_ids - existing_asset_ids:
            result.assets.creates.append(asset_id)
        for asset_id in contract_asset_ids & existing_asset_ids:
            result.assets.conflicts.append(asset_id)
        for asset_id in existing_asset_ids - contract_asset_ids:
            result.assets.orphans.append(asset_id)

        # ---- Signals ----
        existing_signals = signal_repo.get_all()
        existing_signal_ids = {
            s.signal_id for s in existing_signals
            if any(s.signal_id.startswith(aid) for aid in contract_asset_ids)
        }
        # Broader: get all signals for the plant
        all_plant_signals = {
            s.signal_id for s in existing_signals
            if s.asset_id in existing_asset_ids
        }
        contract_signal_ids = {s["signal_id"] for s in contract_dict["signals"]}

        for sig_id in contract_signal_ids - all_plant_signals:
            result.signals.creates.append(sig_id)
        for sig_id in contract_signal_ids & all_plant_signals:
            result.signals.conflicts.append(sig_id)
        for sig_id in all_plant_signals - contract_signal_ids:
            result.signals.orphans.append(sig_id)

    # Overall validity: valid if no errors from previous validation + no structural issues
    return result


def _get_plant(session, plant_id: str):
    """Get plant by ID. Returns None if not found."""
    from sqlalchemy import text
    rows = session.execute(
        text("SELECT plant_id FROM plants WHERE plant_id = :pid"),
        {"pid": plant_id}
    ).fetchall()
    return rows[0] if rows else None


def _get_areas(session, plant_id: str):
    """Get all areas for a plant."""
    from sqlalchemy import text
    rows = session.execute(
        text("SELECT area_id, name FROM areas WHERE plant_id = :pid"),
        {"pid": plant_id}
    ).fetchall()
    return rows


def _get_assets(session, plant_id: str):
    """Get all assets for a plant (via areas)."""
    from sqlalchemy import text
    rows = session.execute(
        text("""
            SELECT a.asset_id, a.name FROM assets a
            JOIN areas ar ON a.area_id = ar.area_id
            WHERE ar.plant_id = :pid
        """),
        {"pid": plant_id}
    ).fetchall()
    return rows
```

### 2. Modify `backend/app/modules/contracts/router.py`

Add the preview endpoint after the validate endpoint:

```python
from .preview import preview_contract

@router.post("/contracts/preview")
async def preview_contract_endpoint(payload: dict):
    """Preview import — compare contract against DB. Does NOT write."""
    try:
        contract = ContractV2(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Contract structure invalid: {e}")

    contract_dict = contract.model_dump()

    # Run validator first (reuse 7-01 logic)
    from .validator import validate_contract
    validation = validate_contract(contract_dict)
    if not validation.valid:
        return {
            "valid": False,
            "validation_errors": validation.errors,
            "validation_warnings": validation.warnings,
            "changes": None,
        }

    # Run preview
    preview = preview_contract(contract_dict)

    return {
        "valid": True,
        "validation_warnings": validation.warnings,
        "changes": {
            "plants": {
                "create": preview.plants.creates,
                "update": preview.plants.updates,
                "conflict": preview.plants.conflicts,
                "orphan": preview.plants.orphans,
            },
            "areas": {
                "create": preview.areas.creates,
                "update": preview.areas.updates,
                "conflict": preview.areas.conflicts,
                "orphan": preview.areas.orphans,
            },
            "assets": {
                "create": preview.assets.creates,
                "update": preview.assets.updates,
                "conflict": preview.assets.conflicts,
                "orphan": preview.assets.orphans,
            },
            "signals": {
                "create": preview.signals.creates,
                "update": preview.signals.updates,
                "conflict": preview.signals.conflicts,
                "orphan": preview.signals.orphans,
            },
        },
        "summary": {
            "total_creates": (
                len(preview.plants.creates)
                + len(preview.areas.creates)
                + len(preview.assets.creates)
                + len(preview.signals.creates)
            ),
            "total_updates": (
                len(preview.plants.updates)
                + len(preview.areas.updates)
                + len(preview.assets.updates)
                + len(preview.signals.updates)
            ),
            "total_conflicts": (
                len(preview.plants.conflicts)
                + len(preview.areas.conflicts)
                + len(preview.assets.conflicts)
                + len(preview.signals.conflicts)
            ),
            "total_orphans": (
                len(preview.plants.orphans)
                + len(preview.areas.orphans)
                + len(preview.signals.orphans)
            ),
        },
    }
```

### 3. Tests: `backend/tests/test_contracts_preview.py`

```python
import pytest
from app.modules.contracts.preview import preview_contract

VALID_CONTRACT = {
    "contract": {"version": "2.0", "schema_version": "2.0", "description": "Preview test"},
    "source": {"system_type": "manual", "system_name": "Test", "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z"},
    "plant": {"plant_id": "PREVIEW-TEST", "plant_code": "PT", "name": "Preview Test Plant", "timezone": "UTC"},
    "areas": [{"area_id": "PT-AREA", "area_code": "PTA", "name": "Test Area", "plant_id": "PREVIEW-TEST"}],
    "assets": [
        {"asset_id": "PT-PUMP", "asset_code": "PTP", "name": "Test Pump", "asset_type": "pump", "area_id": "PT-AREA"},
    ],
    "signals": [
        {"signal_id": "PT-PUMP.speed", "asset_id": "PT-PUMP", "signal_name": "speed", "display_name": "Speed", "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM"},
        {"signal_id": "PT-PUMP.temp", "asset_id": "PT-PUMP", "signal_name": "temp", "display_name": "Temp", "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC"},
    ],
    "uns": {"namespace_root": "test", "path_template": "{namespace_root}/{plant_id}/{signal_name}"},
    "import_recommendation": {"suggested_mode": "preview", "reason": "test"},
}


class TestPreview:
    def test_new_plant_all_creates(self):
        """Preview against empty DB: all entities should be creates."""
        result = preview_contract(VALID_CONTRACT)
        assert result.valid is True
        assert len(result.plants.creates) == 1
        assert len(result.plants.conflicts) == 0
        assert len(result.areas.creates) == 1
        assert len(result.assets.creates) == 1
        assert len(result.signals.creates) == 2

    def test_existing_plant_detected(self):
        """Preview against VF-DEMO should detect conflicts."""
        # This test requires VF-DEMO to exist in DB
        contract = {**VALID_CONTRACT}
        contract["plant"]["plant_id"] = "VF-DEMO"
        contract["areas"][0]["plant_id"] = "VF-DEMO"
        result = preview_contract(contract)
        # VF-DEMO exists → conflict on plant
        assert "VF-DEMO" in result.plants.conflicts or "VF-DEMO" in result.plants.creates

    def test_preview_does_not_write(self):
        """Preview must not write to DB."""
        import random, string
        rand_id = "R" + "".join(random.choices(string.ascii_uppercase, k=8))
        contract = {**VALID_CONTRACT}
        contract["plant"]["plant_id"] = rand_id
        contract["areas"][0]["plant_id"] = rand_id

        # Run preview twice — second should still show creates (not conflicts)
        result1 = preview_contract(contract)
        result2 = preview_contract(contract)

        assert len(result1.plants.creates) == 1  # First: create
        assert len(result2.plants.creates) == 1  # Second: STILL create (not written)
```

### 4. Deploy & Verify

```bash
# Build and test locally
cd backend && python -m pytest tests/test_contracts_preview.py -v

# If tests pass, build and deploy
cd deployment && docker compose build backend
# ... scp + docker load + restart on VPS

# Test via API
curl -s -X POST http://localhost:8000/api/v1/contracts/preview \
  -H "Content-Type: application/json" \
  -H "X-API-Key: plantos-edge-key-2026" \
  -d @/tmp/test_contract_valid.json
```

### 5. Validation

| Check | Expected |
|---|---|
| Preview new plant | `creates: 1 plant, 1 area, 1 asset, 2 signals`, `conflicts: 0` |
| Preview VF-DEMO | `conflicts` list shows existing entities |
| Preview twice → same result | Proves no DB write |
| Existing validate endpoint | Still works (unchanged from 7-01) |
| Existing APIs | Unaffected |

## Notes

- Preview uses raw SQL via `text()` to access plants/areas tables — because AssetRepository may not have plant-level queries. If AssetRepository already has the needed methods, use them instead.
- The `signal_repo.get_all()` might be heavy for large datasets. In production, add filtering by `asset_id`. For MVP with 26 signals, this is fine.
- Orphan detection only works when contract specifies a plant that already exists in DB.
- Phase C does NOT implement the `apply` action — that's Phase D (7-03).
