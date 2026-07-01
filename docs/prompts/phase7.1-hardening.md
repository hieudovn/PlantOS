# Phase 7.1 — Hardening (SA Conditional Approval)

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P0  
> **Context:** Solution Architect approved Phase 7 with conditions. Must complete these 6 items before Phase 8.

---

## 1. DB Migration: signals.status + plants.timezone

### Background

Contract v2 defines `status` on signals and `timezone` on plants. These columns may not exist in the current PostgreSQL schema.

### Tasks

- [ ] Check if `signals.status` column exists
- [ ] Check if `plants.timezone` column exists  
- [ ] Add missing columns via Alembic or raw SQL migration
- [ ] Set defaults: `status='active'`, `timezone='UTC'`
- [ ] Update existing rows to have default values

### Implementation

File: `backend/app/db/migrations/add_status_timezone.py` (or Alembic)

```python
"""Migration: add status to signals, timezone to plants."""

from app.db import get_session
from sqlalchemy import text

def upgrade():
    with get_session() as session:
        # signals.status
        try:
            session.execute(text(
                "ALTER TABLE signals ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active'"
            ))
            session.execute(text(
                "UPDATE signals SET status = 'active' WHERE status IS NULL"
            ))
        except Exception as e:
            print(f"signals.status: {e}")

        # plants.timezone
        try:
            session.execute(text(
                "ALTER TABLE plants ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'UTC'"
            ))
            session.execute(text(
                "UPDATE plants SET timezone = 'UTC' WHERE timezone IS NULL"
            ))
        except Exception as e:
            print(f"plants.timezone: {e}")

        session.commit()
```

Call this from `backend/app/main.py` startup or as a standalone script.

---

## 2. Update Seed Script for Contract v2

### Background

`backend/app/seed/vf_demo_plant.py` currently reads the v1 contract format. It must support v2 format.

### Tasks

- [ ] Read `examples/contracts/vf-compressor-train.contract.yaml` (v2 format)
- [ ] Fallback to v1 format (`examples/vf-plantos-contract.yaml`) if v2 not found
- [ ] Detect version from `contract.version` field
- [ ] Map v2 fields to existing seed logic

### Implementation

File: `backend/app/seed/vf_demo_plant.py`

Key changes:
```python
def load_contract():
    """Load contract v2 or fallback to v1."""
    v2_path = Path("examples/contracts/vf-compressor-train.contract.yaml")
    v1_path = Path("examples/vf-plantos-contract.yaml")
    
    if v2_path.exists():
        with open(v2_path) as f:
            contract = yaml.safe_load(f)
        if contract.get("contract", {}).get("version", "").startswith("2"):
            return contract, 2
    
    with open(v1_path) as f:
        return yaml.safe_load(f), 1

def seed_vf_demo_plant():
    contract, version = load_contract()
    
    if version == 2:
        plant_data = contract["plant"]
        areas_data = contract["areas"]
        assets_data = contract["assets"]
        signals_data = contract["signals"]
        # ... existing seed logic with v2 field names
    else:
        # ... existing v1 logic
```

---

## 3. Apply Technical Report

### Background

SA requires documentation of the Apply endpoint's technical behavior.

### Tasks

- [ ] CREATE `docs/contracts/apply-technical-report.md`

### Content

