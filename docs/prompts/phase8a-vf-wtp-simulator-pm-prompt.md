# Prompt for PM-Designer — Virtual Factory WTP Simulator for PlantOS Phase 8A

You are the PM-Designer-Planner for the **Virtual Factory** project.

## Context

PlantOS Phase 8A is building the first industry reference model:

```text
WTP-DEMO-01 — Water Treatment Plant Reference Model
```

The data contract between PlantOS and Virtual Factory is the **PlantOS Integration Contract v2**, stored at:

```text
examples/contracts/wtp-demo-01.contract.yaml
```

This contract defines the plant model (areas, assets, signals) that both PlantOS and Virtual Factory share as a single source of truth.

Your job is to design and plan the **Virtual Factory WTP Simulator** that reads this contract and generates realistic telemetry for PlantOS ingestion.

## Required Reading (from the PlantOS repo)

Before planning, read these files from the PlantOS repository:

```text
docs/contracts/plantos-integration-contract-spec.md     ← understand contract structure
schemas/plantos-integration-contract.schema.json         ← understand schema
examples/contracts/wtp-demo-01.contract.yaml             ← THE contract to implement
examples/contracts/vf-compressor-train.contract.yaml     ← existing VF example for reference
```

## What PlantOS Already Provides

PlantOS provides these ingestion endpoints (no need to build):

```text
POST /api/v1/measurements/ingest
Content-Type: application/json

{
  "measurements": [
    {
      "timestamp": "2026-07-02T10:00:00.000Z",
      "signal_id": "RWP-101.flow_rate",
      "value": 450.5,
      "quality": "GOOD",
      "source": "wtp-sim-01"
    }
  ]
}
```

PlantOS handles:
- Signal registry (from contract)
- UNS path generation
- Historian storage (TDengine)
- Current value query
- Historical trend query
- Visualization (trend, P&ID, GIS)

## What Virtual Factory Must Build

### A. WTP Process Simulator

Build a Python simulator that:

1. **Reads the contract file** (`wtp-demo-01.contract.yaml`)
2. **Parses the `simulation.behaviors` section** to get signal patterns
3. **Generates telemetry** for ALL signals at configurable interval (default 1 second)
4. **Publishes** measurements to PlantOS via `POST /api/v1/measurements/ingest`
5. **Supports 8 scenarios** defined in the contract's simulation section

### B. Simulation Behavior Patterns

The contract's `simulation.behaviors` section defines how each signal should be simulated. Support these pattern types:

| Pattern | Behavior | Parameters |
|---------|----------|------------|
| `sine` | Oscillating signal | `mid`, `amplitude`, `noise`, `frequency_hz` |
| `random_walk` | Random walk with bounds | `baseline`, `bounds_min`, `bounds_max`, `noise`, `step_size` |
| `constant` | Fixed value with noise | `mid`, `noise` |
| `step` | Step changes | `mid`, `step_size`, `noise` |
| `degradation` | Slow drift upward/downward | `baseline`, `drift_rate`, `noise` |
| `dependent` | Value depends on another signal | `depends_on` (signal_id), `transform` (formula string) |

### C. Dependent Signal Engine

Some WTP signals depend on upstream signals. For example:

```yaml
# settled_turbidity depends on raw_turbidity
- signal_id: CLARIFIER-QUALITY-STATION-101.settled_turbidity
  pattern: dependent
  depends_on: RAW-WATER-QUALITY-STATION-101.raw_turbidity
  transform: "max(1.0, input * 0.18 + noise(0, 0.5))"
```

The simulator must:
1. Evaluate signals in dependency order (upstream first)
2. Support `input` variable (value of the depended-on signal)
3. Support `noise(mean, std)` function in transform expressions
4. Support basic math: `+`, `-`, `*`, `/`, `max()`, `min()`, `abs()`, `clamp()`

### D. Scenario System

8 scenarios are defined. Each scenario overrides signal parameters:

