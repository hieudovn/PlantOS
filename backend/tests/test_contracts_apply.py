"""Unit tests for Contract Apply — Phase 7 Task 7-03."""

from copy import deepcopy
import random
import string

import pytest

from app.modules.contracts.apply import apply_contract

VALID_CONTRACT = {
    "contract": {"version": "2.0", "schema_version": "2.0", "description": "Apply test"},
    "source": {
        "system_type": "manual", "system_name": "Test",
        "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z",
    },
    "plant": {"plant_id": "APPLY-TEST", "plant_code": "AT", "name": "Apply Test Plant", "timezone": "UTC"},
    "areas": [{"area_id": "AT-AREA", "area_code": "ATA", "name": "Test Area", "plant_id": "APPLY-TEST"}],
    "assets": [
        {"asset_id": "AT-PUMP", "asset_code": "ATP", "name": "Test Pump",
         "asset_type": "pump", "area_id": "AT-AREA"},
    ],
    "signals": [
        {"signal_id": "AT-PUMP.speed", "asset_id": "AT-PUMP", "signal_name": "speed",
         "display_name": "Speed", "signal_type": "measurement",
         "data_type": "float", "engineering_unit": "RPM"},
    ],
    "uns": {"namespace_root": "test", "path_template": "{ns}/{pid}/{sn}"},
    "import_recommendation": {"suggested_mode": "apply", "reason": "test"},
}

SAFE_POLICY = {
    "mode": "apply",
    "on_conflict": "fail",
    "allow_update_existing": False,
    "allow_delete_missing": False,
    "orphaned_action": "report",
}


def _random_id(prefix: str = "AT") -> str:
    return prefix + "".join(random.choices(string.ascii_uppercase, k=6))


class TestApplyNewPlant:
    """Apply a new plant — should create all entities."""

    def test_apply_new_plant_creates_everything(self):
        rand_id = _random_id()
        rand_area = _random_id("AREA")
        rand_asset = _random_id("ASSET")
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = rand_id
        contract["plant"]["name"] = f"Test Plant {rand_id}"
        contract["areas"][0]["plant_id"] = rand_id
        contract["areas"][0]["area_id"] = rand_area
        contract["areas"][0]["name"] = f"Area {rand_area}"
        contract["assets"][0]["area_id"] = rand_area
        contract["assets"][0]["asset_id"] = rand_asset
        contract["assets"][0]["name"] = f"Asset {rand_asset}"
        contract["signals"][0]["asset_id"] = rand_asset
        rand_signal = f"{rand_asset}.speed"
        contract["signals"][0]["signal_id"] = rand_signal

        result = apply_contract(contract, SAFE_POLICY)
        assert result.success is True, f"Errors: {result.errors}"
        assert rand_id in result.created["plants"], f"Expected plant in created, got {result.created}"
        assert rand_area in result.created["areas"]
        assert rand_asset in result.created["assets"]
        assert rand_signal in result.created["signals"]
        assert len(result.errors) == 0

    def test_apply_twice_same_plant_fails(self):
        """Applying the same new plant twice should fail on second attempt."""
        rand_id = _random_id()
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = rand_id
        contract["areas"][0]["plant_id"] = rand_id

        # First apply — succeeds
        r1 = apply_contract(contract, SAFE_POLICY)
        assert r1.success is True
        assert rand_id in r1.created["plants"]

        # Second apply — should fail (on_conflict=fail)
        r2 = apply_contract(contract, SAFE_POLICY)
        assert r2.success is False
        assert any("already exists" in e for e in r2.errors)

    def test_apply_without_mode_apply_rejected(self):
        """Calling apply with mode=validate_only should fail."""
        result = apply_contract(VALID_CONTRACT, {"mode": "validate_only"})
        assert result.success is False
        assert any("mode must be 'apply'" in e for e in result.errors)


class TestApplyConflictSkip:
    """Apply with on_conflict=skip should skip existing entities."""

    def test_apply_with_skip_does_not_fail(self):
        rand_id = _random_id()
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = rand_id
        contract["areas"][0]["plant_id"] = rand_id

        skip_policy = {**SAFE_POLICY, "on_conflict": "skip"}

        # First apply creates
        r1 = apply_contract(contract, skip_policy)
        assert r1.success is True
        assert rand_id in r1.created["plants"]

        # Second apply skips
        r2 = apply_contract(contract, skip_policy)
        assert r2.success is True
        assert rand_id in r2.skipped["plants"]
        assert len(r2.created["plants"]) == 0