```markdown
# Apply Endpoint — Technical Report

## Transaction Boundary

Each entity type (plants, areas, assets, signals) is committed in a separate transaction:

```
BEGIN (plants) → CREATE/UPDATE → COMMIT
BEGIN (areas)  → CREATE/UPDATE → COMMIT  
BEGIN (assets) → CREATE/UPDATE → COMMIT
BEGIN (signals)→ CREATE/UPDATE → COMMIT
```

**Rationale:** Partial success is preferred over full rollback. If asset creation fails, the plant and areas are already persisted. This avoids orphaned data where possible while allowing forward progress.

## Rollback Behavior

- **No automatic rollback** across entity types. Each type commits independently.
- If a specific entity write fails, that entity is skipped (on_conflict=skip) or the entire apply aborts (on_conflict=fail).
- No data written in previous transactions is rolled back.

## Conflict Handling

| on_conflict | Behavior |
|---|---|
| `fail` | Abort apply immediately, return error |
| `skip` | Skip conflicting entity, continue with next |
| `update` | Update existing entity (only if allow_update_existing=true) |

## Idempotency

Apply with `on_conflict=skip` is idempotent:
- First apply: creates all entities
- Second apply with same contract: all entities skipped (already exist)
- Result: no duplicate data, no errors

Apply with `on_conflict=fail` is NOT idempotent:
- First apply: creates entities
- Second apply: aborts with conflict error

## Orphan Handling

| orphaned_action | Behavior |
|---|---|
| `report` (default) | List orphaned entities in response, no DB changes |
| `deactivate` | Set `status='deprecated'` on orphaned entities |
| `delete` | Hard delete (requires explicit allow_delete_missing=true) |

## Repository/Service Usage

| Entity | Read | Write |
|---|---|---|
| Plant | `PlantRepository` | Raw SQL `text()` — no existing create method |
| Area | Raw SQL — no dedicated repository | Raw SQL `text()` |
| Asset | `AssetRepository.get_by_id()` | Raw SQL `text()` — no existing create method |
| Signal | `SignalRepository.get_by_id()` | Raw SQL `text()` — no existing create method |

**Note:** Raw SQL is used for writes because Asset/Signal repositories currently lack `create()` methods. This is acceptable for MVP but should be migrated to repository methods in future.
```

---

## 4. Additional Tests

### Tasks

- [ ] ADD to `backend/tests/test_contracts_apply.py`:

```python
class TestApplyAdvanced:
    def test_apply_idempotent_with_skip(self):
        """Apply same contract twice with skip — second should skip all."""
        rand_id = "IDEM" + "".join(random.choices(string.ascii_uppercase, k=4))
        contract = _make_contract(rand_id)
        policy = {**SAFE_POLICY, "on_conflict": "skip"}
        
        r1 = apply_contract(contract, policy)
        assert r1.success
        total1 = sum(len(v) for v in r1.created.values())
        assert total1 >= 4  # plant + area + asset + signal
        
        r2 = apply_contract(contract, policy)
        assert r2.success
        total2_created = sum(len(v) for v in r2.created.values())
        total2_skipped = sum(len(v) for v in r2.skipped.values())
        assert total2_created == 0  # Nothing new
        assert total2_skipped >= 4  # All skipped

    def test_multi_level_asset_hierarchy(self):
        """Apply contract with 3-level asset tree."""
        contract = _make_hierarchy_contract()
        result = apply_contract(contract, SAFE_POLICY)
        assert result.success
        assets_created = result.created["assets"]
        assert len(assets_created) >= 3  # parent + 2 children

    def test_orphan_report(self):
        """Apply then preview with smaller contract → orphans detected."""
        rand_id = "ORPH" + "".join(random.choices(string.ascii_uppercase, k=4))
        # Step 1: Apply full contract (2 signals)
        full = _make_contract(rand_id, signal_count=2)
        r1 = apply_contract(full, SAFE_POLICY)
        assert r1.success
        
        # Step 2: Preview with smaller contract (1 signal)
        small = _make_contract(rand_id, signal_count=1)
        from app.modules.contracts.preview import preview_contract
        preview = preview_contract(small)
        assert len(preview.signals.orphans) >= 1  # Second signal orphaned

    def test_smoke_large_contract(self):
        """Validate a contract with 50+ signals."""
        contract = _make_contract("SMOKE", asset_count=10, signal_count=50)
        from app.modules.contracts.validator import validate_contract
        result = validate_contract(contract)
        assert result.valid is True

# Helper
def _make_contract(plant_id, asset_count=1, signal_count=1):
    areas = [{"area_id": f"{plant_id}-AREA", "area_code": f"{plant_id}A", "name": "Test Area", "plant_id": plant_id}]
    assets = []
    signals = []
    for i in range(asset_count):
        aid = f"{plant_id}-ASSET{i}"
        assets.append({"asset_id": aid, "asset_code": aid, "name": f"Asset {i}", "asset_type": "pump", "area_id": f"{plant_id}-AREA"})
        for j in range(signal_count // asset_count):
            signals.append({"signal_id": f"{aid}.sig{j}", "asset_id": aid, "signal_name": f"sig{j}", "display_name": f"Signal {j}", "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM"})
    return {
        "contract": {"version": "2.0", "schema_version": "2.0", "description": "Test"},
        "source": {"system_type": "manual", "system_name": "Test", "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z"},
        "plant": {"plant_id": plant_id, "plant_code": plant_id, "name": plant_id, "timezone": "UTC"},
        "areas": areas, "assets": assets, "signals": signals,
        "uns": {"namespace_root": "test", "path_template": "{ns}/{pid}/{sn}"},
        "import_recommendation": {"suggested_mode": "apply", "reason": "test"},
    }

def _make_hierarchy_contract():
    return {
        "contract": {"version": "2.0", "schema_version": "2.0", "description": "Hierarchy test"},
        "source": {"system_type": "manual", "system_name": "Test", "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z"},
        "plant": {"plant_id": "HIER-TEST", "plant_code": "HT", "name": "Hierarchy Test", "timezone": "UTC"},
        "areas": [{"area_id": "HT-AREA", "area_code": "HTA", "name": "Area", "plant_id": "HIER-TEST"}],
        "assets": [
            {"asset_id": "HT-ROOT", "asset_code": "HTR", "name": "Root", "asset_type": "production_line", "area_id": "HT-AREA", "parent_asset_id": None},
            {"asset_id": "HT-CHILD1", "asset_code": "HTC1", "name": "Child 1", "asset_type": "motor", "area_id": "HT-AREA", "parent_asset_id": "HT-ROOT"},
            {"asset_id": "HT-CHILD2", "asset_code": "HTC2", "name": "Child 2", "asset_type": "pump", "area_id": "HT-AREA", "parent_asset_id": "HT-ROOT"},
        ],
        "signals": [
            {"signal_id": "HT-ROOT.status", "asset_id": "HT-ROOT", "signal_name": "status", "display_name": "Status", "signal_type": "status", "data_type": "bool", "engineering_unit": ""},
            {"signal_id": "HT-CHILD1.speed", "asset_id": "HT-CHILD1", "signal_name": "speed", "display_name": "Speed", "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM"},
        ],
        "uns": {"namespace_root": "test", "path_template": "{ns}/{pid}/{sn}"},
        "import_recommendation": {"suggested_mode": "apply", "reason": "test"},
    }
```

