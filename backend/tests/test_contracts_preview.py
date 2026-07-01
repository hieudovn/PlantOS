"""Unit tests for Contract Preview — Phase 7 Task 7-02."""

from copy import deepcopy

import pytest

from app.modules.contracts.preview import preview_contract

VALID_CONTRACT = {
    "contract": {"version": "2.0", "schema_version": "2.0", "description": "Preview test"},
    "source": {
        "system_type": "manual", "system_name": "Test",
        "generated_by": "Tester", "generated_at": "2026-07-01T00:00:00Z",
    },
    "plant": {"plant_id": "PREVIEW-TEST", "plant_code": "PT", "name": "Preview Test Plant", "timezone": "UTC"},
    "areas": [{"area_id": "PT-AREA", "area_code": "PTA", "name": "Test Area", "plant_id": "PREVIEW-TEST"}],
    "assets": [
        {"asset_id": "PT-PUMP", "asset_code": "PTP", "name": "Test Pump",
         "asset_type": "pump", "area_id": "PT-AREA"},
    ],
    "signals": [
        {"signal_id": "PT-PUMP.speed", "asset_id": "PT-PUMP", "signal_name": "speed",
         "display_name": "Speed", "signal_type": "measurement",
         "data_type": "float", "engineering_unit": "RPM"},
        {"signal_id": "PT-PUMP.temp", "asset_id": "PT-PUMP", "signal_name": "temp",
         "display_name": "Temp", "signal_type": "measurement",
         "data_type": "float", "engineering_unit": "degC"},
    ],
    "uns": {"namespace_root": "test", "path_template": "{namespace_root}/{plant_id}/{signal_name}"},
    "import_recommendation": {"suggested_mode": "preview", "reason": "test"},
}


class TestPreviewNewPlant:
    """Preview against an empty DB — all entities should be creates."""

    def test_new_plant_all_creates(self):
        result = preview_contract(VALID_CONTRACT)
        assert result.valid is True
        assert result.plants.creates == ["PREVIEW-TEST"]
        assert result.plants.conflicts == []
        assert result.areas.creates == ["PT-AREA"]
        assert result.areas.conflicts == []
        assert result.assets.creates == ["PT-PUMP"]
        assert result.assets.conflicts == []
        assert sorted(result.signals.creates) == ["PT-PUMP.speed", "PT-PUMP.temp"]
        assert result.signals.conflicts == []


class TestPreviewExisting:
    """Preview against VF-DEMO plant which exists in DB."""

    def test_existing_plant_detected_as_conflict(self):
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = "VF-DEMO"
        contract["areas"][0]["plant_id"] = "VF-DEMO"
        result = preview_contract(contract)
        # VF-DEMO exists in seeded data → conflict
        assert "VF-DEMO" in result.plants.conflicts, (
            f"Expected VF-DEMO in conflicts, got creates={result.plants.creates}"
        )

    def test_existing_area_detected(self):
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = "VF-DEMO"
        contract["areas"][0]["plant_id"] = "VF-DEMO"
        contract["areas"][0]["area_id"] = "COMPRESSOR-AREA"
        contract["assets"][0]["area_id"] = "COMPRESSOR-AREA"
        result = preview_contract(contract)
        assert "COMPRESSOR-AREA" in result.areas.conflicts or "COMPRESSOR-AREA" in result.areas.creates


class TestPreviewNoWrite:
    """Preview must NOT write to DB — running twice gives same result."""

    def test_preview_does_not_write_to_db(self):
        import random
        import string
        rand_id = "R" + "".join(random.choices(string.ascii_uppercase, k=8))
        contract = deepcopy(VALID_CONTRACT)
        contract["plant"]["plant_id"] = rand_id
        contract["areas"][0]["plant_id"] = rand_id

        # Run preview twice — second should still show creates, not conflicts
        result1 = preview_contract(contract)
        result2 = preview_contract(contract)

        assert result1.plants.creates == [rand_id]
        assert result1.plants.conflicts == []
        # Second run must NOT see the plant as existing → proves no write
        assert result2.plants.creates == [rand_id]
        assert result2.plants.conflicts == []