```yaml
scenarios:
  - scenario_id: normal_operation
    name: Normal Operation
    description: Stable production, compliant outlet quality.
    overrides: {}  # use default behaviors

  - scenario_id: raw_water_contamination
    name: Raw Water Contamination Event
    description: Raw turbidity/COD/ammonia increase.
    overrides:
      RAW-WATER-QUALITY-STATION-101.raw_turbidity:
        baseline: 80.0
        bounds_min: 50.0
        bounds_max: 150.0
      RAW-WATER-QUALITY-STATION-101.raw_cod:
        mid: 45.0
        amplitude: 10.0
```

The simulator must:
1. Start with `normal_operation` by default
2. Allow hot-switching scenarios via HTTP endpoint: `POST /scenario/{scenario_id}`
3. Smoothly transition between scenarios (not abrupt jumps)

### E. Key WTP Process Logic

The WTP process has these treatment chain relationships (the simulator must respect them):

```
Raw Water Quality
    ↓ (coagulation reduces turbidity by ~80-85%)
Settled Water Quality (clarifier)
    ↓ (filtration reduces turbidity by ~95-98%)
Filtered Water Quality
    ↓ (disinfection adds chlorine, no turbidity change)
Disinfected Water Quality
    ↓ (clear water tank — same quality)
Clear Water Quality
    ↓ (pumping — same quality)
Outlet Quality
```

Key process rules:
- **Turbidity**: raw (10-120 NTU) → settled (2-20 NTU) → filtered (0.1-1.0 NTU) → outlet (0.1-1.0 NTU)
- **pH**: Typically 6.5-8.5, coagulation may lower pH slightly
- **Chlorine**: Free chlorine target 0.5-1.0 mg/L at outlet
- **Filter DP**: Increases over time (filter clogging), reset on backwash
- **Energy**: Total active power ~500-800 kW depending on pump load
- **Chemical dosing**: Coagulant dose proportional to raw turbidity (~20-80 L/h)
- **Production**: ~800-1000 m³/h typical throughput

### F. WTP-Specific Signal Categories

The 97 signals fall into these categories:

| Category | Count | Example Signals |
|----------|-------|----------------|
| Process (flow, pressure, level) | 28 | flow_rate, discharge_pressure, tank_level |
| Equipment Health (motor) | 8 | motor_current, vibration_de, winding_temp |
| Water Quality | 27 | turbidity, pH, conductivity, chlorine, ORP, ammonia, COD |
| Energy Monitoring | 5 | total_active_power, specific_energy_consumption |
| Chemical Consumption | 6 | coagulant_dose_rate, chlorine_specific_consumption |
| Traceability & KPIs | 12 | outlet_quality_risk_score, cost_per_m3 |
| Derived/Calculated | ~11 | quality indices, compliance status, CT value |

## Deliverables

### 1. Design Document

Create a design doc in your Virtual Factory repo:

```text
docs/wtp-simulator-design.md
```

Must include:
- Architecture overview
- Signal dependency graph
- Simulation engine design
- Scenario system design
- Data flow (simulator → PlantOS)
- Signal category breakdown with realistic value ranges
- Error handling and retry logic

### 2. Simulator Implementation

```text
simulators/wtp/wtp_simulator.py          ← main simulator
simulators/wtp/wtp_config.yaml           ← configuration (PlantOS URL, interval, etc.)
simulators/wtp/scenarios/                ← scenario definitions
simulators/wtp/requirements.txt          ← dependencies
```

### 3. Scenario Definitions

Create 8 scenario files with realistic override parameters:

```text
simulators/wtp/scenarios/normal_operation.yaml
simulators/wtp/scenarios/raw_water_contamination.yaml
simulators/wtp/scenarios/algae_bloom.yaml
simulators/wtp/scenarios/filter_breakthrough.yaml
simulators/wtp/scenarios/chlorine_underdosing.yaml
simulators/wtp/scenarios/chemical_overdosing.yaml
simulators/wtp/scenarios/filter_clogging_energy_impact.yaml
simulators/wtp/scenarios/hsp_trip.yaml
```

### 4. Test Suite

```text
simulators/wtp/tests/
    test_signal_generation.py
    test_dependent_signals.py
    test_scenarios.py
    test_ingestion.py
```

## Non-Negotiable Guardrails

