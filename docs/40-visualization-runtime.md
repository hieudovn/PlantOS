# PlantOS Visualization Runtime

## 1. Visualization objective

PlantOS needs a lightweight but governed visualization layer for industrial operations.

The first phase focuses on 2D dynamic visualization, not 3D.

Priority visualization types:

- dynamic P&ID diagram,
- electrical one-line diagram,
- GIS map,
- trend chart,
- KPI/gauge card,
- alarm table,
- event table,
- asset detail panel.

3D digital twin visualization is a future extension, not an MVP requirement.

## 2. Core principle

Visualization must be bound to PlantOS semantic objects, not raw tags.

Bad:

```text
SVG element → PLC_TAG_001
```

Good:

```text
SVG element → asset_id + signal_name + state/alarm binding
```

## 3. Visualization architecture

```text
UNS / CDM / Asset Registry / Signal Registry / Historian
        ↓
Visualization Data Adapter
        ↓
Binding Runtime
        ↓
Widget Runtime
        ↓
P&ID / One-line / GIS / Trend / Alarm Table
```

## 4. Runtime components

```text
Visualization Runtime
├── Product UI Shell
├── Widget Registry
├── Binding Runtime
├── State Renderer
├── Realtime Data Adapter
├── Historical Query Adapter
├── Permission Filter
├── Theme / Branding Tokens
├── SVG Diagram Runtime
├── GIS Layer Runtime
└── Interaction Runtime
```

## 5. Dynamic diagram scope

### P&ID Viewer

Used for process equipment and flows:

- pump,
- valve,
- tank,
- heat exchanger,
- compressor,
- motor,
- pipeline,
- instrument,
- control loop,
- process value label.

### One-line Diagram Viewer

Used for electrical systems:

- feeder,
- breaker,
- transformer,
- busbar,
- switch,
- relay,
- meter,
- power flow,
- breaker status,
- alarm state.

## 6. SVG-first design

P&ID and one-line diagrams should use SVG-first rendering.

Reasons:

- lightweight for Edge,
- easy to render in browser,
- easy to change color/state dynamically,
- easy to attach click/hover interactions,
- easy zoom/pan,
- suitable for industrial symbols,
- can be stored as files or JSON definitions.

## 7. Diagram object model

Each visual object should have four layers:

```text
Shape Layer      static geometry / SVG path / symbol
Binding Layer    asset, signal, alarm or event reference
State Layer      normal, running, stopped, warning, alarm, trip, offline
Interaction      hover, click, drilldown, action, navigation
```

Example:

```json
{
  "element_id": "pump_101",
  "symbol_type": "pump",
  "asset_id": "PUMP-101",
  "bindings": {
    "status": "state.running",
    "value": "measurement.discharge_pressure",
    "alarm": "alarm.high_pressure"
  },
  "interactions": {
    "click": "open_asset_detail",
    "hover": "show_tooltip"
  }
}
```

## 8. Symbol state model

Initial state set:

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

State rendering should be centralized.

Individual diagrams should not define their own alarm colors or status logic.

## 9. GIS visualization

GIS is required for:

- asset location,
- site map,
- distributed equipment,
- pipeline/route/feeder visualization,
- alarm by location,
- regional overview,
- smart utility and energy monitoring use cases.

Recommended libraries:

- Edge: Leaflet,
- Center: MapLibre GL.

GIS layers:

```text
Base map
Site boundary
Area / zone
Asset marker
Alarm layer
Route / pipeline / feeder layer
Heatmap layer
Realtime status layer
```

## 10. Chart, trend and table widgets

Recommended libraries:

- Apache ECharts for trends, gauges, KPI and charts,
- TanStack Table for tables,
- optional Grafana embedded for advanced dashboards.

Initial widgets:

```text
KPI Card
Current Value
Trend Chart
Multi-signal Trend
Gauge
Alarm Table
Event Table
Asset Status Card
Signal List
Map Marker
Diagram Value Label
```

## 11. Edge versus Center visualization

### Edge visualization

Edge visualization must be lightweight and local-resilient.

Required:

- local status page,
- local P&ID / one-line viewer,
- local trend for recent data,
- local alarm list,
- edge connectivity status,
- store-and-forward status.

Avoid:

- complex dashboard builder,
- heavy GIS layers,
- 3D,
- cross-site analytics.

### Center visualization

Center visualization can be richer.

Required:

- dashboard builder,
- cross-site/plant views,
- GIS map with layers,
- dynamic diagrams,
- trend analysis,
- alarm/event management,
- user/role-based workspaces,
- integration views.

## 12. Visualization governance

Every visualization definition must have:

- id,
- name,
- type,
- owner,
- version,
- scope,
- asset context,
- data bindings,
- permissions,
- change history.

## 13. Future 3D extension

3D should be added later through a separate Digital Twin Viewer.

Possible technologies:

- Three.js,
- Babylon.js,
- CesiumJS for geospatial 3D.

3D must reuse the same Asset/CDM binding model instead of creating a separate data model.
