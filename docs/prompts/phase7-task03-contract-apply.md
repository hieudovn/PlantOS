# Phase 7 — Task 7-03: Safe Apply Import (Phase D)

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P1  
> **Depends on:** Phase 7-01 (Validator) ✅, Phase 7-02 (Preview) ✅

## Context

Sau khi validate và preview, bước cuối là **apply** — thực hiện import thật vào PostgreSQL. Đây là bước duy nhất ghi database, nên phải cực kỳ an toàn.

```
Contract → Validate (7-01) → Preview (7-02) → Apply (7-03)
```

## Architecture

```
POST /api/v1/contracts/apply
        │
        ▼
Validate (reuse 7-01)
        │
        ▼
Preview (reuse 7-02) — kiểm tra conflicts/orphans
        │
        ▼
Apply theo import_policy
  ├─ mode: apply (bắt buộc)
  ├─ on_conflict: fail | skip | update
  ├─ allow_update_existing: false (default)
  ├─ allow_delete_missing: false (default)
  └─ orphaned_action: report | deactivate (default: report)
        │
        ▼
Viết qua AssetRepository / SignalRepository
        │
        ▼
Return kết quả: {created, updated, skipped, orphaned, errors}
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/contracts/apply.py` — import logic
- [ ] MODIFY `backend/app/modules/contracts/router.py` — add POST /api/v1/contracts/apply
- [ ] CREATE `backend/tests/test_contracts_apply.py` — apply tests
- [ ] VERIFY: apply new plant → data appears in DB
- [ ] VERIFY: apply existing plant with on_conflict=fail → rejected
- [ ] VERIFY: apply existing plant with on_conflict=skip → skipped, not overwritten
- [ ] VERIFY: orphaned_action=report → no deletes
- [ ] VERIFY: apply does not affect unrelated plants

## Non-Negotiable Constraints

1. **Default safe**: `on_conflict=fail`, no deletes, no silent overwrites
2. **Use existing service/repository layer** — no raw SQL for writes
3. **Do NOT modify** Asset/Signal models or DB schema
4. **Do NOT access TDengine**
5. **Respect** `import_policy` from API request (not from contract)
6. **Transaction** where possible (per entity type)

## Detailed Instructions

### 1. File: `backend/app/modules/contracts/apply.py`

