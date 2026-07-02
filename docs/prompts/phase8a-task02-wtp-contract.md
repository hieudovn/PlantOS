# Task 8A-02 — WTP Contract File

## Context

You are the Coder-Executioner for PlantOS Phase 8A.

PlantOS is building WTP-DEMO-01, the first Water Treatment Plant Reference Model. The design is complete at `docs/reference-models/wtp-demo-01-design.md`. Your job is to create the Integration Contract v2 YAML file that defines the plant model.

## Required Reading

Before coding, read:

```text
docs/reference-models/wtp-demo-01-design.md          ← Design document (just created)
docs/contracts/plantos-integration-contract-spec.md   ← Contract v2 spec
examples/contracts/vf-compressor-train.contract.yaml  ← Canonical v2 example (REFERENCE)
schemas/plantos-integration-contract.schema.json      ← JSON Schema
backend/app/modules/contracts/schemas.py              ← Pydantic models (ContractV2, etc.)
backend/app/modules/contracts/validator.py            ← Custom validation rules
```

## Key Technical Constraints (CRITICAL)

The contract goes through **two validation layers**:

### Layer 1: Pydantic (`schemas.py`)

```python
class ContractMeta(BaseModel):
    version: str
    schema_version: str = "2.0"     # REQUIRED — must be present
    description: str

class PlantDef(BaseModel):
    timezone: str = "UTC"           # MUST be present (even with default)

class SignalDef(BaseModel):
    signal_type: str = "measurement"  # NOT restricted to enum by Pydantic
    data_type: str = "float"

class Simulation(BaseModel):
    behaviors: dict[str, SimulationBehavior]  # DICT, NOT list!

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
    # NOTE: depends_on and transform are NOT in this model
```

### Layer 2: Custom Validator (`validator.py`)

```python
VALID_SIGNAL_TYPES = {"measurement", "status", "setpoint", "command"}
# "calculated" is NOT valid → will ERROR!

VALID_ASSET_TYPES = {
    "compressor_train", "compressor", "pump", "motor", "turbine", "fan", "gearbox",
    "tank", "vessel", "heat_exchanger", "cooling_tower", "boiler", "furnace",
    "reactor", "column", "bearing_assembly", "seal_system", "lubrication_system",
    "cooling_system", "transformer", "switchgear", "breaker", "feeder",
    "motor_control_center", "vfd", "valve", "control_valve", "safety_valve",
    "pipeline", "filter", "strainer", "sensor_array", "analyzer", "flow_meter",
    "transmitter", "production_line", "work_cell", "conveyor", "robot", "cnc_machine",
}
# Unrecognized types → WARNING only (does NOT block)

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
# Unrecognized units → WARNING only
```

## Source Contract Draft

Start from the draft contract attached by the PM. Key stats: 9 areas, 47 assets, ~97 signals, 8 scenarios.

## Implementation Checklist

### Step 1: Create the Contract File

```text
examples/contracts/wtp-demo-01.contract.yaml
```

### Step 2: CRITICAL FIXES — Apply these changes to the draft

#### C1: Add `schema_version` to contract section
```yaml
contract:
  version: "2.0"
  schema_version: "2.0"          # ← ADD THIS
  description: "Water Treatment Plant Reference Model for PlantOS and Virtual Factory"
```

#### C2: Add `timezone` to plant section
```yaml
plant:
  plant_id: WTP-DEMO-01
  plant_code: WTP01
  name: Water Treatment Plant Demo 01
  description: >
    Reference water treatment plant model with process monitoring, equipment health,
    water quality chain, energy and chemical consumption monitoring, cost KPIs,
    and quality traceability.
  timezone: "Asia/Ho_Chi_Minh"   # ← ADD THIS
  status: active
```

#### C3: Change ALL `signal_type: calculated` → `signal_type: measurement`

Search for `signal_type: calculated` across all signals (approximately 18 occurrences) and change them to `signal_type: measurement`. The signals affected include:

- `raw_algae_index`
- `floc_size_index`
- `clarifier_efficiency_index`
- `filter_runtime_hours` (actually this is `runtime_hours`)
- `particle_count_proxy`
- `filter_run_quality_index`
- `ct_value_proxy`
- `quality_index`
- `outlet_compliance_status`
- `total_energy_today`
- `specific_energy_consumption`
- `energy_cost_per_m3`
- `peak_demand`
- `coagulant_specific_consumption`
- `chlorine_specific_consumption`
- `chemical_cost_per_m3`
- `dosing_efficiency_index`
- `outlet_quality_risk_score`
- `raw_water_impact_score`
- `chemical_dosing_abnormality_score`
- `energy_abnormality_score`
- `probable_root_cause_code`
- `water_production_today`
- `treatment_yield`
- `outlet_quality_index`
- `compliance_rate_today`
- `cost_per_m3`

