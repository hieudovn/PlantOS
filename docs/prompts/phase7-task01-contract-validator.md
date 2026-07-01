# Phase 7 — Task 7-01: Contract Validator (Phase B)

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P1

## Context

PlantOS cần một Contract Validator để kiểm tra tính hợp lệ của Integration Contract trước khi import. Validator chỉ validate — **không ghi database, không đụng vào module hiện có.**

## Architecture

```
Contract YAML → JSON Schema (structural) → Cross-reference validator → Response
                                                    ↓
                                          UNS Path Generator
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/contracts/__init__.py`
- [ ] CREATE `backend/app/modules/contracts/schemas.py` — Pydantic models mirroring contract v2
- [ ] CREATE `backend/app/modules/contracts/validator.py` — cross-reference validation
- [ ] CREATE `backend/app/modules/contracts/router.py` — POST /api/v1/contracts/validate
- [ ] MODIFY `backend/app/api/v1.py` — register contracts router
- [ ] CREATE `backend/tests/test_contracts_validator.py` — unit tests
- [ ] VERIFY: validate example contract returns valid=true
- [ ] VERIFY: invalid contracts caught correctly

## Non-Negotiable Constraints

1. **Do NOT write to PostgreSQL** — validator is read-only
2. **Do NOT modify existing Asset/Signal/Measurement modules**
3. **Do NOT access TDengine**
4. **Do NOT change frontend UI**
5. **Do NOT change Edge Agent behavior**

## Detailed Instructions

### 1. File: `backend/app/modules/contracts/schemas.py`

Create Pydantic models that mirror the contract v2 structure. All core sections required, extensions optional.

```python
"""Contract v2 Pydantic models — mirrors JSON Schema."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContractMeta(BaseModel):
    version: str
    schema_version: str = "2.0"
    description: str


class SourceInfo(BaseModel):
    system_type: str  # virtual_factory | opcua | scada | manual | csv | engineering_tool
    system_name: str
    owner: Optional[str] = None
    generated_by: str
    generated_at: datetime


class PlantDef(BaseModel):
    plant_id: str
    plant_code: str
    name: str
    description: Optional[str] = None
    timezone: str = "UTC"
    status: str = "active"


class AreaDef(BaseModel):
    area_id: str
    area_code: str
    name: str
    plant_id: str


class AssetDef(BaseModel):
    asset_id: str
    asset_code: str
    name: str
    asset_type: str
    parent_asset_id: Optional[str] = None
    area_id: str
    criticality: str = "medium"
    status: str = "active"


class SignalDef(BaseModel):
    signal_id: str
    asset_id: str
    signal_name: str
    display_name: str
    signal_type: str = "measurement"
    data_type: str = "float"
    engineering_unit: str
    scale: float = 1.0
    offset: float = 0.0
    status: str = "active"


class UnsPolicy(BaseModel):
    namespace_root: str
    path_template: str
    normalize_case: str = "lower"
    separator: str = "/"


class ImportRecommendation(BaseModel):
    suggested_mode: str
    reason: str
    notes: Optional[str] = None


class OpcuaBinding(BaseModel):
    signal_id: str
    node_id: str
    scale: float = 1.0
    offset: float = 0.0


class Bindings(BaseModel):
    opcua: list[OpcuaBinding] = Field(default_factory=list)


class SimulationBehavior(BaseModel):
    signal_id: str
    pattern: str
    mid: Optional[float] = None
    amplitude: Optional[float] = None
    noise: Optional[float] = None
    frequency_hz: Optional[float] = None
    step_size: Optional[float] = None
    bounds_min: Optional[float] = None
    bounds_max: Optional[float] = None
    unit: Optional[str] = None


class Simulation(BaseModel):
    behaviors: dict[str, SimulationBehavior] = Field(default_factory=dict)


class ContractV2(BaseModel):
    contract: ContractMeta
    source: SourceInfo
    plant: PlantDef
    areas: list[AreaDef]
    assets: list[AssetDef]
    signals: list[SignalDef]
    uns: UnsPolicy
    import_recommendation: ImportRecommendation
    bindings: Optional[Bindings] = None
    simulation: Optional[Simulation] = None
    extensions: Optional[dict] = None
```

### 2. File: `backend/app/modules/contracts/validator.py`

Implement all 18 validation rules from Section 7 of the spec. Key rules:

