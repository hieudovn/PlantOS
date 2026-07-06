# PlantOS Runtime Event Contract — Draft for SA Review

> **Version:** 1.0-draft | **Date:** 2026-07-06  
> **Status:** Pending SA approval before Phase 9D implementation

---

## 1. UNS Topic Decision

| Event Type | UNS Topic | Rationale |
|-----------|-----------|-----------|
| `SignalValueUpdated` | `plantos/{plant}/{area}/{asset}/{category}/{signal_name}` | Signal-level topic — direct mapping to data source. MES can subscribe per signal. |
| `AssetStatusChanged` | `plantos/events/AssetStatusChanged` | Asset-level event — not signal-specific. |
| `AlarmRaised` | `plantos/events/AlarmRaised` | Alarm event — cross-cutting concern. |
| `AlarmCleared` | `plantos/events/AlarmCleared` | Alarm event — cross-cutting concern. |
| `SignalQualityChanged` | `plantos/events/SignalQualityChanged` | Diagnostic event. |
| `EdgeHeartbeatReceived` | `plantos/events/EdgeHeartbeatReceived` | Fleet-level event. |

**Decision:** Signal-level topic for `SignalValueUpdated` (SA recommendation). Event-level topic for all others. This allows MES to subscribe to individual signals or wildcard `plantos/+/+/+/measurement/#` for all measurements.

---

## 2. Event Envelope

### 2.1 Common Envelope (all events)

```json
{
  "schema_version": "1.0",
  "source_system": "plantos_center",
  "event_id": "string (required, globally unique)",
  "correlation_id": "string | null (optional, for chaining related events)",
  "event_type": "string (required, from controlled vocabulary)",
  "timestamp": "ISO8601 with timezone (required)",
  "asset": {
    "plant_id": "string",
    "area_id": "string",
    "asset_id": "string",
    "asset_code": "string",
    "asset_type": "string",
    "asset_role": "string"
  },
  "signal": {
    "signal_id": "string (present for signal-specific events)",
    "signal_name": "string",
    "signal_category": "string",
    "data_type": "string",
    "engineering_unit": "string"
  },
  "uns_topic": "string (the topic this event was published to)",
  "payload": { }
}
```

### 2.2 event_id Convention

```
Format:  plantos-{entity_id}-{ISO8601_compact}-{random6}
Example: plantos-COMP01-CORE.speed-20260706T120000Z-a1b2c3
         plantos-COMP01-MOTOR-20260706T120000Z-d4e5f6     (asset event)
         plantos-edge-wtp-01-20260706T120000Z-g7h8i9      (edge event)

Rules:
- Always starts with "plantos-"
- {entity_id} is signal_id for signal events, asset_id for asset events, edge hostname for edge events
- {ISO8601_compact} is YYYYMMDDTHHMMSSZ
- {random6} is 6 lowercase hex characters
- Globally unique across all event types
- Doubles as idempotency key for MES deduplication
```

### 2.3 correlation_id

```yaml
Purpose: Chain related events (e.g., all signals from one Edge flush cycle)
Required: No (optional, null when not applicable)
Format:   plantos-flush-{edge_hostname}-{ISO8601}
Example:  "plantos-flush-edge-wtp-01-20260706T120000Z"
```

---

## 3. Event-Specific Payload Schemas

### 3.1 SignalValueUpdated

```json
{
  "event_type": "SignalValueUpdated",
  "uns_topic": "plantos/wtp-demo-01/intake-area/hsp-101/measurement/flow_rate",
  "signal": {
    "signal_id": "HSP-101.flow_rate",
    "signal_name": "flow_rate",
    "signal_category": "measurement",
    "data_type": "float",
    "engineering_unit": "m3/h"
  },
  "payload": {
    "value": 1250.5,
    "quality": "GOOD"
  }
}
```

| Payload Field | Type | Required | Description |
|--------------|------|----------|-------------|
| `value` | number \| bool | ✅ | Current signal value |
| `quality` | string | ✅ | GOOD, BAD, UNCERTAIN, STALE, SIMULATED, MISSING |

### 3.2 AssetStatusChanged

```json
{
  "event_type": "AssetStatusChanged",
  "signal": null,
  "payload": {
    "previous_status": "active",
    "new_status": "maintenance",
    "reason": "Scheduled maintenance window"
  }
}
```

| Payload Field | Type | Required | Description |
|--------------|------|----------|-------------|
| `previous_status` | string | ✅ | active, inactive, maintenance, decommissioned |
| `new_status` | string | ✅ | active, inactive, maintenance, decommissioned |
| `reason` | string | No | Human-readable reason for status change |

### 3.3 AlarmRaised

