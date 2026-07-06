# PlantOS Integration Data Contract — Full Specification

> **Purpose:** This document defines the single source of truth for asset models, signal definitions, and OPC UA bindings between Virtual Factory (simulator) and PlantOS (operational platform).
>
> **Use this to build a new production simulation model.** Give this entire document to ChatGPT/Claude and describe your target production process.

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│           Integration Data Contract (YAML)                │
│           Single Source of Truth                          │
│           examples/vf-plantos-contract.yaml               │
└──────────────────────┬───────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ Virtual      │ │ PlantOS      │ │ PlantOS          │
│ Factory      │ │ Center       │ │ Edge Agent       │
│ (Simulator)  │ │ (Backend)    │ │ (OPC UA Client)  │
├──────────────┤ ├──────────────┤ ├──────────────────┤
│ Reads:       │ │ Reads:       │ │ Reads:           │
│ plant_id     │ │ plant, areas │ │ opcua_node_id    │
│ signals[].   │ │ assets,      │ │ signal_id        │
│   vf_sensor_ │ │ signals      │ │ scale            │
│   id,        │ │              │ │                  │
│   vf_internal│ │ Generates:   │ │ Syncs from:      │
│   _ref       │ │ PG metadata  │ │ Center manifest  │
│              │ │ Seed script  │ │ API              │
│ Generates:   │ │              │ │                  │
│ OPC UA       │ │              │ │ Publishes:       │
│ server :4840 │ │              │ │ Measurements →   │
│              │ │              │ │ TDengine         │
└──────────────┘ └──────────────┘ └──────────────────┘
```

---

## 2. Contract Format Specification

### 2.1 Top-Level Structure

```yaml
contract:
  version: "1.0"            # Semantic version of the contract
  description: "..."         # Human-readable description
  vf_plant_config: "..."    # Path to VF simulator config file (for reference)

plant:                       # Exactly ONE plant
  plant_id: ""               # Unique ID, uppercase, hyphens allowed
  plant_code: ""             # Short code (same as plant_id for now)
  name: ""                   # Display name
  description: ""            # Longer description

areas:                       # List of physical/functional areas
  - area_id: ""              # Unique ID
    area_code: ""            # Short code
    name: ""                 # Display name
    plant_id: ""             # Must match plant.plant_id

assets:                      # Asset tree (parent-child hierarchy)
  - asset_id: ""             # Unique ID
    asset_code: ""           # Short code
    name: ""                 # Display name
    asset_type: ""           # See Asset Types below
    asset_role: ""           # See Asset Roles below (v2.0+)
    parent_asset_id: null    # null = root, or parent asset_id
    area_id: ""              # Must match an area.area_id
    criticality: ""          # critical | high | medium | low
    status: active           # active | inactive | maintenance | decommissioned

signals:                     # All measurement signals
  - signal_id: ""            # Format: {asset_id}.{signal_name}
    asset_id: ""             # Must match an asset.asset_id
    signal_name: ""          # Short snake_case name
    display_name: ""         # Human-readable name
    signal_category: measurement  # measurement | status | alarm | counter | calculated | command (v2.0+)
    data_type: float         # float | bool | int
    engineering_unit: ""     # SI unit: kPa, degC, RPM, A, kW, m3/h, mm/s, etc.
    opcua_node_id: ""        # OPC UA NodeId: ns=2;s=NODE_NAME
    scale: 1.0               # Conversion factor: raw_value * scale + offset
    offset: 0.0              # (optional) defaults to 0
    vf_internal_ref: ""      # VF simulator internal variable reference
    vf_sensor_id: ""         # Sensor tag for P&ID reference
    external_refs: {}         # (optional) Opaque dict for external system metadata
```

### 2.2 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| `plant_id` | UPPERCASE, hyphens | `VF-DEMO`, `STEEL-PLANT-01` |
| `area_id` | UPPERCASE, hyphens | `COMPRESSOR-AREA`, `FURNACE-ZONE` |
| `asset_id` | UPPERCASE, hyphens, hierarchical | `COMP01`, `COMP01-MOTOR`, `FURN01-ZONE1` |
| `signal_id` | `{asset_id}.{signal_name}` | `COMP01-CORE.speed`, `FURN01.temp_zone1` |
| `signal_name` | snake_case | `suction_pressure`, `flow_rate`, `bearing_temp` |
| `opcua_node_id` | `ns=2;s={UPPER_SNAKE}` | `ns=2;s=COMP01_SPEED` |
| `vf_internal_ref` | dot notation matching VF internal | `COMP01.speed_rpm` |

### 2.3 Asset Types

Available asset types for classification:

```yaml
# Rotating equipment
compressor_train, compressor, pump, motor, turbine, fan, gearbox