```python
"""Contract validator — structural + cross-reference validation."""

import re
from typing import Any

VALID_ASSET_TYPES = {
    "compressor_train", "compressor", "pump", "motor", "turbine", "fan", "gearbox",
    "tank", "vessel", "heat_exchanger", "cooling_tower", "boiler", "furnace",
    "reactor", "column", "bearing_assembly", "seal_system", "lubrication_system",
    "cooling_system", "transformer", "switchgear", "breaker", "feeder",
    "motor_control_center", "vfd", "valve", "control_valve", "safety_valve",
    "pipeline", "filter", "strainer", "sensor_array", "analyzer", "flow_meter",
    "transmitter", "production_line", "work_cell", "conveyor", "robot", "cnc_machine",
}

VALID_UNITS = {
    "kPa", "MPa", "bar", "psi", "Pa", "mbar",
    "degC", "degF", "K",
    "m3/h", "Nm3/h", "L/min", "kg/h", "t/h", "m3/s",
    "RPM", "Hz", "m/s", "rad/s",
    "A", "V", "kW", "kVA", "kWh", "PF", "ohm",
    "mm/s", "um", "mil", "g",
    "m", "mm", "cm", "%",
    "kg", "t", "g",
    "N", "kN", "Nm", "kNm",
    "kJ", "MJ", "kWh", "MWh", "W", "MW",
    "kg/m3", "g/cm3", "cSt", "cP",
}

VALID_CRITICALITY = {"critical", "high", "medium", "low"}
VALID_STATUS = {"active", "inactive", "deprecated"}
VALID_SIGNAL_TYPES = {"measurement", "status", "setpoint", "command"}
VALID_DATA_TYPES = {"float", "bool", "int", "string"}
OPCUA_NODE_PATTERN = re.compile(r"^ns=\d+;s=[A-Z][A-Z0-9_]*$")


class ValidationResult:
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def error(self, path: str, message: str):
        self.errors.append({"path": path, "message": message})

    def warning(self, path: str, message: str):
        self.warnings.append({"path": path, "message": message})


def validate_contract(contract: dict) -> ValidationResult:
    """Validate a contract dict against all rules. Does NOT access database."""
    result = ValidationResult()

    plant = contract.get("plant", {})
    areas = contract.get("areas", [])
    assets = contract.get("assets", [])
    signals = contract.get("signals", [])
    bindings = contract.get("bindings", {})
    source = contract.get("source", {})

    # Build lookup sets
    area_ids = {a["area_id"] for a in areas}
    asset_ids = {a["asset_id"] for a in assets}
    signal_ids = {s["signal_id"] for s in signals}

    # V1: contract version valid semver
    version = contract.get("contract", {}).get("version", "")
    if not re.match(r"^\d+\.\d+(\.\d+)?$", version):
        result.error("contract.version", f"Invalid semver: '{version}'")

    # V2: plant_id present, valid format
    plant_id = plant.get("plant_id", "")
    if not re.match(r"^[A-Z][A-Z0-9-]*$", plant_id):
        result.error("plant.plant_id", f"Invalid format: '{plant_id}'")

    # V3: area.plant_id matches plant.plant_id
    for i, area in enumerate(areas):
        if area.get("plant_id") != plant_id:
            result.error(f"areas[{i}].plant_id",
                         f"Area plant_id '{area.get('plant_id')}' != plant.plant_id '{plant_id}'")

    # V4: asset.area_id exists
    for i, asset in enumerate(assets):
        aid = asset.get("area_id", "")
        if aid not in area_ids:
            result.error(f"assets[{i}].area_id", f"Area '{aid}' not found")

    # V5: asset.parent_asset_id exists or null
    for i, asset in enumerate(assets):
        pid = asset.get("parent_asset_id")
        if pid is not None and pid not in asset_ids:
            result.error(f"assets[{i}].parent_asset_id", f"Parent asset '{pid}' not found")

    # V6: signal.asset_id exists
    for i, sig in enumerate(signals):
        aid = sig.get("asset_id", "")
        if aid not in asset_ids:
            result.error(f"signals[{i}].asset_id", f"Asset '{aid}' not found")

    # V7-V9: uniqueness
    _check_duplicates(result, areas, "area_id", "areas")
    _check_duplicates(result, assets, "asset_id", "assets")
    _check_duplicates(result, signals, "signal_id", "signals")

    # V10: signal_id format {ASSET_ID}.{signal_name}
    for i, sig in enumerate(signals):
        sid = sig.get("signal_id", "")
        aid = sig.get("asset_id", "")
        sname = sig.get("signal_name", "")
        expected = f"{aid}.{sname}"
        if sid != expected:
            result.error(f"signals[{i}].signal_id",
                         f"Expected '{expected}', got '{sid}'")

    # V11: opcua_node_id format
    opcua = bindings.get("opcua", [])
    for i, b in enumerate(opcua):
        nid = b.get("node_id", "")
        if not OPCUA_NODE_PATTERN.match(nid):
            result.error(f"bindings.opcua[{i}].node_id", f"Invalid OPC UA NodeId: '{nid}'")

    # V12: engineering_unit recognized
    for i, sig in enumerate(signals):
        unit = sig.get("engineering_unit", "")
        if unit and unit not in VALID_UNITS:
            result.warning(f"signals[{i}].engineering_unit", f"Unrecognized unit: '{unit}'")

    # V13: asset_type recognized
    for i, asset in enumerate(assets):
        atype = asset.get("asset_type", "")
        if atype and atype not in VALID_ASSET_TYPES:
            result.warning(f"assets[{i}].asset_type", f"Unrecognized type: '{atype}'")

    # V14: status valid
    for i, asset in enumerate(assets):
        if asset.get("status", "") not in VALID_STATUS:
            result.error(f"assets[{i}].status", f"Invalid status: '{asset.get('status')}'")
    for i, sig in enumerate(signals):
        if sig.get("status", "") not in VALID_STATUS:
            result.error(f"signals[{i}].status", f"Invalid status: '{sig.get('status')}'")

    # V15: criticality valid
    for i, asset in enumerate(assets):
        if asset.get("criticality", "") not in VALID_CRITICALITY:
            result.error(f"assets[{i}].criticality", f"Invalid criticality: '{asset.get('criticality')}'")

    # V16: opcua binding signal_id references existing signal
    for i, b in enumerate(opcua):
        sid = b.get("signal_id", "")
        if sid not in signal_ids:
            result.error(f"bindings.opcua[{i}].signal_id", f"Signal '{sid}' not found")

    # V17: no duplicate opcua node_ids
    node_ids = [b.get("node_id") for b in opcua]
    seen = set()
    for i, nid in enumerate(node_ids):
        if nid and nid in seen:
            result.error(f"bindings.opcua[{i}].node_id", f"Duplicate OPC UA NodeId: '{nid}'")
        seen.add(nid)

    # V18: warning if signal has no opcua binding (when system_type expects it)
    src_type = source.get("system_type", "")
    if src_type in ("virtual_factory", "opcua"):
        bound_signals = {b.get("signal_id") for b in opcua}
        for sig_id in signal_ids:
            if sig_id not in bound_signals:
                result.warning(f"signals[{sig_id}]", f"Signal has no OPC UA binding (system_type={src_type})")

    return result


def _check_duplicates(result: ValidationResult, items: list, key: str, category: str):
    seen = {}
    for i, item in enumerate(items):
        val = item.get(key, "")
        if val and val in seen:
            result.error(f"{category}[{i}].{key}", f"Duplicate {key}: '{val}' (first at index {seen[val]})")
        seen[val] = i


def generate_uns_path(signal: dict, area: dict, asset: dict, plant: dict, uns_policy: dict) -> str:
    """Generate UNS path from contract entities."""
    template = uns_policy.get("path_template", "{namespace_root}/{plant_id}/{area_id}/{asset_id}/{signal_name}")
    separator = uns_policy.get("separator", "/")

    path = template.format(
        namespace_root=uns_policy.get("namespace_root", ""),
        plant_id=plant.get("plant_id", ""),
        area_id=area.get("area_id", ""),
        asset_id=asset.get("asset_id", ""),
        signal_name=signal.get("signal_name", ""),
    )

    if uns_policy.get("normalize_case") == "lower":
        path = path.lower()

    return path.replace("/", separator)
```

