# ADR-0004: OPC UA -> PlantOS CDM Mapping

## Status

Accepted

## Context

PlantOS integrates with Virtual Factory via OPC UA. VF publishes raw OPC UA variables
with flat NodeIds. PlantOS must map these to hierarchical CDM signal_ids.

## Decision

### 1. Collector Pattern

Same as Modbus collector: client -> mapper -> collector -> DuckDB -> sync.

### 2. Asset Hierarchy

PlantOS assets mirror sub-system structure:

- COMP01 (compressor_train) -> COMP01-MOTOR, COMP01-CORE, COMP01-BEARINGS,
  COMP01-LUBE, COMP01-COOLING, COMP01-SEAL

### 3. Signal Naming

`{ASSET_ID}.{physical_property}` -- e.g. `COMP01-MOTOR.vibration_de`

### 4. Unit Conversion

Edge mapper handles: `COMP01_FLOW` m3/s x 3600 -> m3/h. All others 1:1.

### 5. Virtual Factory Independence

VF knows nothing about PlantOS CDM. All CDM packaging in PlantOS Edge + Center.

## Consequences

- VF deployable independently
- Pattern reusable for any OPC UA source
- Asset hierarchy enables sub-system analytics drill-down