# Static equipment
tank, vessel, heat_exchanger, cooling_tower, boiler, furnace, reactor, column

# Mechanical
bearing_assembly, seal_system, lubrication_system, cooling_system

# Electrical
transformer, switchgear, breaker, feeder, motor_control_center, vfd

# Piping & Valves
valve, control_valve, safety_valve, pipeline, filter, strainer

# Instrumentation
sensor_array, analyzer, flow_meter, transmitter

# Production
production_line, work_cell, conveyor, robot, cnc_machine
```

### 2.4 Asset Roles (v2.0+)

Each asset must declare an `asset_role` to indicate its semantic position in the hierarchy:

```yaml
functional_location:  # Grouping/organizational node (Line, Cell, System, Zone)
                      # Does not generate telemetry itself; groups equipment beneath it

equipment:            # Physical asset with telemetry/signals
                      # Has at least one associated signal

subsystem:            # Maintainable component within equipment
                      # May have dedicated diagnostic signals

component:            # Small replaceable part (use only when lifecycle tracking needed)

logical_group:        # Non-physical grouping for display/analytics (e.g., "Critical Path Assets")
```

**Backward compatibility:** Contracts without `asset_role` will auto-derive from `asset_type`:
- `production_line`, `work_cell`, `equipment_group` → `functional_location`
- `bearing_assembly`, `seal_system`, `lubrication_system`, `cooling_system` → `subsystem`
- All others → `equipment`

### 2.5 Signal Categories (v2.0+)

Each signal declares a `signal_category` (replaces the single-value `signal_type: measurement`):

```yaml
measurement:  # Continuous or sampled value (temperature, pressure, speed, flow)
status:       # Discrete state or enumeration (running/stopped, open/closed)
alarm:        # Binary alarm state (normal/alarmed)
counter:      # Cumulative count (cycle count, energy totalizer)
calculated:   # Derived/computed value (efficiency, KPI, index)
command:      # Control command (future — requires control authorization)
```

**Backward compatibility:** Old contracts with `signal_type: measurement` will auto-map to `signal_category: measurement`.

### 2.6 Engineering Units

Common units supported by PlantOS:

```yaml
# Pressure:    kPa, MPa, bar, psi, Pa
# Temperature: degC, degF, K
# Flow:        m3/h, Nm3/h, L/min, kg/h, t/h
# Speed:       RPM, Hz, m/s
# Electrical:  A, V, kW, kVA, kWh, PF, Hz
# Vibration:   mm/s, um, mil, g
# Level:       m, %, mm
# Mass:        kg, t
# Dimension:   mm, um
```

---

## 3. Complete Example: Compressor Train (current model)

### 3.1 Asset Hierarchy

```
VF-DEMO (Virtual Factory Demo Plant)
└── COMPRESSOR-AREA
    └── COMP01 (Compressor Train A) [critical]
        ├── COMP01-MOTOR (Drive Motor) [critical] — 7 signals
        ├── COMP01-CORE (Compressor Core) [critical] — 7 signals
        ├── COMP01-BEARINGS (Bearings Assembly) [high] — 6 signals
        ├── COMP01-LUBE (Lube Oil System) [high] — 3 signals
        ├── COMP01-COOLING (Cooling Water System) [medium] — 2 signals
        └── COMP01-SEAL (Seal Gas System) [high] — 1 signal