1. Do NOT modify the PlantOS contract file. Read-only.
2. Do NOT hardcode PlantOS API URLs. Use config.
3. All measurements must include: timestamp (ISO 8601 UTC), signal_id, value, quality, source.
4. Quality must be "GOOD" for normal operation, "UNCERTAIN" or "BAD" for abnormal.
5. Timestamps must be in UTC.
6. The simulator must handle PlantOS being temporarily unavailable (retry with backoff).
7. Do NOT build a UI for the simulator. CLI + HTTP API only.
8. Do NOT implement OPC UA server. Use HTTP ingestion only.

## Realistic Value Ranges for Key Signals

Use these as starting points for simulation parameters:

| Signal | Unit | Normal Range | Abnormal Range |
|--------|------|-------------|----------------|
| raw_turbidity | NTU | 10-50 | 50-120 |
| settled_turbidity | NTU | 1.5-8 | 8-25 |
| filtered_turbidity | NTU | 0.1-0.5 | 0.5-2.0 |
| outlet_turbidity | NTU | 0.1-0.5 | 0.5-2.0 |
| raw_pH | pH | 6.8-7.5 | 5.5-9.0 |
| free_chlorine | mg/L | 0.5-1.0 | 0.0-0.3 |
| raw_ammonia | mg/L | 0.05-0.5 | 0.5-2.0 |
| raw_cod | mg/L | 5-20 | 20-60 |
| total_active_power | kW | 500-750 | 750-900 |
| filter_dp | kPa | 20-50 | 50-100 |
| coagulant_dose_rate | L/h | 20-60 | 60-100 |
| flow_rate (outlet) | m³/h | 800-1000 | 400-800 |
| specific_energy_consumption | kWh/m³ | 0.35-0.55 | 0.55-0.80 |
| cost_per_m3 | VND/m³ | 2500-4000 | 4000-6000 |

## Acceptance Criteria

The VF WTP Simulator is accepted when:

1. It reads `wtp-demo-01.contract.yaml` and extracts all 97 signals.
2. It generates realistic values within the specified ranges.
3. Dependent signals correctly follow upstream values.
4. All 8 scenarios can be activated and produce visibly different behavior.
5. Measurements are posted to PlantOS ingestion endpoint successfully.
6. PlantOS can query current values for all 97 signals.
7. PlantOS can query historical trends for the treatment chain.
8. Scenario switching works via HTTP endpoint.
9. Retry logic works when PlantOS is unavailable.
10. At least 5 scenarios demonstrate visible impact on outlet quality and cost KPIs.

## Required PM Output

Before coding, produce:

1. Understanding of the WTP simulation challenge.
2. Signal dependency graph (which signals depend on which).
3. Simulation engine architecture and data flow.
4. Scenario parameter design for all 8 scenarios.
5. API design for scenario switching.
6. Risk assessment.
7. Task breakdown for your Coder.
8. File structure and module list.

Do not code until the PM plan is reviewed.

---

## Appendix: Quick Reference — Contract Structure

The contract has these sections relevant to VF:

```yaml
signals:                          # All 97 signal definitions
  - signal_id: RWP-101.flow_rate
    signal_name: flow_rate
    data_type: float
    engineering_unit: m3/h
    ...

simulation:                       # VF SIMULATION CONFIG
  default_scenario: normal_operation
  behaviors:                      # How to simulate each signal
    "RWP-101.flow_rate":
      pattern: sine
      mid: 450.0
      amplitude: 35.0
      noise: 5.0
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity":
      pattern: random_walk
      baseline: 35.0
      bounds_min: 10.0
      bounds_max: 120.0
      noise: 3.0
    "CLARIFIER-QUALITY-STATION-101.settled_turbidity":
      pattern: dependent
      depends_on: RAW-WATER-QUALITY-STATION-101.raw_turbidity
      transform: "max(1.0, input * 0.18 + noise(0, 0.5))"
    ...

  scenarios:                      # 8 scenarios
    - scenario_id: normal_operation
      ...
    - scenario_id: raw_water_contamination
      ...

extensions:
  monitoring:                     # Dashboard and alarm specs (for PlantOS, not VF)
    ...
```

The `plant`, `areas`, `assets`, `uns`, `bindings` sections are used by PlantOS, not VF directly. VF only needs `signals` (for metadata) and `simulation` (for behavior config).