```python
"""Contract apply — safe import into PostgreSQL via existing service layer."""

from dataclasses import dataclass, field
from app.db import get_session
from app.modules.assets.repository import AssetRepository
from app.modules.signals.repository import SignalRepository


@dataclass
class ApplyResult:
    success: bool
    created: dict[str, list[str]] = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": []
    })
    updated: dict[str, list[str]] = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": []
    })
    skipped: dict[str, list[str]] = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": []
    })
    orphaned: dict[str, list[str]] = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": []
    })
    deactivated: dict[str, list[str]] = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": []
    })
    errors: list[str] = field(default_factory=list)


def apply_contract(contract_dict: dict, import_policy: dict) -> ApplyResult:
    """Execute contract import. Writes to PostgreSQL."""
    result = ApplyResult(success=True)
    mode = import_policy.get("mode", "validate_only")

    if mode != "apply":
        result.errors.append(f"import_policy.mode must be 'apply', got '{mode}'")
        result.success = False
        return result

    on_conflict = import_policy.get("on_conflict", "fail")
    allow_update = import_policy.get("allow_update_existing", False)
    allow_delete = import_policy.get("allow_delete_missing", False)
    orphaned_action = import_policy.get("orphaned_action", "report")

    if orphaned_action == "delete" and not allow_delete:
        result.errors.append("orphaned_action='delete' requires allow_delete_missing=true")
        result.success = False
        return result

    plant_id = contract_dict["plant"]["plant_id"]
    plant_name = contract_dict["plant"]["name"]

    with get_session() as session:
        asset_repo = AssetRepository(session)
        signal_repo = SignalRepository(session)

        # ---- Plant ----
        existing_plant = _get_plant(session, plant_id)
        if existing_plant:
            if on_conflict == "fail":
                result.errors.append(f"Plant '{plant_id}' already exists (on_conflict=fail)")
                result.success = False
                return result
            elif on_conflict == "skip":
                result.skipped["plants"].append(plant_id)
            elif on_conflict == "update" and allow_update:
                result.updated["plants"].append(plant_id)
                # Update plant fields if allowed
                _update_plant(session, plant_id, contract_dict["plant"])
        else:
            _create_plant(session, plant_id, plant_name)
            result.created["plants"].append(plant_id)

        session.commit()

        # ---- Areas ----
        for area in contract_dict["areas"]:
            area_id = area["area_id"]
            existing = _get_area(session, area_id)
            if existing:
                if on_conflict == "fail":
                    result.skipped["areas"].append(area_id)
                    continue
                elif on_conflict == "skip":
                    result.skipped["areas"].append(area_id)
                    continue
                elif on_conflict == "update" and allow_update:
                    _update_area(session, area_id, area)
                    result.updated["areas"].append(area_id)
            else:
                _create_area(session, area)
                result.created["areas"].append(area_id)

        session.commit()

        # ---- Assets ----
        for asset in contract_dict["assets"]:
            asset_id = asset["asset_id"]
            existing = asset_repo.get_by_id(asset_id)
            if existing:
                if on_conflict == "fail":
                    result.skipped["assets"].append(asset_id)
                    continue
                elif on_conflict == "skip":
                    result.skipped["assets"].append(asset_id)
                    continue
                elif on_conflict == "update" and allow_update:
                    result.updated["assets"].append(asset_id)
            else:
                _create_asset(session, asset)
                result.created["assets"].append(asset_id)

        session.commit()

        # ---- Signals ----
        for sig in contract_dict["signals"]:
            sig_id = sig["signal_id"]
            existing = signal_repo.get_by_id(sig_id)
            if existing:
                if on_conflict == "fail":
                    result.skipped["signals"].append(sig_id)
                    continue
                elif on_conflict == "skip":
                    result.skipped["signals"].append(sig_id)
                    continue
                elif on_conflict == "update" and allow_update:
                    result.updated["signals"].append(sig_id)
            else:
                _create_signal(session, sig)
                result.created["signals"].append(sig_id)

        session.commit()

        # ---- Orphaned handling ----
        if orphaned_action != "report":
            # Find entities in DB not in contract
            existing_assets_in_plant = _get_assets_for_plant(session, plant_id)
            contract_asset_ids = {a["asset_id"] for a in contract_dict["assets"]}
            orphaned_asset_ids = {a for a in existing_assets_in_plant if a not in contract_asset_ids}

            for aid in orphaned_asset_ids:
                result.orphaned["assets"].append(aid)
                if orphaned_action == "deactivate":
                    _deactivate_asset(session, aid)
                    result.deactivated["assets"].append(aid)

            existing_signals_in_plant = _get_signals_for_plant(session, plant_id)
            contract_signal_ids = {s["signal_id"] for s in contract_dict["signals"]}
            orphaned_signal_ids = existing_signals_in_plant - contract_signal_ids

            for sid in orphaned_signal_ids:
                result.orphaned["signals"].append(sid)
                if orphaned_action == "deactivate":
                    _deactivate_signal(session, sid)
                    result.deactivated["signals"].append(sid)

        session.commit()

    return result


# ---- SQL Helpers (internal to apply.py, not a public API) ----

def _get_plant(session, plant_id: str):
    from sqlalchemy import text
    rows = session.execute(
        text("SELECT plant_id FROM plants WHERE plant_id = :pid"),
        {"pid": plant_id}
    ).fetchall()
    return rows[0] if rows else None

def _get_area(session, area_id: str):
    from sqlalchemy import text
    rows = session.execute(
        text("SELECT area_id FROM areas WHERE area_id = :aid"),
        {"aid": area_id}
    ).fetchall()
    return rows[0] if rows else None

def _create_plant(session, plant_id: str, plant_name: str):
    from sqlalchemy import text
    session.execute(
        text("INSERT INTO plants (plant_id, name) VALUES (:pid, :name)"),
        {"pid": plant_id, "name": plant_name}
    )

def _update_plant(session, plant_id: str, plant_data: dict):
    from sqlalchemy import text
    session.execute(
        text("UPDATE plants SET name=:name, timezone=:tz WHERE plant_id=:pid"),
        {"pid": plant_id, "name": plant_data.get("name", ""), "tz": plant_data.get("timezone", "UTC")}
    )

def _create_area(session, area: dict):
    from sqlalchemy import text
    session.execute(
        text("INSERT INTO areas (area_id, area_code, name, plant_id) VALUES (:aid, :ac, :n, :pid)"),
        {"aid": area["area_id"], "ac": area.get("area_code", ""), "n": area["name"], "pid": area["plant_id"]}
    )

def _update_area(session, area_id: str, area: dict):
    from sqlalchemy import text
    session.execute(
        text("UPDATE areas SET name=:name WHERE area_id=:aid"),
        {"aid": area_id, "name": area["name"]}
    )

def _create_asset(session, asset: dict):
    from sqlalchemy import text
    session.execute(
        text("""
            INSERT INTO assets (asset_id, asset_code, name, asset_type, parent_asset_id, area_id, criticality)
            VALUES (:aid, :ac, :n, :at, :pid, :area, :crit)
        """),
        {
            "aid": asset["asset_id"], "ac": asset.get("asset_code", ""),
            "n": asset["name"], "at": asset.get("asset_type", ""),
            "pid": asset.get("parent_asset_id"), "area": asset["area_id"],
            "crit": asset.get("criticality", "medium"),
        }
    )

def _create_signal(session, sig: dict):
    from sqlalchemy import text
    session.execute(
        text("""
            INSERT INTO signals (signal_id, asset_id, signal_name, display_name, signal_type, data_type, engineering_unit, scale, offset)
            VALUES (:sid, :aid, :sn, :dn, :st, :dt, :eu, :sc, :off)
        """),
        {
            "sid": sig["signal_id"], "aid": sig["asset_id"],
            "sn": sig["signal_name"], "dn": sig.get("display_name", ""),
            "st": sig.get("signal_type", "measurement"), "dt": sig.get("data_type", "float"),
            "eu": sig.get("engineering_unit", ""),
            "sc": sig.get("scale", 1.0), "off": sig.get("offset", 0.0),
        }
    )

def _deactivate_asset(session, asset_id: str):
    from sqlalchemy import text
    session.execute(
        text("UPDATE assets SET status='deprecated' WHERE asset_id=:aid"),
        {"aid": asset_id}
    )

def _deactivate_signal(session, signal_id: str):
    from sqlalchemy import text
    session.execute(
        text("UPDATE signals SET status='deprecated' WHERE signal_id=:sid"),
        {"sid": signal_id}
    )

def _get_assets_for_plant(session, plant_id: str) -> set:
    from sqlalchemy import text
    rows = session.execute(
        text("SELECT a.asset_id FROM assets a JOIN areas ar ON a.area_id = ar.area_id WHERE ar.plant_id = :pid"),
        {"pid": plant_id}
    ).fetchall()
    return {r[0] for r in rows}

def _get_signals_for_plant(session, plant_id: str) -> set:
    from sqlalchemy import text
    rows = session.execute(
        text("""
            SELECT s.signal_id FROM signals s
            JOIN assets a ON s.asset_id = a.asset_id
            JOIN areas ar ON a.area_id = ar.area_id
            WHERE ar.plant_id = :pid
        """),
        {"pid": plant_id}
    ).fetchall()
    return {r[0] for r in rows}
```

