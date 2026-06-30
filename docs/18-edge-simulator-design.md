# PlantOS Edge Simulator Design

## 1. Purpose

The Edge Simulator provides realistic enough operational data for PlantOS MVP development and demo.

It allows PlantOS to validate ingestion, historian, current value query, trend, dynamic diagrams, GIS, alarm and future MES/Virtual Factory integration before connecting to real equipment.

## 2. Simulator goals

The simulator must generate:

- asset states,
- numeric measurements,
- boolean statuses,
- quality values,
- simple abnormal conditions,
- heartbeat/status for edge node,
- optional alarm trigger scenarios.

## 3. Simulator non-goals

The MVP simulator does not need:

- full physics simulation,
- complex process model,
- 3D model,
- real PLC protocol emulation,
- full MES production workflow.

Those belong to Virtual Factory or later simulation modules.

## 4. Demo plant scope

Initial simulator should cover:

```text
DEMO-PLANT
├── PROCESS-AREA
│   └── LINE-01
│       ├── PUMP-101
│       ├── MOTOR-101
│       ├── TANK-101
│       └── VALVE-101
└── ELECTRICAL-AREA
    └── SUBSTATION-A
        ├── TRANSFORMER-01
        ├── FEEDER-01
        └── BREAKER-01
```

## 5. Example signals

### PUMP-101

```text
discharge_pressure: float, bar
flow_rate: float, m3/h
running_status: boolean
vibration_rms: float, mm/s
```

### MOTOR-101

```text
motor_current: float, A
motor_temperature: float, °C
running_status: boolean
```

### TANK-101

```text
tank_level: float, %
temperature: float, °C
```

### BREAKER-01

```text
breaker_status: boolean
voltage: float, kV
current: float, A
power: float, kW
```

## 6. Publishing modes

MVP should support HTTP ingestion first because it is simple to validate.

Optional MQTT publishing can be added after API ingestion works.

### HTTP mode

```text
Simulator → POST /api/v1/measurements/ingest
```

### MQTT mode

```text
Simulator → EMQX → backend ingestion subscriber
```

MQTT topic should follow governed UNS-like pattern, not arbitrary tag naming.

## 7. Data generation pattern

Signals should use simple time-based functions plus noise.

Example patterns:

- pressure oscillates around normal range,
- flow follows pump running status,
- tank level rises/falls slowly,
- motor current increases when running,
- breaker status changes occasionally,
- alarm scenario creates high pressure or high temperature.

## 8. Quality simulation

Supported quality values:

```text
GOOD
SIMULATED
STALE
BAD
MISSING
```

MVP can use `SIMULATED` for all simulator values or combine `GOOD` with source metadata.

Recommended:

```json
{
  "quality": "SIMULATED"
}
```

## 9. Configuration file

Simulator should load demo assets and signals from a config file.

Possible path:

```text
examples/demo-plant/demo-plant.yaml
```

Config should define:

- plant,
- areas,
- assets,
- signals,
- initial values,
- generation pattern,
- location,
- abnormal scenarios.

## 10. Heartbeat

Simulator should call:

```text
POST /api/v1/edge-nodes/heartbeat
```

Payload should include:

- edge_node_id,
- status,
- timestamp,
- buffered message count,
- publishing mode,
- simulator version.

## 11. Abnormal scenarios

Initial scenarios:

```text
normal_operation
pump_high_pressure
motor_high_temperature
breaker_trip
edge_offline
stale_data
```

These can be selected through config or command-line argument.

## 12. MVP acceptance criteria

- Simulator can register or rely on sample registered assets/signals.
- Simulator can publish measurements periodically.
- Backend accepts and stores measurements.
- UI trend updates from simulated data.
- Dynamic diagram changes based on simulated status.
- GIS marker status reflects simulated alarm/state.
- Heartbeat appears in Edge Fleet page.
