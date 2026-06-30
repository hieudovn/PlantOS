# PlantOS Storage and Historian Design

## 1. Purpose

This document defines how PlantOS stores metadata, time-series measurements, current values and future operational events.

PlantOS includes time-series and historian capability, but the Historian is a service inside PlantOS, not the whole product.

## 2. Storage responsibility split

```text
PostgreSQL
  asset registry
  signal registry
  device registry
  UNS paths
  schema registry
  visualization bindings
  rules/alarms metadata
  edge node registry

Time-Series DB
  timestamp
  signal_id
  value
  quality
  source

Redis / current cache (optional)
  latest values
  edge heartbeat cache
  short-lived UI cache

MinIO (future)
  diagrams
  GIS files
  reports
  attachments
  simulation packages
```

## 3. Metadata database: PostgreSQL

PostgreSQL is the source of truth for PlantOS metadata.

Initial tables:

```text
plants
areas
assets
devices
signals
uns_paths
edge_nodes
alarm_definitions
alarm_events
visualization_bindings
```

MVP can simplify `plants` and `areas` if needed, but the data model should keep these concepts visible.

## 4. Time-series database

Preferred MVP candidate: TDengine.

Alternative: VictoriaMetrics.

The backend must use a historian abstraction so a future switch does not affect API and UI.

## 5. Historian service responsibility

The Historian Service must support:

- write measurements,
- query latest value,
- query historical range,
- downsample/aggregate where supported,
- handle quality values,
- enforce signal registry validation,
- hide physical TSDB schema from UI and other application modules.

## 6. Measurement schema

Canonical measurement object:

```json
{
  "timestamp": "2026-06-30T10:00:00.000Z",
  "signal_id": "PUMP-101.discharge_pressure",
  "value": 7.2,
  "quality": "GOOD",
  "source": "edge-sim-01"
}
```

## 7. TDengine physical model direction

Implementation should be decided with an ADR, but the likely model is:

```text
stable: measurements
columns:
  ts TIMESTAMP
  value DOUBLE or NCHAR for non-numeric support later
  quality NCHAR
  source NCHAR

tags:
  signal_id NCHAR
  asset_id NCHAR
  signal_name NCHAR
  unit NCHAR
```

MVP can restrict measurement values to numeric and boolean-like values if this simplifies implementation.

## 8. Current value strategy

### MVP default

Query latest values from TSDB through Historian Service.

### Future optimization

Add current value cache:

```text
measurement ingestion
  ↓
write TSDB
  ↓
update current_value cache/table
```

Do not expose the cache directly to UI.

## 9. Retention and compression

MVP can use default retention.

Future policies:

```text
raw high-frequency data: short/medium retention
1-minute aggregate: longer retention
15-minute/hourly aggregate: long retention
alarm/event data: long retention
```

## 10. Built-in Historian positioning

PlantOS should support three deployment modes:

### Built-in Historian mode

For plants without existing Historian.

PlantOS TSDB is the operational historian.

### Historian integration mode

For plants with PI, Canary, IP.21 or other historians.

PlantOS maps external historian tags to PlantOS assets/signals and provides context above them.

### Hybrid mode

PlantOS stores contextualized/derived data while existing historian remains raw time-series system of record.

## 11. Data quality values

Supported MVP values:

```text
GOOD
BAD
UNCERTAIN
STALE
SIMULATED
MANUAL
ESTIMATED
MISSING
```

## 12. Storage rules

- UI must not know physical table names.
- Backend API must not leak TDengine schema.
- All measurements must reference registered signals.
- Signal registry must connect signal to asset.
- Raw tag/source references stay in metadata, not in UI bindings.
- Historian backend must be replaceable behind interface.

## 13. ADR required

Before implementation, create ADRs for:

- TSDB final choice,
- TDengine physical schema,
- current value strategy,
- numeric-only versus mixed-type measurement handling.