```

### 3.2 Signal Breakdown (26 total)

| # | Signal ID | Asset | Display Name | Unit | OPC UA Node |
|---|---|---|---|---|---|
| 1 | COMP01-CORE.suction_pressure | COMP01-CORE | Suction Pressure | kPa | COMP01_SUCTION_PRESSURE |
| 2 | COMP01-CORE.discharge_pressure | COMP01-CORE | Discharge Pressure | kPa | COMP01_DISCHARGE_PRESSURE |
| 3 | COMP01-CORE.flow_rate | COMP01-CORE | Flow Rate | m3/h | COMP01_FLOW |
| 4 | COMP01-CORE.suction_temp | COMP01-CORE | Suction Temperature | degC | COMP01_SUCTION_TEMP |
| 5 | COMP01-CORE.discharge_temp | COMP01-CORE | Discharge Temperature | degC | COMP01_DISCHARGE_TEMP |
| 6 | COMP01-CORE.speed | COMP01-CORE | Rotational Speed | RPM | COMP01_SPEED |
| 7 | COMP01-CORE.power | COMP01-CORE | Power Consumption | kW | COMP01_POWER |
| 8 | COMP01-MOTOR.current | COMP01-MOTOR | Motor Current | A | COMP01_MOTOR_CURRENT |
| 9 | COMP01-MOTOR.power | COMP01-MOTOR | Motor Power | kW | COMP01_MOTOR_POWER |
| 10 | COMP01-MOTOR.winding_temp | COMP01-MOTOR | Winding Temperature | degC | COMP01_MOTOR_WINDING_TEMP |
| 11 | COMP01-MOTOR.bearing_de_temp | COMP01-MOTOR | DE Bearing Temp | degC | COMP01_MOTOR_BRG_DE_TEMP |
| 12 | COMP01-MOTOR.bearing_nde_temp | COMP01-MOTOR | NDE Bearing Temp | degC | COMP01_MOTOR_BRG_NDE_TEMP |
| 13 | COMP01-MOTOR.vibration_de | COMP01-MOTOR | DE Vibration | mm/s | COMP01_MOTOR_VIB_DE |
| 14 | COMP01-MOTOR.vibration_nde | COMP01-MOTOR | NDE Vibration | mm/s | COMP01_MOTOR_VIB_NDE |
| 15 | COMP01-BEARINGS.de_temp | COMP01-BEARINGS | DE Bearing Temp | degC | COMP01_BRG_DE_TEMP |
| 16 | COMP01-BEARINGS.nde_temp | COMP01-BEARINGS | NDE Bearing Temp | degC | COMP01_BRG_NDE_TEMP |
| 17 | COMP01-BEARINGS.thrust_temp | COMP01-BEARINGS | Thrust Bearing Temp | degC | COMP01_BRG_THRUST_TEMP |
| 18 | COMP01-BEARINGS.vibration_de | COMP01-BEARINGS | DE Vibration | mm/s | COMP01_VIB_DE |
| 19 | COMP01-BEARINGS.vibration_nde | COMP01-BEARINGS | NDE Vibration | mm/s | COMP01_VIB_NDE |
| 20 | COMP01-BEARINGS.vibration_axial | COMP01-BEARINGS | Axial Vibration | mm/s | COMP01_VIB_AXIAL |
| 21 | COMP01-LUBE.pressure | COMP01-LUBE | Lube Oil Pressure | kPa | COMP01_LO_PRESS |
| 22 | COMP01-LUBE.temperature | COMP01-LUBE | Lube Oil Temperature | degC | COMP01_LO_TEMP |
| 23 | COMP01-LUBE.filter_dp | COMP01-LUBE | Filter Delta-P | kPa | COMP01_LO_FILTER_DP |
| 24 | COMP01-COOLING.supply_temp | COMP01-COOLING | CW Supply Temp | degC | COMP01_CW_SUPPLY_TEMP |
| 25 | COMP01-COOLING.return_temp | COMP01-COOLING | CW Return Temp | degC | COMP01_CW_RETURN_TEMP |
| 26 | COMP01-SEAL.flow_rate | COMP01-SEAL | Seal Gas Flow | Nm3/h | COMP01_SEAL_FLOW |

### 3.3 Signal Behavior Specifications

For the Virtual Factory simulator, each signal needs a **behavior pattern**:

| Signal Pattern | Description | Parameters |
|---|---|---|
| `sine` | Oscillating around a midpoint | `mid`, `amplitude`, `frequency`, `noise` |
| `random_walk` | Drifting from current value | `step_size`, `bounds_min`, `bounds_max` |
| `ramp_up` | Linear increase to target | `target`, `rate`, `hold_time` |
| `step` | Abrupt change between states | `values[]`, `hold_time_per_step` |
| `degradation` | Slow drift with occasional spikes | `drift_rate`, `spike_probability`, `spike_magnitude` |

**Example signal behavior (for VF simulator config):**

```yaml
# Steady operation with noise
COMP01.suction_pressure_kpa:
  pattern: sine
  mid: 120.0
  amplitude: 5.0
  noise: 0.5

# Degradation simulation (for predictive maintenance)
COMP01.vibration_de_mm_s:
  pattern: degradation
  baseline: 2.0
  drift_rate: 0.001       # mm/s per hour — slow wear
  spike_probability: 0.05
  spike_magnitude: 0.5

# Speed with operating modes
COMP01.speed_rpm:
  pattern: step
  states: [0, 800, 3500, 3500, 800, 0]   # startup, idle, full, full, idle, stop
  hold_time_per_step: [10, 30, 300, 300, 30, 10]  # seconds