---

## 5. Wording Fix

### Background

SA noted: "Contract v2 không phải toàn bộ CDM. Contract v2 là Operational Model Import Contract aligned with PlantOS CDM."

### Tasks

- [ ] UPDATE `docs/contracts/plantos-integration-contract-spec.md` — title and intro
- [ ] UPDATE `docs/adr/ADR-0006-integration-contract-v2.md` — description
- [ ] UPDATE `schemas/plantos-integration-contract.schema.json` — `$id` and `title`
- [ ] UPDATE `examples/contracts/vf-compressor-train.contract.yaml` — header comment

### Changes

**Old wording:**
```
PlantOS Integration Contract
PlantOS Integration Contract v2.0
```

**New wording:**
```
PlantOS Operational Model Import Contract
Aligned with PlantOS CDM (Canonical Data Model)
```

**In schema:**
```json
{
  "$id": "https://plantos.avenue.dev/schemas/operational-model-import-contract-v2.schema.json",
  "title": "PlantOS Operational Model Import Contract",
  "description": "Import contract for industrial asset models, aligned with PlantOS CDM."
}
```

---

## 6. No Phase E

Phase E (Manifest Generation) is **blocked** until Phase 7.1 is reviewed and approved by SA.

---

## Implementation Order

```
1. DB Migration (30 min)     ← No dependencies
2. Wording Fix (15 min)      ← No dependencies
3. Technical Report (30 min) ← No dependencies
4. Update Seed Script (1h)   ← Depends on #1
5. Additional Tests (1h)     ← Depends on #1, #4
```

## Deploy & Verify

```bash
# Run migration
cd backend && python -m app.db.migrations.add_status_timezone

# Run all tests
python -m pytest tests/test_contracts_validator.py tests/test_contracts_preview.py tests/test_contracts_apply.py -v

# Build & deploy
cd deployment && docker compose build backend
# ... scp + docker load + restart

# Verify existing functionality
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/plants
```
