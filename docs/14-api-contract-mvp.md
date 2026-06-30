# PlantOS MVP API Contract

## 1. Purpose

This document defines the first API contract for PlantOS MVP.

The contract is intentionally simple but must preserve PlantOS principles:

- asset/signal binding,
- no raw tag dependency in UI,
- historian abstraction,
- UNS-aware data access,
- CDM-ready objects.

## 2. Base URL

```text
/api/v1
```

## 3. Common object fields

Most metadata objects should include:

```json
{
  "id": "string",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

## 4. Asset APIs

### Create asset

```http
POST /api/v1/assets
```

Request:

```json
{
  "asset_id": "PUMP-101",
  "asset_code": "PUMP-101",
  "name": "Feed Pump 101",
  "asset_type": "pump",
  "parent_asset_id": null,
  "plant_id": "DEMO-PLANT",
  "area_id": "PROCESS-AREA",
  "criticality": "medium",
  "location": {
    "lat": 10.762622,
    "lng": 106.660172
  }
}
```

Response:

```json
{
  "asset_id": "PUMP-101",
  "name": "Feed Pump 101",
  "asset_type": "pump",
  "plant_id": "DEMO-PLANT",
  "area_id": "PROCESS-AREA",
  "status": "active"
}
```

### List assets

```http
GET /api/v1/assets
```

Optional filters:

```text
plant_id
area_id
asset_type
parent_asset_id
```

### Get asset detail

```http
GET /api/v1/assets/{asset_id}
```

## 5. Signal APIs

### Create signal

```http
POST /api/v1/signals
```

Request:

```json
{
  "signal_id": "PUMP-101.discharge_pressure",
  "asset_id": "PUMP-101",
  "signal_name": "discharge_pressure",
  "display_name": "Discharge Pressure",
  "signal_type": "measurement",
  "data_type": "float",
  "engineering_unit": "bar",
  "source": {
    "source_type": "simulator",
    "source_ref": "sim://pump-101/discharge_pressure"
  },
  "uns_path": "avenue/demo-plant/process-area/line-01/pump-101/discharge_pressure"
}
```

Response:

```json
{
  "signal_id": "PUMP-101.discharge_pressure",
  "asset_id": "PUMP-101",
  "signal_name": "discharge_pressure",
  "engineering_unit": "bar",
  "uns_path": "avenue/demo-plant/process-area/line-01/pump-101/discharge_pressure"
}
```

### List signals

```http
GET /api/v1/signals
```

Optional filters:

```text
asset_id
signal_type
data_type
```

### Get signal detail

```http
GET /api/v1/signals/{signal_id}
```

## 6. Measurement APIs

### Ingest measurements

```http
POST /api/v1/measurements/ingest
```

Request:

```json
{
  "source": "edge-sim-01",
  "measurements": [
    {
      "timestamp": "2026-06-30T10:00:00.000Z",
      "signal_id": "PUMP-101.discharge_pressure",
      "value": 7.2,
      "quality": "GOOD"
    }
  ]
}
```

Response:

```json
{
  "accepted": 1,
  "rejected": 0,
  "errors": []
}
```

### Query current values

```http
GET /api/v1/measurements/current?asset_id=PUMP-101
```

or:

```http
GET /api/v1/measurements/current?signal_id=PUMP-101.discharge_pressure
```

Response:

```json
{
  "items": [
    {
      "asset_id": "PUMP-101",
      "signal_id": "PUMP-101.discharge_pressure",
      "signal_name": "discharge_pressure",
      "timestamp": "2026-06-30T10:00:00.000Z",
      "value": 7.2,
      "quality": "GOOD",
      "unit": "bar"
    }
  ]
}
```

### Query historical values

```http
GET /api/v1/measurements/history?signal_id=PUMP-101.discharge_pressure&from=2026-06-30T09:00:00Z&to=2026-06-30T10:00:00Z&interval=1m
```

Response:

```json
{
  "signal_id": "PUMP-101.discharge_pressure",
  "unit": "bar",
  "items": [
    {
      "timestamp": "2026-06-30T09:00:00.000Z",
      "value": 7.0,
      "quality": "GOOD"
    }
  ]
}
```

## 7. UNS APIs

### List UNS paths

```http
GET /api/v1/uns/paths
```

Optional filters:

```text
plant_id
area_id
asset_id
```

Response:

```json
{
  "items": [
    {
      "uns_path": "avenue/demo-plant/process-area/line-01/pump-101/discharge_pressure",
      "asset_id": "PUMP-101",
      "signal_id": "PUMP-101.discharge_pressure"
    }
  ]
}
```

## 8. Alarm APIs

### List alarms

```http
GET /api/v1/alarms
```

MVP may return generated or placeholder alarms.

Response:

```json
{
  "items": [
    {
      "alarm_id": "ALM-001",
      "asset_id": "PUMP-101",
      "signal_id": "PUMP-101.discharge_pressure",
      "severity": "high",
      "state": "active",
      "message": "Discharge pressure high",
      "start_time": "2026-06-30T10:00:00.000Z"
    }
  ]
}
```

## 9. Edge node APIs

### Heartbeat

```http
POST /api/v1/edge-nodes/heartbeat
```

Request:

```json
{
  "edge_node_id": "edge-sim-01",
  "name": "Demo Edge Simulator",
  "status": "online",
  "timestamp": "2026-06-30T10:00:00.000Z",
  "metrics": {
    "buffered_messages": 0,
    "cpu_percent": 12.5,
    "memory_percent": 45.0
  }
}
```

### List edge nodes

```http
GET /api/v1/edge-nodes
```

## 10. API rules

- Use `asset_id` and `signal_id` in UI-facing APIs.
- Do not expose TSDB table names to frontend.
- Do not require frontend to know source tag names.
- Return quality and unit with measurements.
- Keep timestamps timezone-aware.
- Keep error responses structured.

## 11. Future API groups

Not MVP:

- `/api/v1/rules`,
- `/api/v1/visualizations`,
- `/api/v1/diagrams`,
- `/api/v1/gis-layers`,
- `/api/v1/mes-events`,
- `/api/v1/semantic-query`,
- `/api/v1/users`,
- `/api/v1/tenants`.
