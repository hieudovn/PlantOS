# PlantOS Edge-Center Strategy

## 1. Objective

PlantOS must support both local plant resilience and centralized governance.

The Edge should keep plant-side data acquisition and critical local visibility working even when the Center is unavailable.

The Center should provide global governance, integration, advanced visualization, analytics and fleet management.

## 2. Responsibility split

| Capability | Edge | Center |
|---|---|---|
| Protocol connection | Primary | Configuration/governance |
| Local buffering | Primary | Monitoring |
| Store-and-forward | Primary | Receiver/validator |
| Local visualization | Lightweight | Full visualization |
| P&ID / one-line | Local subset | Full diagram management |
| GIS | Simple/local | Full layers and cross-site |
| Historian | Local cache / short retention | Main historian service |
| Rule engine | Simple/local | Full governed rules |
| Alarm | Local critical alarms | Central alarm management |
| UNS | Local namespace subset | Global namespace governance |
| CDM | Local subset | Global CDM registry |
| Edge management | Agent | Fleet manager |
| User management | Cached/minimal | Central identity |

## 3. Edge capabilities

Minimum Edge capabilities:

- protocol adapters,
- device service,
- local MQTT broker or local message bus,
- normalization,
- local quality check,
- local buffer,
- store-and-forward,
- health reporting,
- local lightweight historian/cache (**DuckDB** — see `docs/adr/ADR-0003-edge-local-tsdb-duckdb.md`),
- local P&ID / one-line viewer,
- local alarm list,
- sync status.

## 4. Center capabilities

Minimum Center capabilities:

- edge fleet registry,
- device registry,
- asset registry,
- signal registry,
- schema registry,
- UNS governance,
- CDM governance,
- central historian service,
- visualization management,
- alarm/rule management,
- integration API,
- identity and access control,
- license/tenant management,
- reporting and audit.

## 5. Edge Manager direction

PlantOS should not build a complex edge manager from scratch.

Recommended direction:

- use KubeEdge concepts for node/app lifecycle,
- use container deployment where practical,
- keep PlantOS Edge Agent responsible for product-specific telemetry and configuration,
- provide custom UI for edge fleet management.

Edge Manager must support:

- edge node registration,
- node health,
- app/service deployment,
- configuration push,
- certificate/secret management,
- log/metric inspection,
- OTA/update control,
- rollback,
- offline status.

## 6. Offline behavior

When Center connectivity is lost, Edge should continue:

- collecting data,
- buffering data,
- applying local critical rules,
- showing local status and diagrams,
- recording local alarms/events,
- reporting backlog when connection returns.

## 7. Synchronization principles

Sync must be:

- idempotent,
- resumable,
- auditable,
- bandwidth-aware,
- priority-aware,
- schema/version-aware.

## 8. Security principles

Edge-center communication must use:

- authenticated edge identity,
- encrypted transport,
- certificate/key rotation plan,
- scoped permissions,
- audit logging,
- no default trust from edge to center or center to edge.

## 9. MVP approach

Do not overbuild KubeEdge/Kubernetes on day one.

MVP should validate:

- edge data ingestion,
- local buffer,
- MQTT sync,
- edge status,
- central registry,
- simple deployment configuration,
- local visualization.

Production architecture can evolve toward KubeEdge/Kubernetes later.
