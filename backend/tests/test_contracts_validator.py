"""Unit tests for Contract Validator — Phase 7 Task 7-01."""

import pytest
import yaml
from copy import deepcopy
from pathlib import Path
from app.modules.contracts.validator import validate_contract

VALID_MINIMAL = {
    "contract": {"version": "2.0", "schema_version": "2.0", "description": "Test"},
    "source": {
        "system_type": "manual", "system_name": "Test",
        "generated_by": "Test", "generated_at": "2026-07-01T00:00:00Z",
    },
    "plant": {"plant_id": "TEST", "plant_code": "TEST", "name": "Test Plant", "timezone": "UTC"},
    "areas": [{"area_id": "AREA1", "area_code": "AREA1", "name": "Area 1", "plant_id": "TEST"}],
    "assets": [{
        "asset_id": "PUMP01", "asset_code": "PUMP01", "name": "Pump",
        "asset_type": "pump", "area_id": "AREA1",
    }],
    "signals": [{
        "signal_id": "PUMP01.speed", "asset_id": "PUMP01", "signal_name": "speed",
        "display_name": "Speed", "signal_type": "measurement",
        "data_type": "float", "engineering_unit": "RPM",
    }],
    "uns": {
        "namespace_root": "test",
        "path_template": "{namespace_root}/{plant_id}/{signal_name}",
    },
    "import_recommendation": {"suggested_mode": "validate_only", "reason": "test"},
}


class TestValidatorMinimal:
    """Basic contract validation tests."""

    def test_valid_minimal(self):
        r = validate_contract(VALID_MINIMAL)
        assert r.valid is True

    def test_missing_plant_id(self):
        c = deepcopy(VALID_MINIMAL)
        c["plant"]["plant_id"] = ""
        r = validate_contract(c)
        assert r.valid is False
        assert any("plant.plant_id" in e["path"] for e in r.errors)

    def test_area_references_wrong_plant(self):
        c = deepcopy(VALID_MINIMAL)
        c["areas"][0]["plant_id"] = "WRONG"
        r = validate_contract(c)
        assert r.valid is False
        assert any("areas[0].plant_id" in e["path"] for e in r.errors)

    def test_signal_asset_not_found(self):
        c = deepcopy(VALID_MINIMAL)
        c["signals"][0]["asset_id"] = "NONEXISTENT"
        r = validate_contract(c)
        assert r.valid is False
        assert any("signals[0].asset_id" in e["path"] for e in r.errors)

    def test_duplicate_signal_id(self):
        c = deepcopy(VALID_MINIMAL)
        c["signals"].append(deepcopy(c["signals"][0]))
        r = validate_contract(c)
        assert r.valid is False
        assert any("Duplicate" in e["message"] for e in r.errors)

    def test_signal_id_format_mismatch(self):
        c = deepcopy(VALID_MINIMAL)
        c["signals"][0]["signal_id"] = "WRONG.format"
        r = validate_contract(c)
        assert r.valid is False
        assert any("Expected" in e["message"] for e in r.errors)

    def test_invalid_version_format(self):
        c = deepcopy(VALID_MINIMAL)
        c["contract"]["version"] = "not-a-version"
        r = validate_contract(c)
        assert r.valid is False
        assert any("contract.version" in e["path"] for e in r.errors)


class TestValidatorCrossReference:
    """Cross-reference validation rules V4-V6, V16."""

    def test_asset_area_not_found(self):
        c = deepcopy(VALID_MINIMAL)
        c["assets"][0]["area_id"] = "MISSING_AREA"
        r = validate_contract(c)
        assert r.valid is False
        assert any("assets[0].area_id" in e["path"] for e in r.errors)

    def test_parent_asset_not_found(self):
        c = deepcopy(VALID_MINIMAL)
        c["assets"].append({
            "asset_id": "PUMP02", "asset_code": "PUMP02", "name": "Pump 2",
            "asset_type": "pump", "area_id": "AREA1", "parent_asset_id": "NONEXISTENT",
        })
        r = validate_contract(c)
        assert r.valid is False
        assert any("parent_asset_id" in e["path"] for e in r.errors)

    def test_parent_asset_null_is_valid(self):
        c = deepcopy(VALID_MINIMAL)
        c["assets"][0]["parent_asset_id"] = None
        r = validate_contract(c)
        assert r.valid is True


class TestValidatorStatus:
    """Status and criticality validation V14-V15."""

    def test_invalid_asset_status(self):
        c = deepcopy(VALID_MINIMAL)
        c["assets"][0]["status"] = "invalid_status"
        r = validate_contract(c)
        assert r.valid is False
        assert any("assets[0].status" in e["path"] for e in r.errors)

    def test_invalid_signal_status(self):
        c = deepcopy(VALID_MINIMAL)
        c["signals"][0]["status"] = "bogus"
        r = validate_contract(c)
        assert r.valid is False
        assert any("signals[0].status" in e["path"] for e in r.errors)

    def test_invalid_criticality(self):
        c = deepcopy(VALID_MINIMAL)
        c["assets"][0]["criticality"] = "ultra"
        r = validate_contract(c)
        assert r.valid is False


