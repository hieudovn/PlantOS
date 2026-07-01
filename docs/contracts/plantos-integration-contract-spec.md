# PlantOS Integration Contract — Specification v2.0

> **Status:** Proposed | **Replaces:** v1.0 (examples/vf-plantos-contract.yaml)  
> **ADR:** ADR-0006 — Integration Contract v2 & Model Importer Architecture

---

## 1. Purpose

The PlantOS Integration Contract is the **single source of truth** for industrial asset models shared between:

| Consumer | What it reads |
|---|---|
| **Virtual Factory** (simulator) | `simulation.behaviors`, `extensions.vf_sensor_refs` |
| **PlantOS Center** (backend) | `plant`, `areas`, `assets`, `signals` → seed PostgreSQL |
| **PlantOS Edge** (OPC UA collector) | `bindings.opcua[]` → build NodeId→signal_id mapping |
| **External systems** (SCADA, MES, CSV) | Core sections + their own `bindings.*` extensions |

```
┌─────────────────────────────────────────┐
│     Integration Contract YAML           │
│     Single Source of Truth              │
├─────────────────────────────────────────┤
│  CORE (always required)                 │
│  ├─ contract / source                   │
│  ├─ plant / areas / assets / signals    │
│  └─ uns / import_recommendation         │
├─────────────────────────────────────────┤
│  EXTENSIONS (optional)                  │
│  ├─ bindings.opcua / bindings.mqtt      │
│  ├─ simulation.behaviors                │
│  └─ extensions.{}                       │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
  VF       PlantOS     Edge
         (validate/
          preview/
          apply)
```

---

## 2. Contract Structure

### 2.1 Top-Level Sections

```yaml
# =============================================================================
# PlantOS Integration Contract — v2.0
# =============================================================================
contract:                # Metadata
source:                  # Who/what generated this contract
plant:                   # Exactly ONE plant
areas:                   # Physical/functional areas
assets:                  # Asset hierarchy
signals:                 # Signal definitions (core fields only)
uns:                     # UNS namespace policy
import_recommendation:   # Hint from contract author (not binding)

bindings:                # EXTENSION — protocol-specific mappings
simulation:              # EXTENSION — simulator behavior definitions
extensions:              # EXTENSION — arbitrary key-value
```

### 2.2 Core Sections Detail

#### `contract` (required)

```yaml
contract:
  version: "2.0"                      # Semantic version of this contract
  schema_version: "2.0"               # Which JSON Schema validates this
  description: "Compressor Train Analytics Benchmark"
```

Compatibility rules:
- Major version change → may be breaking (new required fields, removed fields)
- Minor version change → backward compatible (new optional fields)
- Patch version change → documentation/validation fix only

#### `source` (required)

```yaml
source:
  system_type: virtual_factory        # virtual_factory | opcua | scada | manual | csv | engineering_tool
  system_name: "Virtual Factory v2.1"
  owner: "Avenue Engineering"
  generated_by: "PlantOS PM Designer"
  generated_at: "2026-07-01T00:00:00Z"
```

`system_type` determines which extensions are relevant:
- `virtual_factory` → expects `simulation.behaviors`
- `opcua` → expects `bindings.opcua`
- `manual`/`csv` → may have no bindings or simulation

#### `plant` (required)

```yaml
plant:
  plant_id: VF-DEMO                    # Unique ID, uppercase, hyphens only
  plant_code: VF-DEMO                  # Short code
  name: "Virtual Factory Demo Plant"   # Display name
  description: "Compressor Train Analytics Benchmark"
  timezone: "Asia/Ho_Chi_Minh"        # IANA timezone
  status: active                       # active | inactive
```

#### `areas` (required, at least 1)

```yaml
areas:
  - area_id: COMPRESSOR-AREA           # Unique ID, uppercase, hyphens
    area_code: COMPRESSOR-AREA
    name: "Compressor Area"
    plant_id: VF-DEMO                  # Must match plant.plant_id
```