### 3. File: `backend/app/modules/contracts/router.py`

```python
"""Contract validation API."""

from fastapi import APIRouter, HTTPException
from .schemas import ContractV2
from .validator import validate_contract, generate_uns_path

router = APIRouter()


@router.post("/contracts/validate")
async def validate_contract_endpoint(payload: dict):
    """Validate a PlantOS Integration Contract. Does NOT write to database."""
    try:
        # Parse and validate structure via Pydantic
        contract = ContractV2(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Contract structure invalid: {e}")

    # Cross-reference validation
    contract_dict = contract.model_dump()
    result = validate_contract(contract_dict)

    # Generate UNS paths for each signal
    asset_map = {a["asset_id"]: a for a in contract_dict["assets"]}
    area_map = {a["area_id"]: a for a in contract_dict["areas"]}
    uns_paths = {}
    for sig in contract_dict["signals"]:
        asset = asset_map.get(sig["asset_id"])
        if asset:
            area = area_map.get(asset["area_id"])
            if area:
                path = generate_uns_path(
                    sig, area, asset,
                    contract_dict["plant"],
                    contract_dict["uns"]
                )
                uns_paths[sig["signal_id"]] = path

    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "summary": {
            "plants": 1,
            "areas": len(contract_dict["areas"]),
            "assets": len(contract_dict["assets"]),
            "signals": len(contract_dict["signals"]),
        },
        "uns_paths": uns_paths,
    }
```