class TestApplyExisting:
    """Apply against an existing plant (VF-DEMO)."""

    def test_apply_vfdemo_with_fail_rejected(self):
        """VF-DEMO exists → on_conflict=fail should reject."""
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = "VF-DEMO"
        contract["areas"][0]["plant_id"] = "VF-DEMO"

        result = apply_contract(contract, SAFE_POLICY)
        assert result.success is False
        assert any("already exists" in e for e in result.errors)

    def test_apply_vfdemo_with_skip_ok(self):
        """VF-DEMO exists → on_conflict=skip should skip."""
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = "VF-DEMO"
        contract["areas"][0]["plant_id"] = "VF-DEMO"

        skip_policy = {**SAFE_POLICY, "on_conflict": "skip"}
        result = apply_contract(contract, skip_policy)
        assert result.success is True
        assert "VF-DEMO" in result.skipped["plants"]


class TestApplySafety:
    """Safety checks — dangerous configs must be rejected."""

    def test_delete_without_allow_delete_fails(self):
        """orphaned_action=delete without allow_delete_missing=true should fail."""
        result = apply_contract(
            VALID_CONTRACT,
            {**SAFE_POLICY, "orphaned_action": "delete"},
        )
        assert result.success is False
        assert any("orphaned_action='delete' requires" in e for e in result.errors)


# =========================================================================
# Advanced tests — Phase 7.1 hardening
# =========================================================================


def _make_contract(plant_id, asset_count=1, signal_count=1):
    """Helper: create a contract dict with N assets and M signals."""
    areas = [{"area_id": f"{plant_id}-AREA", "area_code": f"{plant_id}A",
              "name": "Test Area", "plant_id": plant_id}]
    assets = []
    signals = []
    for i in range(asset_count):
        aid = f"{plant_id}-ASSET{i}"
        assets.append({
            "asset_id": aid, "asset_code": aid, "name": f"Asset {i}",
            "asset_type": "pump", "area_id": f"{plant_id}-AREA",
        })
        for j in range(signal_count // asset_count):
            signals.append({
                "signal_id": f"{aid}.sig{j}", "asset_id": aid,
                "signal_name": f"sig{j}", "display_name": f"Signal {j}",
                "signal_type": "measurement", "data_type": "float",
                "engineering_unit": "RPM",
            })
    return {
        "contract": {"version": "2.0", "schema_version": "2.0", "description": "Test"},
        "source": {"system_type": "manual", "system_name": "Test",
                   "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z"},
        "plant": {"plant_id": plant_id, "plant_code": plant_id,
                  "name": plant_id, "timezone": "UTC"},
        "areas": areas, "assets": assets, "signals": signals,
        "uns": {"namespace_root": "test", "path_template": "{ns}/{pid}/{sn}"},
        "import_recommendation": {"suggested_mode": "apply", "reason": "test"},
    }


def _make_hierarchy_contract():
    """Helper: contract with 3-level asset hierarchy."""
    return {
        "contract": {"version": "2.0", "schema_version": "2.0", "description": "Hierarchy test"},
        "source": {"system_type": "manual", "system_name": "Test",
                   "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z"},
        "plant": {"plant_id": "HIER-TEST", "plant_code": "HT",
                  "name": "Hierarchy Test", "timezone": "UTC"},
        "areas": [{"area_id": "HT-AREA", "area_code": "HTA",
                   "name": "Area", "plant_id": "HIER-TEST"}],
        "assets": [
            {"asset_id": "HT-ROOT", "asset_code": "HTR", "name": "Root",
             "asset_type": "production_line", "area_id": "HT-AREA",
             "parent_asset_id": None},
            {"asset_id": "HT-CHILD1", "asset_code": "HTC1", "name": "Child 1",
             "asset_type": "motor", "area_id": "HT-AREA",
             "parent_asset_id": "HT-ROOT"},
            {"asset_id": "HT-CHILD2", "asset_code": "HTC2", "name": "Child 2",
             "asset_type": "pump", "area_id": "HT-AREA",
             "parent_asset_id": "HT-ROOT"},
        ],
        "signals": [
            {"signal_id": "HT-ROOT.status", "asset_id": "HT-ROOT",
             "signal_name": "status", "display_name": "Status",
             "signal_type": "status", "data_type": "bool", "engineering_unit": ""},
            {"signal_id": "HT-CHILD1.speed", "asset_id": "HT-CHILD1",
             "signal_name": "speed", "display_name": "Speed",
             "signal_type": "measurement", "data_type": "float",
             "engineering_unit": "RPM"},
        ],
        "uns": {"namespace_root": "test", "path_template": "{ns}/{pid}/{sn}"},
        "import_recommendation": {"suggested_mode": "apply", "reason": "test"},
    }


class TestApplyAdvanced:
    """Advanced hardening tests — Phase 7.1."""

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