#### `assets` (required, at least 1)

```yaml
assets:
  - asset_id: COMP01                   # Unique ID
    asset_code: COMP01
    name: "Compressor Train A"
    asset_type: compressor_train       # See Appendix A for valid types
    parent_asset_id: null              # null = root asset
    area_id: COMPRESSOR-AREA           # Must match an area.area_id
    criticality: critical              # critical | high | medium | low
    status: active                     # active | inactive | deprecated
```

#### `signals` (required, at least 1)

```yaml
signals:
  - signal_id: COMP01-CORE.speed       # Format: {asset_id}.{signal_name}
    asset_id: COMP01-CORE              # Must match an asset.asset_id
    signal_name: speed                 # snake_case
    display_name: "Rotational Speed"   # Human-readable
    signal_type: measurement           # measurement | status | setpoint | command
    data_type: float                   # float | bool | int | string
    engineering_unit: RPM              # See Appendix B for valid units
    scale: 1.0                         # value = raw_value * scale + offset (unit conversion)
    offset: 0.0
    status: active                     # active | inactive | deprecated
```

**Important:** Core signal definition does NOT include:
- ❌ `opcua_node_id` → in `bindings.opcua[]`
- ❌ `vf_internal_ref`, `vf_sensor_id` → in `simulation.behaviors` / `extensions`
- ❌ Behavior patterns → in `simulation.behaviors`

#### `uns` (required)

```yaml
uns:
  namespace_root: avenue
  path_template: "{namespace_root}/{plant_id}/{area_id}/{asset_id}/{signal_name}"
  normalize_case: lower
  separator: "/"
```

UNS paths are **generated** by PlantOS from the template, not manually specified.  
Example: `avenue/vf-demo/compressor-area/comp01/comp01-core.speed`

#### `import_recommendation` (required)

```yaml
import_recommendation:
  suggested_mode: apply                # Hint: validate | preview | apply
  reason: "Initial plant seed"         # Why this recommendation
  notes: "Safe to apply — new plant, no conflicts"
```

This is a **hint** from the contract author. The actual import decision (`import_policy`) is controlled by the API caller, not the contract. See Section 6 for API details.

---

### 2.3 Extension Sections (optional)

#### `bindings` — Protocol-specific mappings

```yaml
bindings:
  opcua:                               # OPC UA NodeId → signal_id mapping
    - signal_id: COMP01-CORE.speed      # Must reference a defined signal
      node_id: ns=2;s=COMP01_SPEED      # OPC UA NodeId
      scale: 1.0                        # Applied AFTER core signal.scale
      offset: 0.0
  # Future:
  # mqtt:
  #   - signal_id: ...
  #     topic: "avenue/vf-demo/comp01/speed"
  # modbus:
  #   - signal_id: ...
  #     register: 40001
  #     type: holding
```

**Validation rules:**
- Each `signal_id` in `bindings.opcua[]` must reference an existing signal (Rule V16)
- Duplicate `node_id` values are rejected (Rule V17)
- Warning if a signal has no OPC UA binding when `source.system_type` is `virtual_factory` or `opcua` (Rule V18)

#### `simulation` — Virtual Factory behavior definitions

```yaml
simulation:
  behaviors:
    COMP01.speed_rpm:                  # vf_internal_ref (matches VF variable)
      signal_id: COMP01-CORE.speed      # Links to PlantOS signal
      pattern: sine                    # sine | random_walk | ramp | step | degradation
      mid: 3500
      amplitude: 200
      noise: 10
      frequency_hz: 0.01
      unit: RPM
```

**This section is ONLY consumed by Virtual Factory simulator. PlantOS Center and Edge ignore it.**

#### `extensions` — Custom metadata