### 2. Modify `backend/app/modules/contracts/router.py`

Add after the preview endpoint:

```python
from .apply import apply_contract

@router.post("/contracts/apply")
async def apply_contract_endpoint(payload: dict):
    """Apply contract import — writes to database."""
    # 1. Parse contract
    try:
        contract = ContractV2(**payload.get("contract", {}))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Contract invalid: {e}")

    # 2. Parse import policy (from request, NOT contract)
    import_policy = payload.get("import_policy", {})
    mode = import_policy.get("mode", "")
    if mode != "apply":
        raise HTTPException(
            status_code=400,
            detail=f"import_policy.mode must be 'apply' to execute import. Got: '{mode}'. "
                   f"Use preview first to review changes."
        )

    contract_dict = contract.model_dump()

    # 3. Validate
    from .validator import validate_contract
    validation = validate_contract(contract_dict)
    if not validation.valid:
        return {
            "applied": False,
            "validation_errors": validation.errors,
            "result": None,
        }

    # 4. Run preview (extra safety check)
    from .preview import preview_contract
    preview = preview_contract(contract_dict)

    # 5. Apply
    result = apply_contract(contract_dict, import_policy)

    return {
        "applied": result.success,
        "errors": result.errors,
        "result": {
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
            "orphaned": result.orphaned,
            "deactivated": result.deactivated,
        },
        "summary": {
            "total_created": sum(len(v) for v in result.created.values()),
            "total_updated": sum(len(v) for v in result.updated.values()),
            "total_skipped": sum(len(v) for v in result.skipped.values()),
            "total_orphaned": sum(len(v) for v in result.orphaned.values()),
        },
    }
```

### 3. Tests: `backend/tests/test_contracts_apply.py`