```

---

## 4. How to Build a New Production Model

### Step 1: Define the process

Describe your production process in natural language. Example:

> "A steel rolling mill with reheat furnace, roughing mill, finishing mill, and coiler. The furnace has 3 temperature zones. Each mill stand has motor current, speed, and bearing vibration. The coiler has tension and speed control."

### Step 2: Model the asset hierarchy

Draw the asset tree with parent-child relationships:

```
STEEL-MILL-01
├── FURNACE-AREA
│   └── FURN01 (Reheat Furnace)
│       ├── FURN01-ZONE1 (Preheat Zone)
│       ├── FURN01-ZONE2 (Heating Zone)
│       └── FURN01-ZONE3 (Soaking Zone)
├── MILL-AREA
│   ├── RM01 (Roughing Mill Stand)
│   │   ├── RM01-MOTOR (Main Drive)
│   │   └── RM01-BEARINGS
│   ├── FM01 (Finishing Mill Stand 1)
│   │   ├── FM01-MOTOR
│   │   └── FM01-BEARINGS
│   └── FM02 (Finishing Mill Stand 2)
│       ├── FM02-MOTOR
│       └── FM02-BEARINGS
└── COILER-AREA
    └── COIL01 (Down Coiler)
        ├── COIL01-MOTOR
        └── COIL01-TENSION
```

### Step 3: Define signals per asset

For each asset, list what you want to measure. Follow the pattern:

```
{asset_id}.{signal_name}  →  {display_name}  ({unit})  →  OPC UA: ns=2;s={NODE_NAME}
```

### Step 4: Write the YAML contract

Use the template in Section 2. Fill in all fields. Save as `examples/{your-plant}-contract.yaml`.

### Step 5: Define OPC UA behaviors

For each signal, define the simulation behavior pattern (Section 3.3) for the VF simulator to implement.

### Step 6: Register in PlantOS

```bash
# 1. Place contract in examples/
# 2. Seed PlantOS Center:
curl -X POST http://localhost:8000/api/v1/seed/vf-demo -H "Authorization: Bearer $TOKEN"

# 3. Update Edge config with OPC UA tags (derived from contract signals[].opcua_node_id)
# 4. Restart Edge Agent:
sudo systemctl restart plantos-edge
```

---

## 5. Full Contract Template (copy-paste ready)

```yaml
# =============================================================================
# Integration Data Contract: {YOUR_PLANT_NAME} ↔ PlantOS
# =============================================================================
contract:
  version: "1.0"
  description: "{One-line description of the production process}"
  vf_plant_config: "configs/plants/{your_plant_config}.yaml"

# ---------------------------------------------------------------------------
# Plant & Areas
# ---------------------------------------------------------------------------
plant:
  plant_id: {PLANT_ID}
  plant_code: {PLANT_CODE}
  name: {Plant Display Name}
  description: {Longer description}

areas:
  - area_id: {AREA_ID_1}
    area_code: {AREA_CODE_1}
    name: {Area Name}
    plant_id: {PLANT_ID}

# ---------------------------------------------------------------------------
# Asset Tree (parent_asset_id: null = root)
# ---------------------------------------------------------------------------
assets:
  - asset_id: {ASSET_ID_ROOT}
    asset_code: {ASSET_CODE_ROOT}
    name: {Asset Name}
    asset_type: {type}
    parent_asset_id: null
    area_id: {AREA_ID_1}
    criticality: critical

  - asset_id: {ASSET_ID_CHILD}
    asset_code: {ASSET_CODE_CHILD}
    name: {Asset Name}
    asset_type: {type}
    parent_asset_id: {ASSET_ID_ROOT}
    area_id: {AREA_ID_1}
    criticality: high

# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------
signals:
  - signal_id: {ASSET_ID}.{signal_name}
    asset_id: {ASSET_ID}
    signal_name: {signal_name}
    display_name: {Display Name}
    signal_type: measurement
    data_type: float
    engineering_unit: {unit}
    opcua_node_id: ns=2;s={OPC_UA_NODE_NAME}
    scale: 1.0
    vf_internal_ref: {VF_INTERNAL_VARIABLE}
    vf_sensor_id: {SENSOR_TAG}
```

---

## 6. Validation Checklist

Before submitting your new model, verify:

- [ ] `plant_id` is unique and follows naming convention
- [ ] All `asset_id` values are unique
- [ ] `parent_asset_id` references an existing `asset_id` (or is `null`)
- [ ] `area_id` in assets matches an `area.area_id`
- [ ] `asset_id` in signals matches an existing `asset.asset_id`
- [ ] `signal_id` format: `{asset_id}.{signal_name}`
- [ ] All `opcua_node_id` values follow `ns=2;s=NAME` format
- [ ] All `vf_internal_ref` values match VF simulator internal variable names
- [ ] `vf_sensor_id` values use standard instrument tag notation (PT, TT, FT, VT, CT, etc.)
- [ ] Engineering units are from the supported list (Section 2.4)
- [ ] Scale factors are correct (m3/s → m3/h needs `scale: 3600`)

---

## 7. Sensor Tag Convention

Use standard ISA-5.1 instrument tag notation for `vf_sensor_id`:

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