class TestValidatorOpcua:
    """OPC UA binding validation V11, V16-V18."""

    def test_opcua_binding_refs_valid_signal(self):
        c = deepcopy(VALID_MINIMAL)
        c["bindings"] = {"opcua": [{"signal_id": "PUMP01.speed", "node_id": "ns=2;s=PUMP_SPEED"}]}
        r = validate_contract(c)
        assert r.valid is True

    def test_opcua_binding_refs_missing_signal(self):
        c = deepcopy(VALID_MINIMAL)
        c["bindings"] = {"opcua": [{"signal_id": "NONEXISTENT.x", "node_id": "ns=2;s=X"}]}
        r = validate_contract(c)
        assert r.valid is False
        assert any("bindings.opcua[0].signal_id" in e["path"] for e in r.errors)

    def test_opcua_invalid_node_id_format(self):
        c = deepcopy(VALID_MINIMAL)
        c["bindings"] = {"opcua": [{"signal_id": "PUMP01.speed", "node_id": "invalid"}]}
        r = validate_contract(c)
        assert r.valid is False
        assert any("bindings.opcua[0].node_id" in e["path"] for e in r.errors)

    def test_opcua_duplicate_node_id(self):
        c = deepcopy(VALID_MINIMAL)
        c["bindings"] = {
            "opcua": [
                {"signal_id": "PUMP01.speed", "node_id": "ns=2;s=SPEED"},
                {"signal_id": "PUMP01.speed", "node_id": "ns=2;s=SPEED"},
            ]
        }
        r = validate_contract(c)
        assert r.valid is False
        assert any("Duplicate" in e["message"] for e in r.errors)

    def test_virtual_factory_warns_unbound_signals(self):
        c = deepcopy(VALID_MINIMAL)
        c["source"]["system_type"] = "virtual_factory"
        # Add a second signal without OPC UA binding
        c["signals"].append({
            "signal_id": "PUMP01.temp", "asset_id": "PUMP01", "signal_name": "temp",
            "display_name": "Temp", "signal_type": "measurement",
            "data_type": "float", "engineering_unit": "degC",
        })
        # Only bind one of two signals
        c["bindings"] = {"opcua": [{"signal_id": "PUMP01.speed", "node_id": "ns=2;s=SPEED"}]}
        r = validate_contract(c)
        # Should have warnings, not errors
        assert r.valid is True
        assert len(r.warnings) > 0
        assert any("OPC UA binding" in w["message"] for w in r.warnings)


class TestValidatorWarnings:
    """Warning-level rules V12-V13."""

    def test_unrecognized_unit_warns(self):
        c = deepcopy(VALID_MINIMAL)
        c["signals"][0]["engineering_unit"] = "furlongs_per_fortnight"
        r = validate_contract(c)
        assert r.valid is True  # warnings don't invalidate
        assert any("Unrecognized unit" in w["message"] for w in r.warnings)

    def test_unrecognized_asset_type_warns(self):
        c = deepcopy(VALID_MINIMAL)
        c["assets"][0]["asset_type"] = "quantum_computer"
        r = validate_contract(c)
        assert r.valid is True  # warnings don't invalidate
        assert any("Unrecognized type" in w["message"] for w in r.warnings)


class TestValidatorExampleContract:
    """Validate the canonical example contract."""

    def test_example_contract_valid(self):
        example_path = Path(__file__).parents[2] / "examples" / "contracts" / "vf-compressor-train.contract.yaml"
        if not example_path.exists():
            pytest.skip("Example contract file not found")
        with open(example_path) as f:
            contract = yaml.safe_load(f)
        r = validate_contract(contract)
        assert r.valid is True, f"Expected valid, got errors: {r.errors}"
        assert len(r.errors) == 0, f"Unexpected errors: {r.errors}"

    def test_example_contract_summary(self):
        example_path = Path(__file__).parents[2] / "examples" / "contracts" / "vf-compressor-train.contract.yaml"
        if not example_path.exists():
            pytest.skip("Example contract file not found")
        with open(example_path) as f:
            contract = yaml.safe_load(f)
        r = validate_contract(contract)
        signals = contract.get("signals", [])
        assets = contract.get("assets", [])
        areas = contract.get("areas", [])
        assert r.valid is True
        assert len(areas) >= 1
        assert len(assets) >= 7
        assert len(signals) >= 26