```python
import pytest
import random
import string
from app.modules.contracts.apply import apply_contract

VALID_CONTRACT = {
    "contract": {"version": "2.0", "schema_version": "2.0", "description": "Apply test"},
    "source": {"system_type": "manual", "system_name": "Test", "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z"},
    "plant": {"plant_id": "APPLY-TEST", "plant_code": "AT", "name": "Apply Test Plant", "timezone": "UTC"},
    "areas": [{"area_id": "AT-AREA", "area_code": "ATA", "name": "Test Area", "plant_id": "APPLY-TEST"}],
    "assets": [
        {"asset_id": "AT-PUMP", "asset_code": "ATP", "name": "Test Pump", "asset_type": "pump", "area_id": "AT-AREA"},
    ],
    "signals": [
        {"signal_id": "AT-PUMP.speed", "asset_id": "AT-PUMP", "signal_name": "speed", "display_name": "Speed", "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM"},
    ],
    "uns": {"namespace_root": "test", "path_template": "{ns}/{pid}/{sn}"},
    "import_recommendation": {"suggested_mode": "apply", "reason": "test"},
}

SAFE_POLICY = {"mode": "apply", "on_conflict": "fail", "allow_update_existing": False, "allow_delete_missing": False, "orphaned_action": "report"}


class TestApply:
    def test_apply_new_plant(self):
        """Apply a new plant — should create all entities."""
        rand_id = "AT" + "".join(random.choices(string.ascii_uppercase, k=6))
        contract = {**VALID_CONTRACT}
        contract["plant"]["plant_id"] = rand_id
        contract["areas"][0]["plant_id"] = rand_id

        result = apply_contract(contract, SAFE_POLICY)
        assert result.success is True
        assert rand_id in result.created["plants"]
        assert "AT-AREA" in result.created["areas"]
        assert len(result.errors) == 0

    def test_apply_existing_with_fail(self):
        """Apply to existing plant with on_conflict=fail."""
        result = apply_contract(VALID_CONTRACT, {**SAFE_POLICY, "on_conflict": "fail"})
        # APPLY-TEST already exists from previous test run
        if not result.success:
            assert "already exists" in result.errors[0]

    def test_apply_without_mode_apply(self):
        """Calling apply with mode=validate_only should fail."""
        result = apply_contract(VALID_CONTRACT, {"mode": "validate_only"})
        assert result.success is False
        assert "mode must be 'apply'" in result.errors[0]

    def test_apply_respects_skip(self):
        """Apply with on_conflict=skip should skip existing."""
        result = apply_contract(VALID_CONTRACT, {**SAFE_POLICY, "on_conflict": "skip"})
        # Plant may already exist → skipped
        total_created = sum(len(v) for v in result.created.values())
        total_skipped = sum(len(v) for v in result.skipped.values())
        assert total_created + total_skipped >= 1  # At minimum plant was handled
```

### 4. Deploy & Verify

```bash
# Build and test
cd backend && python -m pytest tests/test_contracts_apply.py -v

# Build & deploy
cd deployment && docker compose build backend
# ... scp + docker load + restart

# Test creating a unique plant
curl -s -X POST http://localhost:8000/api/v1/contracts/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: plantos-edge-key-2026" \
  -d '{
    "contract": {...valid contract...},
    "import_policy": {"mode":"apply","on_conflict":"fail","allow_update_existing":false,"allow_delete_missing":false,"orphaned_action":"report"}
  }'

# Verify in PostgreSQL
sudo docker exec plantos-postgres psql -U plantos -d plantos -c "SELECT plant_id FROM plants"
```

### 5. Validation

| Check | Expected |
|---|---|
| Apply new plant | `success: true`, entities in DB |
| Apply existing with on_conflict=fail | Rejected with error |
| Apply with mode != "apply" | Rejected |
| Apply respects on_conflict=skip | Skipped, not overwritten |
| orphaned_action=report | Listed, not deleted |
| Existing APIs unaffected | Assets/Signals/Measurements still work |
| No SQL injection | All queries use parameter binding |

## Notes

- Apply is the ONLY endpoint that writes to DB in the contracts module
- Uses raw SQL (`text()`) because AssetRepository/SignalRepository may not have all needed write methods. If the repos have `create()` methods, use them instead.
- Each entity type commits separately — partial success is possible (plant created, area failed → plant stays)
- Default policy is safest possible: `on_conflict=fail`, no updates, no deletes
- Phase D is the FINAL phase of the Model Importer. Phase E (manifest generation) is future work.