```yaml
extensions:
  vf_sensor_refs:                      # ISA-5.1 sensor tags (VF-specific)
    COMP01-CORE.speed: ST101
    COMP01-CORE.suction_pressure: PT101
  visualization:
    diagram_bindings: "pid-process.binding.yaml"
  edge:
    poll_interval_ms: 30000            # Edge-specific overrides
```

---

## 3. Naming Conventions

| Element | Convention | Valid Example | Invalid Example |
|---|---|---|---|
| `plant_id` | UPPERCASE, hyphens | `VF-DEMO`, `STEEL-MILL` | `vf_demo`, `steelMill` |
| `area_id` | UPPERCASE, hyphens | `COMPRESSOR-AREA` | `compressor_area` |
| `asset_id` | UPPERCASE, hyphens | `COMP01`, `COMP01-MOTOR` | `comp01`, `comp01.motor` |
| `signal_id` | `{asset_id}.{signal_name}` | `COMP01-CORE.speed` | `speed`, `COMP01.speed` |
| `signal_name` | snake_case | `suction_pressure` | `SuctionPressure`, `suction-pressure` |
| `opcua_node_id` | `ns=2;s={UPPER_SNAKE}` | `ns=2;s=COMP01_SPEED` | `COMP01_SPEED` |

---

## 4. UNS Path Generation

### 4.1 Algorithm

```python
def generate_uns_path(
    signal: dict,
    area: dict,
    asset: dict,
    plant: dict,
    uns_policy: dict
) -> str:
    """Generate UNS path from contract entities."""
    template = uns_policy["path_template"]
    separator = uns_policy["separator"]
    
    path = template.format(
        namespace_root=uns_policy["namespace_root"],
        plant_id=plant["plant_id"],
        area_id=area["area_id"],
        asset_id=asset["asset_id"],
        signal_name=signal["signal_name"],
    )
    
    if uns_policy.get("normalize_case") == "lower":
        path = path.lower()
    
    return path.replace("/", separator)
```

### 4.2 Example

```
Input:  signal=COMP01-CORE.speed, area=COMPRESSOR-AREA, asset=COMP01
Output: avenue/vf-demo/compressor-area/comp01/comp01-core.speed
```

The UNS path is **generated by the validator/preview/apply pipeline** and included in responses. It is not a field in the contract itself.

---

## 5. Import Policy (API-level, not in contract)

The contract provides `import_recommendation` as a hint. The actual import behavior is controlled by the API caller:

```json
// POST /api/v1/contracts/apply
{
  "contract": { ... },
  "import_policy": {
    "mode": "apply",
    "on_conflict": "skip",
    "allow_update_existing": true,
    "allow_delete_missing": false,
    "orphaned_action": "report"
  }
}
```

| Policy Field | Values | Default | Description |
|---|---|---|---|
| `mode` | `validate_only`, `preview`, `apply` | `validate_only` | What the API should do |
| `on_conflict` | `fail`, `skip`, `update` | `fail` | Behavior when entity already exists |
| `allow_update_existing` | `true`, `false` | `false` | Allow modifying existing entities |
| `allow_delete_missing` | `true`, `false` | `false` | Allow deleting entities not in contract |
| `orphaned_action` | `report`, `deactivate`, `delete` | `report` | How to handle DB entities not in contract |

**Safety defaults:** `validate_only` + `fail` + no deletes. Explicit opt-in required for any destructive action.

---

## 6. API Endpoints

### 6.1 `POST /api/v1/contracts/validate`

Validate contract structure and cross-references. **Does not access database.**

Response includes generated UNS paths for each signal.

### 6.2 `POST /api/v1/contracts/preview` (Phase C)

Compare contract against existing PostgreSQL registry. Returns diff of creates/updates/conflicts/orphans.

### 6.3 `POST /api/v1/contracts/apply` (Phase D)

Execute import. Requires `import_policy.mode: apply`. Writes through existing Asset/Signal service layer.

---

## 7. Validation Rules

