# PlantOS Frontend and UX Design

## 1. Objective

PlantOS needs a custom branded product shell and a consistent user experience from the beginning.

The frontend must not become a collection of unrelated dashboards.

## 2. Recommended frontend stack

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui or Radix UI
TanStack Query
TanStack Table
Apache ECharts
SVG runtime
Leaflet / MapLibre later
Storybook
```

## 3. Product shell

The Product Shell is shared across Edge and Center UI.

Core shell elements:

- login placeholder,
- sidebar navigation,
- topbar,
- workspace title,
- tenant/site selector placeholder,
- notification area,
- user menu placeholder,
- command/search placeholder,
- theme and design tokens.

## 4. Navigation model

Navigation should be object-first, not technology-first.

Recommended MVP navigation:

```text
Overview
Assets
Signals
Historian
Diagrams
GIS Map
Alarms
Edge Fleet
Settings
```

Avoid navigation like:

```text
MQTT
TDengine
Kafka
OPC UA
Database
```

Technology details belong in admin/engineering views, not primary user navigation.

## 5. Role-based workspaces

Future roles:

```text
Operator
Engineer
Data Engineer
Administrator
Solution Architect
```

MVP can ignore full RBAC but should keep UI structure compatible with role-based navigation.

## 6. MVP screens

### Overview

Purpose:

- show platform status,
- asset count,
- active alarm count,
- edge status,
- recent data ingestion status.

### Assets

Purpose:

- list assets,
- filter by type/area,
- open asset detail.

Asset detail should show:

- metadata,
- related signals,
- current values,
- recent trend,
- alarms/events placeholder,
- location if available.

### Signals

Purpose:

- list signals,
- inspect asset binding,
- inspect unit, type, quality, UNS path.

### Historian

Purpose:

- select asset/signal,
- view time-series trend,
- query time range,
- display quality.

### Diagrams

Purpose:

- load demo P&ID,
- load demo one-line diagram,
- show dynamic values and status,
- click asset to open detail panel.

### GIS Map

Purpose:

- show asset markers,
- color marker by state/alarm,
- click marker to open asset detail.

### Alarms

MVP:

- show placeholder or simple generated alarms,
- filter by asset/severity/state.

### Edge Fleet

MVP:

- show simulator/edge node status,
- heartbeat timestamp,
- buffered message placeholder.

## 7. Design system principles

PlantOS design should be:

- industrial,
- calm,
- information-dense but readable,
- status-aware,
- accessible,
- dark-mode ready,
- consistent across Edge and Center.

## 8. Design tokens

Initial tokens:

```text
color.background
color.surface
color.border
color.text.primary
color.text.secondary
color.status.normal
color.status.running
color.status.warning
color.status.alarm
color.status.trip
color.status.offline
color.severity.low
color.severity.medium
color.severity.high
color.severity.critical
spacing.*
radius.*
font.*
shadow.*
```

## 9. UI data access rule

Frontend must access data only through PlantOS APIs.

Allowed:

```text
Frontend → API Client → PlantOS Backend API
```

Not allowed:

```text
Frontend → TDengine
Frontend → PostgreSQL
Frontend → MQTT topic directly for business state
```

Realtime UI may later use WebSocket/SSE from PlantOS backend, not raw broker subscriptions unless explicitly governed.

## 10. Frontend folder pattern

```text
frontend/src
├── app
├── components
│   ├── layout
│   ├── ui
│   └── industrial
├── features
│   ├── assets
│   ├── signals
│   ├── historian
│   ├── visualization
│   ├── gis
│   ├── alarms
│   └── edge-fleet
├── lib
│   ├── api
│   ├── types
│   └── utils
├── routes
└── styles
```

## 11. MVP frontend acceptance criteria

- Uses PlantOS branding placeholder.
- Uses shared layout shell.
- Can list assets from API.
- Can list signals from API.
- Can display current values from API.
- Can display historical trend from API.
- Can render demo SVG diagram with dynamic binding.
- Can render GIS map with asset markers.
- Does not directly access database or broker.
- Has clear route structure and feature boundaries.