```json
{
  "event_type": "AlarmRaised",
  "signal": null,
  "payload": {
    "alarm_code": "OVERCURRENT",
    "severity": "critical",
    "description": "Motor current exceeded threshold",
    "threshold_value": 100.0,
    "actual_value": 142.5
  }
}
```

| Payload Field | Type | Required | Description |
|--------------|------|----------|-------------|
| `alarm_code` | string | ✅ | Machine-readable alarm code |
| `severity` | string | ✅ | critical, high, medium, low |
| `description` | string | ✅ | Human-readable description |
| `threshold_value` | number | No | Configured threshold |
| `actual_value` | number | No | Measured value at alarm time |

### 3.4 AlarmCleared

```json
{
  "event_type": "AlarmCleared",
  "signal": null,
  "payload": {
    "alarm_code": "OVERCURRENT",
    "cleared_by": "auto"
  }
}
```

| Payload Field | Type | Required | Description |
|--------------|------|----------|-------------|
| `alarm_code` | string | ✅ | Must match the AlarmRaised alarm_code |
| `cleared_by` | string | No | "auto" or username |

**Lifecycle rule:** Every `AlarmRaised` must eventually have a matching `AlarmCleared` with the same `alarm_code` on the same asset. MES should not auto-clear alarms on PlantOS events alone — wait for explicit AlarmCleared.

### 3.5 SignalQualityChanged

```json
{
  "event_type": "SignalQualityChanged",
  "signal": {
    "signal_id": "COMP01-CORE.speed",
    "signal_name": "speed",
    "signal_category": "measurement"
  },
  "payload": {
    "previous_quality": "GOOD",
    "new_quality": "BAD",
    "reason": "OPC UA connection lost"
  }
}
```

| Payload Field | Type | Required | Description |
|--------------|------|----------|-------------|
| `previous_quality` | string | ✅ | GOOD, BAD, UNCERTAIN, STALE, SIMULATED, MISSING |
| `new_quality` | string | ✅ | GOOD, BAD, UNCERTAIN, STALE, SIMULATED, MISSING |
| `reason` | string | No | Diagnostic reason for quality transition |

### 3.6 EdgeHeartbeatReceived

```json
{
  "event_type": "EdgeHeartbeatReceived",
  "signal": null,
  "payload": {
    "edge_hostname": "edge-wtp-01",
    "ip_address": "192.168.1.100",
    "signal_count": 92,
    "version": "0.1.0"
  }
}
```

| Payload Field | Type | Required | Description |
|--------------|------|----------|-------------|
| `edge_hostname` | string | ✅ | Edge agent hostname |
| `ip_address` | string | No | Edge agent IP |
| `signal_count` | int | ✅ | Number of signals managed by this edge |
| `version` | string | No | Edge agent version |

---

## 4. QoS Policy

| Event Type | MQTT QoS | Rationale |
|-----------|----------|-----------|
| `SignalValueUpdated` | QoS 0 | High frequency (~3-20/s). Loss-tolerant — next sample overwrites. |
| `AssetStatusChanged` | QoS 1 | Low frequency. State transition must be delivered. |
| `AlarmRaised` | QoS 1 | Must not lose alarm events. |
| `AlarmCleared` | QoS 1 | Must not lose alarm clearance. |
| `SignalQualityChanged` | QoS 0 | Diagnostic. Next quality update overwrites. |
| `EdgeHeartbeatReceived` | QoS 0 | Periodic. Next heartbeat overwrites. |

---

## 5. Delivery

- **Primary:** MQTT via EMQX (`plantos-net` Docker network)
- **Topics:** Signal-level for `SignalValueUpdated`; `plantos/events/{event_type}` for others
- **Format:** JSON, UTF-8, no envelope compression
- **Retain:** No MQTT retained messages (events are point-in-time)

---

## 6. Validation Rules

```yaml
Structural:
  - event_id: required, format plantos-{entity}-{ISO8601}-{random6}
  - timestamp: required, ISO8601 with timezone (Z or +HH:MM)
  - event_type: required, in controlled vocabulary
  - source_system: required, must equal "plantos_center"
  - correlation_id: if present, non-empty string; null otherwise

Referential:
  - asset.asset_id: must exist in PlantOS asset registry
  - signal.signal_id: must exist for SignalValueUpdated, SignalQualityChanged
  - uns_topic: must match derived topic from identifiers

Payload (by event_type):
  - SignalValueUpdated: value + quality required; quality in controlled vocab
  - AssetStatusChanged: previous_status + new_status required
  - AlarmRaised: alarm_code + severity + description required
  - AlarmCleared: alarm_code required
  - SignalQualityChanged: previous_quality + new_quality required
  - EdgeHeartbeatReceived: edge_hostname + signal_count required
```