#### C4: Convert `simulation.behaviors` from LIST to DICT

The Pydantic model `Simulation` expects:
```python
behaviors: dict[str, SimulationBehavior]
```

Change from:
```yaml
simulation:
  behaviors:
    - { signal_id: RWP-101.flow_rate, pattern: sine, mid: 450.0, amplitude: 35.0, noise: 5.0 }
```

To:
```yaml
simulation:
  behaviors:
    "RWP-101.flow_rate":
      pattern: sine
      mid: 450.0
      amplitude: 35.0
      noise: 5.0
```

The key of each entry is the `signal_id`. Apply this to ALL behavior entries.

#### C5: Remove unsupported SimulationBehavior fields

The Pydantic model does NOT support these fields:
- `depends_on`
- `transform`
- `drift_rate`
- `spike_probability`
- `spike_magnitude`
- `baseline` (not in model — use `mid` instead)

For any behavior using these fields, simplify to supported fields:
- `depends_on` + `transform` → change pattern to `random_walk` with appropriate bounds
- `drift_rate` → change pattern to `random_walk` with `bounds_min`/`bounds_max`
- `baseline` → use `mid` instead

The VF simulator will add its own advanced config separately — the contract only needs the PlantOS-compatible subset.

#### C6: Move `monitoring` section under `extensions`

Change:
```yaml
monitoring:
  dashboards:
    ...
  alarm_recommendations:
    ...
```

To:
```yaml
extensions:
  monitoring:
    dashboards:
      ...
    alarm_recommendations:
      ...
```

#### C7: Verify ALL asset_type values are recognized

Check every asset in the contract against `VALID_ASSET_TYPES`. The draft uses these types — verify they're all in the set:

- `vessel` ✅
- `filter` ✅
- `pump` ✅
- `motor` ✅
- `pipeline` ✅
- `sensor_array` ✅
- `tank` ✅
- `gearbox` ✅ (listed as `gearbox` in the set)
- `reactor` ✅
- `transformer` ✅
- `motor_control_center` ✅
- `analyzer` ✅

#### C8: Verify `data_type` values

The draft uses: `float`, `bool`, `int`. All are valid per `VALID_DATA_TYPES = {"float", "bool", "int", "string"}`.

#### C9: Verify signal_id format

Every `signal_id` must follow pattern: `{ASSET_ID}.{signal_name}` (V10 rule).
The asset part must match `^[A-Z][A-Z0-9-]*$` and the signal part `^[a-z][a-z0-9_]*$`.

### Step 3: Validate the Contract

After creating the file, validate it programmatically:

```python
# Run this to validate against Pydantic + custom rules
import yaml
import json
import sys
sys.path.insert(0, 'backend')

from app.modules.contracts.schemas import ContractV2
from app.modules.contracts.validator import validate_contract

with open('examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)

# Layer 1: Pydantic
try:
    contract = ContractV2(**data)
    print("✅ Pydantic validation PASSED")
except Exception as e:
    print(f"❌ Pydantic validation FAILED: {e}")
    sys.exit(1)

# Layer 2: Custom rules
result = validate_contract(data)
print(f"\nErrors: {len(result.errors)}")
for e in result.errors:
    print(f"  ❌ {e['path']}: {e['message']}")

print(f"\nWarnings: {len(result.warnings)}")
for w in result.warnings:
    print(f"  ⚠️  {w['path']}: {w['message']}")

if result.valid:
    print("\n✅ Custom validation PASSED")
else:
    print("\n❌ Custom validation FAILED — fix errors above")
    sys.exit(1)
```

### Step 4: Validate Against JSON Schema (optional)

```bash
pip install jsonschema pyyaml
python -c "
import yaml, json
from jsonschema import validate

with open('examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)
with open('schemas/plantos-integration-contract.schema.json') as f:
    schema = json.load(f)
validate(data, schema)
print('✅ JSON Schema validation PASSED')
"
```

## Deliverables

1. `examples/contracts/wtp-demo-01.contract.yaml` — Validated contract file
2. Validation output showing 0 errors

## Expected Signal Count (Verify)

