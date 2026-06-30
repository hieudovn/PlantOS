# PlantOS High-Level Architecture

## 1. Architecture overview

PlantOS follows an edge-center architecture.

```text
PLC / SCADA / OPC UA / Modbus / MQTT / REST
        ↓
PlantOS Edge Runtime
        ↓
Local Buffer / Local UNS / Local Visualization
        ↓
Secure Sync / Message Bus
        ↓
PlantOS Center
        ↓
UNS + CDM + Semantic Layer + Historian + Visualization + APIs
        ↓
MES / Virtual Factory / AHM / Analytics / AI / External Systems
```

## 2. Main layers

```text
PlantOS
├── Edge Layer
├── Communication Layer
├── Center Platform Layer
├── Data Foundation Layer
├── Application Runtime Layer
├── Visualization Layer
├── Integration Layer
└── Governance Layer
```

## 3. Edge Layer

The Edge Layer runs near plant equipment and automation systems.

Main responsibilities:

- connect to industrial protocols,
- collect telemetry and events,
- normalize data,
- validate quality,
- buffer data locally,
- publish local UNS messages,
- provide local lightweight visualization,
- execute limited local rules,
- synchronize to Center when connectivity is available.

Potential components:

- EdgeX-inspired device services,
- EMQX local broker,
- lightweight local time-series storage,
- store-and-forward service,
- edge health agent,
- edge configuration agent,
- local SVG diagram viewer,
- local trend/alarm view.

## 4. Communication Layer

The Communication Layer connects Edge and Center.

Main responsibilities:

- MQTT / MQTT over WebSocket,
- HTTPS APIs,
- event streaming,
- secure tunnel or reverse connection where required,
- data compression and retry,
- store-and-forward synchronization,
- command and configuration delivery.

Initial direction:

- EMQX for MQTT broker,
- optional Kafka or Redpanda for central event streaming,
- HTTP/gRPC APIs for management and query services.

## 5. Center Platform Layer

The Center Platform is the governed central runtime.

Main services:

- Identity and access management,
- Tenant/site management,
- Edge fleet management,
- Device registry,
- Asset registry,
- Signal registry,
- Schema registry,
- Time-Series & Historian Service,
- UNS service,
- CDM service,
- Semantic Context service,
- Rule engine,
- Alarm engine,
- Notification service,
- Visualization runtime,
- API gateway,
- Integration services.

## 6. Data Foundation Layer

The Data Foundation is the most strategic layer of PlantOS.

It turns raw signals into contextualized, application-ready operational data.

```text
Raw Signal
  ↓
Normalized Signal
  ↓
Quality-checked Measurement
  ↓
Asset-bound Signal
  ↓
UNS Message
  ↓
CDM Object / Event
  ↓
Semantic Context
  ↓
Application Data Product
```

Key components:

- Unified Namespace,
- Canonical Data Model,
- Asset model,
- Signal model,
- Event model,
- Alarm model,
- Schema registry,
- Context engine,
- Data product definitions.

## 7. Time-Series & Historian Service

PlantOS includes a built-in time-series and historian-capable service.

It should support:

- high-frequency telemetry storage,
- timestamp, value and quality,
- compression/retention policies,
- historical queries,
- trend data APIs,
- integration with visualization widgets,
- optional replacement or coexistence with PI, Canary, IP.21 or other enterprise historians.

PlantOS should not be positioned only as a Historian, but it can act as an operational historian for plants without an existing historian.

## 8. Visualization Layer

Initial visualization scope focuses on 2D industrial views, not 3D.

Main views:

- Dynamic P&ID diagram,
- Electrical one-line diagram,
- GIS map,
- trend chart,
- gauge/KPI card,
- alarm table,
- event table,
- asset status panel.

Architecture rule:

```text
Widget → Visualization Data Adapter → PlantOS API → Data Foundation / Historian
```

Widgets must not directly query database tables, MQTT topics or raw tag names.

## 9. Rule and Flow Layer

PlantOS should support governed low-code configuration.

Edge rules:

- lightweight,
- template-based,
- local threshold,
- quality checks,
- local routing,
- local store-and-forward control.

Center rules:

- alarm rules,
- calculated signals,
- event enrichment,
- notification,
- integration triggers,
- routing,
- data quality and contextualization.

Rules must be versioned, scoped, tested and auditable.

## 10. Integration Layer

PlantOS integrates with:

- MES,
- Virtual Factory,
- SCADA,
- Historian,
- CMMS/EAM,
- ERP,
- AI assistants,
- BI/analytics tools,
- external APIs.

Integration must prefer CDM-aligned APIs and event contracts.

## 11. Deployment model

Initial deployment profiles:

### Single-node demo

- Center and Edge in one docker compose stack.
- Used for development, demo and simulation.

### Plant local deployment

- Center runs on plant server.
- Edge nodes run near equipment, line or area.

### Hybrid cloud deployment

- Edge runs on site.
- Center runs on private cloud / datacenter.

### Multi-site deployment

- Multiple plants connect to one Center.
- Site isolation and tenant governance are required.
