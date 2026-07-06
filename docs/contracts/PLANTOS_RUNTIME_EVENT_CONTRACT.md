# PlantOS Runtime Event Contract

> **Version:** 2.0-final | **Date:** 2026-07-06  
> **Status:** Final — SA Approved. Implementation authorized.

---

## 1. UNS Topic Decision — Final

**Primary runtime topic model: hybrid**

| Event Type | Primary Topic | Rationale |
|-----------|--------------|-----------|
| `SignalValueUpdated` | `plantos/{plant}/{area}/{asset}/{category}/{signal_name}` | Signal-level. MES subscribes per signal or wildcard `plantos/+/+/+/measurement/#`. |
| `AssetStatusChanged` | `plantos/events/AssetStatusChanged` | Asset-level, not signal-specific. |
| `AlarmRaised` | `plantos/events/AlarmRaised` | Cross-cutting. Requires `correlation_id` for lifecycle pairing. |
| `AlarmCleared` | `plantos/events/AlarmCleared` | Cross-cutting. Same `correlation_id` as AlarmRaised. |
| `SignalQualityChanged` | `plantos/events/SignalQualityChanged` | Diagnostic. Signal-specific payload, event-level topic. |
| `EdgeHeartbeatReceived` | `plantos/events/EdgeHeartbeatReceived` | Fleet-level. |

**Reason:** Signal-level topic for telemetry data allows MES to subscribe to exactly the signals it needs. Event-level topic for cross-cutting/system events prevents topic explosion and simplifies MES subscription management.

---

## 2. Identity & Normalization Rules

### 2.1 Topic segments vs Payload identifiers

| Context | Format | Example |
|---------|--------|---------|
| MQTT topic segments | **Lowercase** | `plantos/vf-demo/compressor-area/comp01-core/measurement/speed` |
| Payload `asset.asset_id` | **Canonical** (preserves case) | `"COMP01-CORE"` |
| Payload `signal.signal_id` | **Canonical** (preserves case) | `"COMP01-CORE.speed"` |

**Rule:** MQTT topics are always lowercase. Payload identifiers preserve PlantOS canonical IDs exactly as stored. MES should use `asset.asset_id` and `signal.signal_id` from the payload as the primary identity mapping keys — never derive them from topic segments.

### 2.2 Primary vs Secondary Asset Identity

- **Primary mapping key:** `asset.asset_id` — guaranteed unique within PlantOS. MES must use this for crosswalk.
- **Secondary/reference:** `asset.asset_code` — display-friendly short code. May not be unique across plants.

### 2.3 uns_topic Semantics

| Event Type | uns_topic value |
|-----------|----------------|
| `SignalValueUpdated` | Signal UNS topic: `plantos/{plant}/{area}/{asset}/{category}/{signal}` |
| All other event types | Event topic: `plantos/events/{event_type}` |

`uns_topic` always reflects the **actual MQTT topic** this event was published to. Consumers can use it for routing/filtering without reconstructing the topic from identifiers.

---

## 3. Event Envelope — Common Section

```json
{
  "schema_version": "1.0",
  "source_system": "plantos_center",
  "event_id": "string (required, globally unique)",
  "correlation_id": "string | null (required for alarm pairs, optional otherwise)",
  "event_type": "string (required, controlled vocabulary)",
  "timestamp": "ISO8601 with timezone (required)",
  "asset": { "plant_id", "area_id", "asset_id", "asset_code", "asset_type", "asset_role" },
  "signal": { } | null,
  "edge": { } | null,
  "alarm": { } | null,
  "uns_topic": "string",
  "payload": { }
}
```

| Section | Present when | Null when |
|---------|-------------|-----------|
| `asset` | All events except EdgeHeartbeat | EdgeHeartbeatReceived |
| `signal` | SignalValueUpdated, SignalQualityChanged | All others |
| `edge` | EdgeHeartbeatReceived | All others |
| `alarm` | AlarmRaised, AlarmCleared | All others |
| `payload` | Always | Never |

---

## 4. Event-Specific Required Fields

### 4.1 SignalValueUpdated

```json
{
  "event_type": "SignalValueUpdated",
  "asset": { "plant_id": "WTP-DEMO-01", "area_id": "RAW-WATER-INTAKE", "asset_id": "HSP-101", "asset_code": "HSP101", "asset_type": "pump", "asset_role": "equipment" },
  "signal": { "signal_id": "HSP-101.flow_rate", "signal_name": "flow_rate", "signal_category": "measurement", "data_type": "float", "engineering_unit": "m3/h" },
  "uns_topic": "plantos/wtp-demo-01/raw-water-intake/hsp-101/measurement/flow_rate",
  "payload": { "value": 1250.5, "quality": "GOOD" },
  "correlation_id": null
}
```
Required: event_id, event_type, timestamp, asset, signal, uns_topic, payload.value, payload.quality

### 4.2 AssetStatusChanged

```json
{
  "event_type": "AssetStatusChanged",
  "signal": null,
  "payload": { "status": "maintenance", "previous_status": "active", "reason": "Scheduled bearing inspection" }
}
```
Required: event_id, event_type, timestamp, asset, payload.status.  
Optional: payload.previous_status, payload.reason