| Category | Expected Count |
|----------|---------------|
| INTAKE-AREA signals | ~20 |
| CHEMICAL-DOSING-AREA signals | ~9 |
| CLARIFICATION-AREA signals | ~7 |
| FILTRATION-AREA signals | ~11 |
| DISINFECTION-CLEARWATER-AREA signals | ~9 |
| DISTRIBUTION-AREA signals | ~14 |
| ELECTRICAL-UTILITY-AREA signals | ~9 |
| QUALITY-LAB-AREA signals | ~7 |
| PLANT-KPI-AREA signals | ~5 |
| **TOTAL** | **~91-97** |

Count and report actual total after creation.

## Reference: VF Compressor Train Contract Structure

The `vf-compressor-train.contract.yaml` is your template for structure. Key patterns to follow:

```yaml
contract:
  version: "2.0"
  schema_version: "2.0"
  description: "..."

source:
  system_type: virtual_factory
  system_name: Virtual Factory
  owner: Avenue
  generated_by: Solution Architect
  generated_at: "2026-07-01T00:00:00Z"

plant:
  plant_id: WTP-DEMO-01
  plant_code: WTP01
  name: "..."
  description: "..."
  timezone: "Asia/Ho_Chi_Minh"
  status: active

uns:
  namespace_root: avenue
  path_template: "{namespace_root}/{plant_id}/{area_id}/{asset_id}/{signal_name}"
  normalize_case: lower
  separator: "/"

import_recommendation:
  suggested_mode: validate_only
  reason: "First import — validate before applying"
  notes: "New plant, expected all creates"

areas:
  - area_id: INTAKE-AREA
    area_code: INTAKE
    name: "Raw Water Intake Area"
    plant_id: WTP-DEMO-01
  # ... 8 more

assets:
  - asset_id: INTAKE-STRUCTURE-101
    asset_code: INTAKE101
    name: "Intake Structure 101"
    asset_type: vessel
    parent_asset_id: null
    area_id: INTAKE-AREA
    criticality: high
    status: active
  # ... 46 more

signals:
  - signal_id: INTAKE-STRUCTURE-101.raw_water_level
    asset_id: INTAKE-STRUCTURE-101
    signal_name: raw_water_level
    display_name: "Raw Water Level"
    signal_type: measurement
    data_type: float
    engineering_unit: "m"
    status: active
  # ... 96 more

bindings:
  opcua:
    - signal_id: RWP-101.flow_rate
      node_id: "ns=2;s=RWP101_FLOW_RATE"
      scale: 1.0
      offset: 0.0
    # ... minimal bindings

simulation:
  default_scenario: normal_operation
  behaviors:
    "RWP-101.flow_rate":
      pattern: sine
      mid: 450.0
      amplitude: 35.0
      noise: 5.0
    # ... DICT format, NOT list

extensions:
  monitoring:
    dashboards:
      - dashboard_id: plant_overview
        name: "Plant Overview"
        ...
    alarm_recommendations:
      - rule_id: WTP_FILTER_101_HIGH_DP
        ...
```

## Important Notes

1. The draft uses `kind:` in the contract section — that field does NOT exist in the Pydantic model and will be silently ignored. Remove it or keep it (harmless).
2. The `import_recommendation` section uses `default_mode`, `default_on_conflict`, `allow_update_existing`, `allow_delete_missing`, `orphaned_action` in the draft. The Pydantic `ImportRecommendation` model only has: `suggested_mode`, `reason`, `notes`. Remove the extra fields.
3. Some signals have `signal_type: calculated` — this is the MOST CRITICAL fix. The validator V14 check validates signal_type against `VALID_SIGNAL_TYPES` which does NOT include "calculated".
4. For the simulation behaviors, if a signal needs complex behavior (like `dependent` on another signal), simplify it to `random_walk` with appropriate bounds. The VF simulator will handle complex logic separately.
5. Keep OPC UA bindings minimal (just the 9 already in the draft). The V18 rule warns about unbound signals but does NOT block validation.

## Test Verification

After creating the file, run:
```bash
cd backend
python -c "
import yaml
from app.modules.contracts.schemas import ContractV2
from app.modules.contracts.validator import validate_contract

with open('../examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)

contract = ContractV2(**data)
result = validate_contract(data)

print(f'Areas: {len(data[\"areas\"])}')
print(f'Assets: {len(data[\"assets\"])}')
print(f'Signals: {len(data[\"signals\"])}')
print(f'Errors: {len(result.errors)}')
print(f'Warnings: {len(result.warnings)}')
assert result.valid, 'VALIDATION FAILED'
print('✅ ALL CHECKS PASSED')
"
```
