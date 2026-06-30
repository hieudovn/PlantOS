# PlantOS High-Level Roadmap

## Roadmap philosophy

PlantOS should grow from a controlled operational foundation, not from disconnected features.

The roadmap prioritizes:

1. architecture and governance first,
2. data model before dashboard,
3. edge-center foundation before advanced apps,
4. 2D visualization before 3D,
5. governed low-code before free-form no-code,
6. MES/Virtual Factory compatibility from the start.

## Phase 0: Foundation and alignment

Goal: establish the product foundation and prevent architecture drift.

Deliverables:

- product vision,
- project constitution,
- high-level architecture,
- data model foundation,
- technology stack selection,
- visualization runtime design,
- integration strategy,
- edge-center strategy,
- working rules for human and AI development,
- initial repo structure.

Status: started.

## Phase 1: MVP data backbone

Goal: prove PlantOS can collect, normalize, store and expose operational data.

Deliverables:

- basic backend service structure,
- PostgreSQL metadata database,
- EMQX MQTT broker,
- TDengine or selected TSDB,
- asset registry MVP,
- signal registry MVP,
- simple UNS path model,
- measurement ingestion API,
- current value API,
- historical query API,
- sample simulated plant data,
- Docker Compose development deployment.

Success criteria:

- simulated edge data can be ingested,
- measurements are stored in TSDB,
- assets and signals are registered in metadata DB,
- frontend can query current and historical signal values through PlantOS API.

## Phase 2: Edge runtime MVP

Goal: create first usable edge-center flow.

Deliverables:

- edge collector simulator,
- MQTT publish flow,
- local buffering prototype,
- edge node registry,
- edge health/status reporting,
- edge-to-center sync pattern,
- local lightweight status page,
- basic store-and-forward behavior.

Success criteria:

- edge node can publish data to center,
- center can monitor edge status,
- data loss is prevented during short network outage simulation,
- edge identity and configuration are tracked.

## Phase 3: Visualization MVP

Goal: deliver the first PlantOS user-facing product experience.

Deliverables:

- custom PlantOS product shell,
- design tokens,
- role-based navigation draft,
- asset tree,
- signal table,
- trend chart,
- alarm/event table,
- SVG dynamic diagram viewer,
- basic P&ID demo,
- basic one-line diagram demo,
- simple GIS map with asset markers,
- visualization binding model.

Success criteria:

- UI does not bind to raw tags,
- diagrams display dynamic status/value/alarm from asset-signal bindings,
- GIS can show asset location and alarm status,
- user can drill down from diagram/map to asset details and trends.

## Phase 4: Rule, alarm and governed low-code

Goal: add configurable operational intelligence without breaking architecture.

Deliverables:

- alarm rule model,
- threshold rule engine,
- calculated signal model,
- rule designer MVP,
- rule versioning,
- test mode,
- audit log,
- notification prototype,
- edge local rule subset.

Success criteria:

- users can define simple rules through controlled UI,
- rules are versioned and auditable,
- alarm events are generated from signals,
- rules cannot create unmanaged tags/topics or bypass registry.

## Phase 5: MES and Virtual Factory integration

Goal: make PlantOS the operational foundation for MES and simulation.

Deliverables:

- CDM-aligned event contracts,
- equipment state event API,
- downtime event API,
- quality measurement event API,
- production context API,
- Virtual Factory simulation connector,
- MES integration sample,
- shared asset/signal/event model validation.

Success criteria:

- Virtual Factory can publish simulated data through PlantOS,
- MES can consume PlantOS equipment/status/event data,
- production context can enrich operational data,
- same dashboard works with real and simulated data.

## Phase 6: Industrial hardening

Goal: prepare for pilot or customer-facing demo.

Deliverables:

- authentication and authorization,
- user and role management,
- tenant/site management,
- license model draft,
- deployment templates,
- backup/restore strategy,
- logging/observability,
- API documentation,
- security baseline,
- performance baseline.

Success criteria:

- platform can run as demo/pilot product,
- core services are observable,
- access is role-controlled,
- deployment can be reproduced reliably.

## Phase 7: Productization and vertical templates

Goal: turn PlantOS into a reusable solution platform.

Deliverables:

- branded UI refinement,
- packaged installer/deployment kit,
- solution templates by industry,
- pump/compressor/energy/electrical templates,
- standard symbol library,
- report templates,
- connector SDK,
- widget SDK,
- documentation portal.

Potential vertical templates:

- smart factory line monitoring,
- energy monitoring,
- substation monitoring,
- pump/compressor asset health,
- F&B production line demo,
- power plant operational monitoring,
- virtual factory demo.

## Backlog themes

Future areas:

- advanced analytics,
- AI assistant integration,
- semantic query,
- event correlation,
- anomaly detection,
- AHM/APM modules,
- plugin marketplace,
- 3D digital twin viewer,
- multi-site enterprise management.

## Near-term next actions

Recommended next actions after foundation docs:

1. Create initial repo structure.
2. Add ADR template.
3. Decide MVP implementation stack: FastAPI vs NestJS vs Go.
4. Create Docker Compose skeleton: PostgreSQL, EMQX, TSDB.
5. Implement asset/signal registry MVP.
6. Implement measurement ingestion and query APIs.
7. Build first simulated data publisher.
8. Build first frontend shell and trend view.
9. Build first SVG dynamic diagram demo.
10. Connect Virtual Factory simulation later using the same event/data model.
