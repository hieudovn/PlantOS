# PlantOS Data Model Foundation

## 1. Data model objective

PlantOS must not be a tag-only platform.

The data model must connect time-series measurements, events, alarms, devices, assets, process context, production context and application objects into one coherent operational model.

## 2. Core modeling layers

```text
Physical Layer
  Plant / Area / Line / System / Asset / Device

Signal Layer
  Tag / Signal / Measurement / Quality / Unit

Event Layer
  Event / Alarm / State Change / Command / Checklist / Operation

Context Layer
  Process / Material / Batch / Work Order / Production Order / Maintenance Context

Application Layer
  MES Object / Virtual Factory Object / AHM Object / AI Context Object
```

## 3. Core entities

### Plant

Represents a production site or facility.

Typical fields:

- plant_id,
- name,
- location,
- industry,
- timezone,
- owner,
- status.

### Area

Represents a physical or functional area inside a plant.

Examples:

- boiler area,
- turbine area,
- packaging area,
- utility area,
- electrical substation,
- production line.

### Asset

Represents an industrial equipment or logical asset.

Examples:

- pump,
- motor,
- valve,
- tank,
- compressor,
- conveyor,
- transformer,
- feeder,
- production line.

Asset fields should include:

- asset_id,
- asset_code,
- asset_type,
- parent_asset_id,
- area_id,
- criticality,
- lifecycle_status,
- location,
- manufacturer/model where available.

### Device

Represents data source hardware or logical endpoint.

Examples:

- PLC,
- RTU,
- gateway,
- sensor,
- meter,
- OPC UA server,
- MQTT device.

### Signal

Represents a semantic measurement or state associated with an asset/device.

Signal is not equal to raw tag.

Examples:

- discharge_pressure,
- motor_current,
- running_status,
- vibration_rms,
- bearing_temperature,
- breaker_status.

Signal fields:

- signal_id,
- asset_id,
- device_id,
- signal_name,
- signal_type,
- engineering_unit,
- data_type,
- sampling_policy,
- quality_policy,
- source_tag_ref.

### Raw Tag

Represents protocol or historian-level identifier.

Examples:

- PLC tag path,
- OPC UA NodeId,
- Modbus register,
- MQTT topic,
- PI tag name,
- Canary tag name.

Raw tags must be mapped to PlantOS signals.

### Measurement

A time-series data point.

Canonical minimum structure:

```json
{
  "timestamp": "2026-06-30T10:00:00.000Z",
  "signal_id": "PUMP-101.discharge_pressure",
  "value": 7.2,
  "quality": "GOOD",
  "unit": "bar",
  "source": "edge-01"
}
```

### Event

Represents a meaningful occurrence.

Examples:

- asset state change,
- production step started,
- alarm triggered,
- operator action,
- maintenance action,
- data quality event,
- command issued.

### Alarm

An event requiring attention.

Alarm fields:

- alarm_id,
- asset_id,
- signal_id,
- severity,
- state,
- start_time,
- end_time,
- acknowledged_by,
- acknowledged_at,
- rule_id,
- message.

## 4. Unified Namespace model

UNS is the operational address space.

Recommended path pattern:

```text
enterprise/site/area/line_or_system/asset/signal_or_event
```

Example:

```text
avenue/demo-plant/packaging/line-01/pump-101/discharge_pressure
avenue/demo-plant/electrical/substation-a/feeder-01/breaker_status
```

UNS path should not be a direct PLC tag dump. It must be governed by asset and signal registry.

## 5. Canonical Data Model direction

CDM defines reusable objects that other applications can consume.

Initial CDM domains:

```text
Asset
Device
Signal
Measurement
Event
Alarm
ProductionOrder
ManufacturingOrder
Operation
Material
QualityCheck
Checklist
MaintenanceWorkOrder
EnergyMeter
Location
```

MES, Virtual Factory, AHM and AI applications should consume these CDM objects instead of redefining private models.

## 6. Signal-to-asset binding

Do not bind UI and rules directly to raw tags.

Bad:

```text
Widget → PLC_TAG_001
```

Good:

```text
Widget → asset_id + signal_name → PlantOS API → current/historical value
```

Example binding:

```json
{
  "binding_type": "asset_signal",
  "asset_id": "PUMP-101",
  "signal": "discharge_pressure",
  "mode": "realtime"
}
```

## 7. Data quality

Every measurement should carry quality metadata.

Recommended quality values:

- GOOD,
- BAD,
- UNCERTAIN,
- STALE,
- SIMULATED,
- MANUAL,
- ESTIMATED,
- MISSING.

## 8. Historian data versus contextual data

The historian service stores high-volume time-series data.

The contextual model stores relationships and meaning.

```text
Time-Series DB:
  timestamp, signal_id, value, quality

PostgreSQL / metadata DB:
  asset, device, signal, schema, rule, binding, context
```

Applications should not depend on physical storage layout.

## 9. MES compatibility

MES integration must use CDM-aligned events and objects:

- production order,
- manufacturing order,
- operation,
- workstation,
- material consumption,
- quality event,
- checklist event,
- equipment state,
- downtime event.

PlantOS provides equipment and signal context; MES provides production and execution context. Both must meet at shared CDM/event contracts.

## 10. Virtual Factory compatibility

Virtual Factory should use the same PlantOS asset, signal, event and CDM structures.

Simulation should publish data as if it came from real edge nodes.

This allows the same visualization, historian, rule, alarm and MES integration layers to work with both real and simulated plants.
