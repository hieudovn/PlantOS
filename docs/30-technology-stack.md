# PlantOS Technology Stack

## 1. Technology strategy

PlantOS should reuse mature open-source components for infrastructure-level capabilities and build proprietary/product-specific value in the operational model, user experience, governance, templates and integration layer.

The goal is not to build everything from scratch.

The goal is to assemble a controlled, brandable, industrial platform architecture.

## 2. Technology selection principles

Prefer technologies that are:

- open-source or source-available with acceptable license,
- widely adopted,
- container-friendly,
- API-first,
- replaceable,
- suitable for edge-center deployment,
- compatible with industrial data workloads,
- easy to integrate into a branded product UI.

Avoid technologies that:

- force the platform into their product model,
- make white-labeling difficult,
- create hard coupling,
- require expensive enterprise features for basic architecture,
- are too heavy for edge use cases.

## 3. Proposed stack overview

```text
Frontend:
  React + TypeScript + Vite/Next.js
  Tailwind CSS + shadcn/ui/Radix UI
  Storybook

Visualization:
  SVG + React
  Apache ECharts
  TanStack Table
  React Flow
  Leaflet / MapLibre GL
  Grafana embedded where useful

Edge:
  EdgeX Foundry patterns
  EMQX local broker
  lightweight local TSDB/cache
  container runtime
  KubeEdge-inspired edge management

Center:
  EMQX
  TDengine / VictoriaMetrics for time-series
  PostgreSQL for metadata
  Redis for cache
  Kafka / Redpanda for event streaming where needed
  MinIO for object storage
  Keycloak for identity

Backend:
  FastAPI / NestJS / Go services depending on team capability
  REST + WebSocket + optional gRPC

Deployment:
  Docker Compose for development/demo
  Kubernetes/KubeEdge for production direction
```

## 4. Open-source components to reference or reuse

### EdgeX Foundry

Role:

- reference architecture for edge device services,
- protocol adapter pattern,
- edge app service pattern,
- edge message bus pattern.

Usage strategy:

- do not blindly adopt the full stack,
- reuse architectural ideas and selected services where beneficial,
- keep PlantOS data model and UI independent.

### ThingsBoard

Role:

- reference for device management,
- dashboard concepts,
- rule engine concepts,
- edge-center synchronization ideas.

Usage strategy:

- do not clone or fork the UI,
- do not make PlantOS device-centric,
- use as benchmark/reference only unless a specific module is intentionally integrated.

### Node-RED

Role:

- reference for visual flow editing and connector ecosystem.

Usage strategy:

- do not expose unrestricted Node-RED-like freedom to normal users,
- use controlled low-code concepts,
- optionally support advanced/admin integration mode.

### EMQX

Role:

- MQTT broker for edge and center,
- UNS message backbone candidate,
- MQTT over WebSocket support for realtime UI where suitable.

### TDengine

Role:

- time-series and historian service candidate,
- high-volume telemetry storage,
- SQL-like query interface for operational data.

Usage strategy:

- use for measurement/time-series data,
- do not use for metadata, asset registry, user management or CDM registry,
- abstract behind PlantOS historian/query API.

### PostgreSQL

Role:

- metadata and relational model storage,
- asset registry,
- device registry,
- signal registry,
- schema registry,
- rule definitions,
- visualization definitions,
- integration configuration.

### Kafka / Redpanda

Role:

- optional central event streaming backbone,
- high-throughput event routing,
- integration with analytics and external systems.

Initial MVP may avoid Kafka if MQTT + API are sufficient.

### Grafana

Role:

- optional embedded dashboard or reference dashboard engine,
- not the main PlantOS UI shell.

Usage strategy:

- keep PlantOS product shell independent,
- use Grafana for advanced dashboard panels if useful,
- avoid making PlantOS a Grafana skin.

### Apache ECharts

Role:

- chart, trend, gauge and operational visualization widgets.

### React Flow

Role:

- topology, rule flow, integration flow and graph-like UI.

Not primary engine for detailed P&ID; SVG-first is preferred for P&ID and one-line diagrams.

### Leaflet / MapLibre GL

Role:

- GIS visualization.

Recommended split:

- Edge: Leaflet for lightweight map use.
- Center: MapLibre GL for richer vector layers and future scalability.

### Keycloak

Role:

- identity and access management,
- SSO,
- roles,
- multi-tenant access control.

### MinIO

Role:

- object storage,
- files, diagram assets, exported reports, attachments, simulation packages.

## 5. Build-versus-adopt rule

Build PlantOS-specific modules when they create product differentiation:

- UNS governance,
- CDM registry,
- asset/signal context engine,
- visualization binding runtime,
- industrial symbol library,
- product shell and UX,
- governed rule/flow designer,
- MES and Virtual Factory integration contracts,
- deployment templates and solution accelerators.

Adopt open-source for infrastructure:

- MQTT broker,
- time-series database,
- relational database,
- object storage,
- identity provider,
- chart rendering,
- map rendering,
- table rendering,
- container orchestration.

## 6. License strategy

Each selected open-source component must be reviewed for:

- license type,
- commercial redistribution constraints,
- SaaS restrictions,
- white-labeling constraints,
- enterprise feature gaps,
- security update responsibility.

No component should be embedded into PlantOS product packaging without license review.

## 7. Initial MVP technology recommendation

For the first implementation phase:

```text
Frontend:
  React + TypeScript + Vite
  Tailwind + shadcn/ui
  Storybook
  ECharts
  SVG runtime
  TanStack Table
  Leaflet

Backend:
  FastAPI or NestJS
  PostgreSQL
  EMQX
  TDengine
  Redis optional

Deployment:
  Docker Compose

Edge:
  lightweight collector simulator
  MQTT local broker or direct Center MQTT
  store-and-forward placeholder
```

The goal is to validate PlantOS data model, UNS, historian service, dynamic diagram and GIS visualization before overbuilding orchestration.
