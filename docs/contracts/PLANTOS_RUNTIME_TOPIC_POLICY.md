# PlantOS Runtime Topic Policy

> **Version:** 1.0 | **Date:** 2026-07-06  
> **Status:** Final — approved as part of Phase 9C-9D

---

## 1. Topic Model

PlantOS uses a **hybrid topic model**:

| Category | Topic Pattern | Usage |
|----------|--------------|-------|
| **Signal UNS** | `plantos/{plant}/{area}/{asset}/{category}/{signal_name}` | Telemetry data (`SignalValueUpdated`) |
| **Event** | `plantos/events/{event_type}` | Cross-cutting/system events |

## 2. Signal UNS Topics

```
Pattern: plantos/{plant_id_lower}/{area_id_lower}/{asset_id_lower}/{signal_category}/{signal_name_lower}

Examples:
  plantos/vf-demo/compressor-area/comp01-core/measurement/speed
  plantos/wtp-demo-01/raw-water-intake/hsp-101/measurement/flow_rate
  plantos/wtp-demo-01/distribution-area/transfer-outlet-quality-station-101/status/outlet_compliance_status
```

**Guarantees:**
- Deterministic: same identifiers → same topic. Always.
- Derived: computed from data model at runtime, never stored.
- Stable: identifiers don't change → topic doesn't change.

**MES subscription:**
```text
# All measurements from one plant:
plantos/vf-demo/+/+/measurement/#

# All status signals:
plantos/+/+/+/status/#

# Specific signal:
plantos/vf-demo/compressor-area/comp01-core/measurement/speed
```

## 3. Event Topics

```
Pattern: plantos/events/{event_type}

Event types:
  plantos/events/AssetStatusChanged
  plantos/events/AlarmRaised
  plantos/events/AlarmCleared
  plantos/events/SignalQualityChanged
  plantos/events/EdgeHeartbeatReceived
```

**MES subscription:**
```text
# All alarms:
plantos/events/AlarmRaised
plantos/events/AlarmCleared

# All system events:
plantos/events/#
```

## 4. Topic Ownership

- Namespace root `plantos/` is owned by PlantOS
- No other system publishes to `plantos/` namespace
- MES publishes to its own namespace (e.g., `mes/`)
- Cross-system communication is uni-directional: PlantOS → MES

## 5. Topic Naming Rules

- All lowercase
- Hyphens for multi-word IDs (plant-id, area-id)
- Underscores for signal names (flow_rate, suction_pressure)
- Forward slash as hierarchy separator
- No special characters except `-`, `_`, `/`
- No wildcards in published topics (only in subscriptions)
- No MQTT `$` prefix (reserved for broker)