### 4.3 AlarmRaised

```json
{
  "event_type": "AlarmRaised",
  "correlation_id": "alarm-COMP01-MOTOR-OVERCURRENT-20260706T121030Z",
  "signal": null,
  "alarm": { "alarm_code": "OVERCURRENT", "severity": "critical", "description": "Motor current exceeded threshold", "state": "raised", "threshold_value": 100.0, "actual_value": 142.5 }
}
```
Required: event_id, event_type, timestamp, correlation_id, asset, alarm.alarm_code, alarm.severity, alarm.description, alarm.state="raised"

### 4.4 AlarmCleared

```json
{
  "event_type": "AlarmCleared",
  "correlation_id": "alarm-COMP01-MOTOR-OVERCURRENT-20260706T121030Z",
  "signal": null,
  "alarm": { "alarm_code": "OVERCURRENT", "severity": "critical", "state": "cleared", "cleared_by": "auto" }
}
```
Required: event_id, event_type, timestamp, correlation_id (must match AlarmRaised), asset, alarm.alarm_code, alarm.state="cleared"

### 4.5 SignalQualityChanged

```json
{
  "event_type": "SignalQualityChanged",
  "signal": { "signal_id": "COMP01-CORE.speed", "signal_name": "speed", "signal_category": "measurement" },
  "payload": { "quality": "BAD", "previous_quality": "GOOD", "reason": "OPC UA connection lost" }
}
```
Required: event_id, event_type, timestamp, asset, signal, payload.quality, payload.previous_quality

### 4.6 EdgeHeartbeatReceived

```json
{
  "event_type": "EdgeHeartbeatReceived",
  "asset": null, "signal": null,
  "edge": { "edge_id": "edge-wtp-01", "status": "online", "ip_address": "172.19.0.5", "signal_count": 92, "version": "0.1.0" }
}
```
Required: event_id, event_type, timestamp, edge.edge_id, edge.status

---

## 5. Event ID / Idempotency Convention

```
Format:  plantos-{entity_id_lower}-{YYYYMMDDTHHMMSSZ}-{random6}
Example: plantos-hsp-101.flow_rate-20260706t120000z-a1b2c3
Regex:   ^plantos-[a-z0-9_.-]+-\d{8}t\d{6}z-[a-f0-9]{6}$

Rules:
  - entity_id is lowercased (e.g., hsp-101.flow_rate, not HSP-101.flow_rate)
  - Timestamp uses lowercase 't' and 'z' (e.g., 20260706t120000z)
  - random6 is 6 lowercase hex characters [a-f0-9]
  - Globally unique. MES uses as idempotency key. Retries use same event_id.
```

- Globally unique. MES uses as idempotency key. Retries use same event_id.

---

## 6. QoS Policy — Final

| Event Type | QoS | Notes |
|-----------|:---:|-------|
| SignalValueUpdated | 0 | High frequency, loss-tolerant |
| AssetStatusChanged | 1 | State transition must deliver |
| AlarmRaised | 1 | Critical |
| AlarmCleared | 1 | Critical |
| SignalQualityChanged | 1 | Data reliability |
| EdgeHeartbeatReceived | 0 | Periodic, overwrites |

---

## 7. Alarm Lifecycle Rule

```text
1. AlarmRaised + AlarmCleared for same instance SHARE correlation_id
2. Format: alarm-{asset_id}-{alarm_code}-{ISO8601}
3. alarm_code = type, correlation_id = instance
4. AlarmRaised ≠ machine_down (MES derives later)
5. Re-raise = new correlation_id
```

---

## 8. Field Exclusion

PlantOS MUST NOT emit: `work_order_id`, `manufacturing_order_id`, `wo_ref`, `mo_ref`, `operation_code`, `product_code`, `material_lot_id`, `checklist_id`, `operator_id`, `shift_id`, `BOM_id`, `routing_id`.

---

## 9. Validation

```yaml
Structural: event_id format, timestamp ISO8601, event_type controlled vocabulary
Context:   asset/signal/edge/alarm presence per event type
Alarm:     state=raised/cleared, correlation_id match for pairs
Exclusion: no WO/MO/Operation fields
```

---

## 10. Bundle Verification

This contract has been verified against all 5 bundle requirements:

1. ✅ `event_id` format finalized: `plantos-{entity_id_lower}-{YYYYMMDDTHHMMSSZ}-{random6}`, retry uses same event_id
2. ✅ Identity mapping: `asset.asset_id` primary, `signal.signal_id` primary, `asset.asset_code` secondary
3. ✅ Topic model finalized: hybrid — signal UNS for `SignalValueUpdated`, `plantos/events/{event_type}` for system events
4. ✅ `uns_topic` semantics: signal UNS topic for `SignalValueUpdated`, event topic for system events
5. ✅ No MES production context fields in any payload

---

> **This contract is the source of truth for MES PlantOSAdapter implementation.**
> Any later change to runtime topic, event envelope, event_id, identity key, alarm lifecycle, or QoS policy must be versioned and reviewed by SA + MES PM before implementation impact is accepted.