### 4. Register in `backend/app/api/v1.py`

```python
from app.modules.contracts.router import router as contracts_router

# Add after other routers:
router.include_router(contracts_router, tags=["Contracts"])
```

### 5. Tests: `backend/tests/test_contracts_validator.py`

Create test file with at minimum:

```python
import pytest
from app.modules.contracts.validator import validate_contract

VALID_MINIMAL = {
    "contract": {"version": "2.0", "schema_version": "2.0", "description": "Test"},
    "source": {"system_type": "manual", "system_name": "Test", "generated_by": "Test", "generated_at": "2026-07-01T00:00:00Z"},
    "plant": {"plant_id": "TEST", "plant_code": "TEST", "name": "Test Plant", "timezone": "UTC"},
    "areas": [{"area_id": "AREA1", "area_code": "AREA1", "name": "Area 1", "plant_id": "TEST"}],
    "assets": [{"asset_id": "PUMP01", "asset_code": "PUMP01", "name": "Pump", "asset_type": "pump", "area_id": "AREA1"}],
    "signals": [{"signal_id": "PUMP01.speed", "asset_id": "PUMP01", "signal_name": "speed", "display_name": "Speed", "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM"}],
    "uns": {"namespace_root": "test", "path_template": "{namespace_root}/{plant_id}/{signal_name}"},
    "import_recommendation": {"suggested_mode": "validate_only", "reason": "test"},
}

class TestValidator:
    def test_valid_minimal(self):
        r = validate_contract(VALID_MINIMAL)
        assert r.valid is True

    def test_missing_plant_id(self):
        c = {**VALID_MINIMAL, "plant": {**VALID_MINIMAL["plant"], "plant_id": ""}}
        r = validate_contract(c)
        assert r.valid is False

    def test_area_references_wrong_plant(self):
        c = {**VALID_MINIMAL}
        c["areas"][0]["plant_id"] = "WRONG"
        r = validate_contract(c)
        assert r.valid is False

    def test_signal_asset_not_found(self):
        c = {**VALID_MINIMAL}
        c["signals"][0]["asset_id"] = "NONEXISTENT"
        r = validate_contract(c)
        assert r.valid is False

    def test_duplicate_signal_id(self):
        c = {**VALID_MINIMAL}
        c["signals"].append(c["signals"][0].copy())
        r = validate_contract(c)
        assert r.valid is False

    def test_signal_id_format_mismatch(self):
        c = {**VALID_MINIMAL}
        c["signals"][0]["signal_id"] = "WRONG.format"
        r = validate_contract(c)
        assert r.valid is False

    def test_opcua_binding_refs_valid_signal(self):
        c = {**VALID_MINIMAL}
        c["bindings"] = {"opcua": [{"signal_id": "PUMP01.speed", "node_id": "ns=2;s=PUMP_SPEED"}]}
        r = validate_contract(c)
        assert r.valid is True

    def test_opcua_binding_refs_missing_signal(self):
        c = {**VALID_MINIMAL}
        c["bindings"] = {"opcua": [{"signal_id": "NONEXISTENT.x", "node_id": "ns=2;s=X"}]}
        r = validate_contract(c)
        assert r.valid is False
```

### 6. Deploy & Verify

```bash
# Build backend
cd deployment && docker compose build backend

# Test locally (no VPS needed for Phase B)
cd backend && python -m pytest tests/test_contracts_validator.py -v

# Validate example contract
python -c "
import yaml, json, requests
with open('examples/contracts/vf-compressor-train.contract.yaml') as f:
    contract = yaml.safe_load(f)
resp = requests.post('http://localhost:8000/api/v1/contracts/validate', json=contract)
print(json.dumps(resp.json(), indent=2))
"
```

### 7. Validation

| Check | Expected |
|---|---|
| `pytest tests/test_contracts_validator.py` | All tests pass |
| POST validate with example contract | `valid: true`, 1 plant, 1 area, 7 assets, 26 signals |
| POST validate with broken contract | `valid: false`, specific error messages |
| Existing APIs still work | `curl /api/v1/plants` → 200 |
| Frontend still works | http://103.97.132.249 → loads normally |
| No DB writes | Check PostgreSQL: no new rows |

## Notes

- Validator is **stateless** — no database dependency
- JSON Schema file is at `schemas/plantos-integration-contract.schema.json` for reference only — Python validator handles the logic
- Phase B does NOT implement preview or apply — those are Phase C+D
