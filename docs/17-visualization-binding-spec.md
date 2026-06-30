# PlantOS Visualization Binding Specification

## 1. Purpose

This document defines how UI widgets, P&ID diagrams, one-line diagrams and GIS maps bind to PlantOS data.

The binding model is critical because it prevents hardcoded raw tags and keeps visualization independent from storage or protocol details.

## 2. Binding principle

Visual elements bind to semantic PlantOS objects:

```text
asset
signal
event
alarm
state
location
```

They must not bind directly to:

```text
PLC tag
OPC UA NodeId
Modbus register
TDengine table
MQTT raw topic
```

## 3. Binding object

Basic binding:

```json
{
  "binding_id": "bind-pump-101-pressure",
  "binding_type": "asset_signal",
  "asset_id": "PUMP-101",
  "signal_name": "discharge_pressure",
  "mode": "realtime",
  "display": {
    "format": "0.0",
    "unit": "bar"
  }
}
```

## 4. Binding types

### asset_signal

Used for current value or historical trend of a signal.

```json
{
  "binding_type": "asset_signal",
  "asset_id": "PUMP-101",
  "signal_name": "discharge_pressure"
}
```

### asset_state

Used for running/stopped/offline/maintenance state.

```json
{
  "binding_type": "asset_state",
  "asset_id": "PUMP-101",
  "state_key": "running_status"
}
```

### asset_alarm

Used for alarm/severity overlay.

```json
{
  "binding_type": "asset_alarm",
  "asset_id": "PUMP-101",
  "alarm_filter": {
    "state": "active"
  }
}
```

### asset_location

Used for GIS markers.

```json
{
  "binding_type": "asset_location",
  "asset_id": "PUMP-101"
}
```

### static

Used for non-dynamic labels or shapes.

## 5. Diagram element model

```json
{
  "element_id": "pump_101_symbol",
  "element_type": "symbol",
  "symbol_type": "pump",
  "asset_id": "PUMP-101",
  "bindings": {
    "state": {
      "binding_type": "asset_state",
      "asset_id": "PUMP-101",
      "state_key": "running_status"
    },
    "pressure_label": {
      "binding_type": "asset_signal",
      "asset_id": "PUMP-101",
      "signal_name": "discharge_pressure",
      "display": {
        "format": "0.0",
        "unit": "bar"
      }
    },
    "alarm_overlay": {
      "binding_type": "asset_alarm",
      "asset_id": "PUMP-101"
    }
  },
  "interactions": {
    "click": {
      "action": "open_asset_detail",
      "asset_id": "PUMP-101"
    },
    "hover": {
      "action": "show_asset_tooltip",
      "asset_id": "PUMP-101"
    }
  }
}
```

## 6. State rendering

State rendering must be centralized.

Recommended state values:

```text
normal
running
stopped
warning
alarm
trip
maintenance
offline
unknown
simulated
```

Diagram authors must not define custom colors per diagram unless mapped through the design token system.

## 7. Alarm rendering

Alarm rendering should use severity:

```text
low
medium
high
critical
```

Display behavior:

- icon/badge overlay,
- color outline,
- tooltip message,
- click to alarm detail.

Avoid excessive blinking in default UI. Blinking should be controlled by user preference or alarm severity policy.

## 8. GIS binding model

GIS marker:

```json
{
  "marker_id": "marker-pump-101",
  "asset_id": "PUMP-101",
  "binding_type": "asset_location",
  "status_binding": {
    "binding_type": "asset_alarm",
    "asset_id": "PUMP-101"
  },
  "interactions": {
    "click": {
      "action": "open_asset_detail",
      "asset_id": "PUMP-101"
    }
  }
}
```

## 9. Data adapter contract

Visualization runtime should call backend APIs through a data adapter.

Example adapter methods:

```text
getAsset(asset_id)
getAssetSignals(asset_id)
getCurrentValues(asset_id | signal_id)
getHistory(signal_id, from, to, interval)
getActiveAlarms(asset_id)
getAssetLocation(asset_id)
```

## 10. Realtime update strategy

MVP can use polling.

Future options:

- WebSocket from backend,
- Server-Sent Events,
- governed MQTT over WebSocket.

Do not let arbitrary widgets subscribe to arbitrary MQTT topics without governance.

## 11. Versioning

Every visualization definition must include:

```json
{
  "visualization_id": "demo-pid-001",
  "type": "pid",
  "version": "0.1.0",
  "owner": "PlantOS",
  "scope": "demo-plant"
}
```

## 12. MVP acceptance criteria

- A diagram element can bind to asset status.
- A value label can bind to an asset signal.
- An alarm overlay can bind to active alarms.
- A GIS marker can bind to asset location and alarm status.
- No visual element requires raw tag names.
- The binding model can work with real or simulated data.