| Rule | Category | Check | Severity |
|---|---|---|---|
| V1 | Structure | `contract.version` valid semver | error |
| V2 | Structure | `plant.plant_id` present, valid format | error |
| V3 | Reference | `area.plant_id` == `plant.plant_id` | error |
| V4 | Reference | `asset.area_id` exists in areas | error |
| V5 | Reference | `asset.parent_asset_id` exists or is null | error |
| V6 | Reference | `signal.asset_id` exists in assets | error |
| V7 | Uniqueness | No duplicate `area_id` | error |
| V8 | Uniqueness | No duplicate `asset_id` | error |
| V9 | Uniqueness | No duplicate `signal_id` | error |
| V10 | Format | `signal_id` matches `{asset_id}.{signal_name}` | error |
| V11 | Format | `opcua_node_id` matches `ns=2;s=NAME` (if present) | error |
| V12 | Domain | `engineering_unit` is recognized | warning |
| V13 | Domain | `asset_type` is recognized | warning |
| V14 | Domain | `status` is valid enum value | error |
| V15 | Domain | `criticality` is valid enum value | error |
| V16 | Binding | `bindings.opcua[].signal_id` references a signal | error |
| V17 | Binding | No duplicate `bindings.opcua[].node_id` | error |
| V18 | Binding | Warning if signal lacks OPC UA binding (when system_type expects it) | warning |

---

## 8. Orphaned Entity Handling

When `import_policy.mode: apply` runs against an existing plant:

| Scenario | Behavior |
|---|---|
| Signal in DB, not in contract | **Orphaned.** Action per `orphaned_action`: `report` (list in response), `deactivate` (set status=deprecated), or `delete` (hard delete — requires explicit flag) |
| Asset in DB, not in contract | Same as signal — per `orphaned_action` |
| Area in DB, not in contract | Report only (areas with assets cannot be deactivated) |

**Default: `report`** — no changes to DB, orphaned entities listed in response for manual review.

---

## Appendix A: Valid Asset Types

```
compressor_train, compressor, pump, motor, turbine, fan, gearbox,
tank, vessel, heat_exchanger, cooling_tower, boiler, furnace, reactor, column,
bearing_assembly, seal_system, lubrication_system, cooling_system,
transformer, switchgear, breaker, feeder, motor_control_center, vfd,
valve, control_valve, safety_valve, pipeline, filter, strainer,
sensor_array, analyzer, flow_meter, transmitter,
production_line, work_cell, conveyor, robot, cnc_machine
```

## Appendix B: Valid Engineering Units

```
# Pressure:    kPa, MPa, bar, psi, Pa, mbar
# Temperature: degC, degF, K
# Flow:        m3/h, Nm3/h, L/min, kg/h, t/h, m3/s
# Speed:       RPM, Hz, m/s, rad/s
# Electrical:  A, V, kW, kVA, kWh, PF, Hz, ohm
# Vibration:   mm/s, um, mil, g
# Level:       m, %, mm, cm
# Mass:        kg, t, g
# Dimension:   mm, um, cm, m
# Force:       N, kN
# Torque:      Nm, kNm
# Energy:      kJ, MJ, kWh, MWh
# Power:       W, kW, MW
# Density:     kg/m3, g/cm3
# Viscosity:   cSt, cP
```

## Appendix C: Sensor Tag Convention (ISA-5.1)

| Prefix | Meaning | Example |
|---|---|---|
| PT | Pressure Transmitter | PT101 |
| TT | Temperature Transmitter | TT101 |
| FT | Flow Transmitter | FT101 |
| VT | Vibration Transmitter | VT101 |
| CT | Current Transmitter | CT101 |
| ST | Speed Transmitter | ST101 |
| LT | Level Transmitter | LT101 |
| PDT | Differential Pressure Transmitter | PDT101 |
| AT | Analyzer Transmitter | AT101 |
| ZT | Position Transmitter | ZT101 |
