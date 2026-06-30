# ADR-0001: MVP Technology Decisions

## Status

Accepted

## Date

2026-06-30

## Context

PlantOS Phase 0 documentation is complete enough to start Phase 1 implementation. Before assigning AI/Codex coding tasks, the Product Owner confirmed the initial technology and MVP scope decisions proposed in `docs/99-phase-0-closure-checklist.md`.

This ADR records those decisions so Phase 1 can proceed without repeatedly reopening the same choices.

## Decision

The following decisions are accepted for PlantOS MVP.

### 1. Backend framework

Use:

```text
FastAPI + Python
```

Rationale:

- fast API development,
- strong Pydantic schema support,
- good fit for data/AI/simulator workflows,
- simple for MVP iteration,
- suitable for AI-assisted implementation.

### 2. TSDB / Historian backend

Use:

```text
TDengine
```

Rationale:

- suitable candidate for industrial time-series workload,
- good fit for PlantOS built-in operational historian capability,
- SQL-like query model,
- aligns with the open-source-based product strategy.

The implementation must still hide TDengine behind PlantOS Historian Service abstraction.

### 3. First ingestion path

Use:

```text
HTTP ingestion first, MQTT path second
```

Rationale:

- faster MVP validation,
- easier debugging,
- avoids building MQTT subscriber before core API/data model is proven.

MQTT/EMQX remains part of the architecture and should be added after HTTP ingestion is stable.

### 4. Frontend stack

Use:

```text
React + TypeScript + Vite + Tailwind CSS + shadcn/ui + ECharts
```

Rationale:

- fast frontend development,
- strong component ecosystem,
- easy branding/custom UI shell,
- ECharts is suitable for trend, gauge and operational chart widgets.

### 5. MVP data type scope

Use:

```text
numeric + boolean-like signals first
```

Rationale:

- enough for trend, diagram, GIS and alarm demo,
- avoids early complexity of mixed-type historian storage,
- keeps MVP focused.

### 6. Demo plant scenario

Use:

```text
Process line + electrical subsystem
```

Initial demo assets:

- PUMP-101,
- MOTOR-101,
- TANK-101,
- VALVE-101,
- TRANSFORMER-01,
- FEEDER-01,
- BREAKER-01.

Rationale:

- covers both P&ID and one-line diagram visualization,
- supports process and electrical monitoring demos,
- provides enough variety for Asset/Signal/Historian/GIS validation.

## Alternatives considered

### Backend: NestJS + TypeScript

Pros:

- same language as frontend,
- strong enterprise backend structure.

Cons:

- less direct fit for data/simulation/AI workflows,
- potentially slower MVP iteration for this project context.

### TSDB: VictoriaMetrics

Pros:

- mature metrics storage,
- strong Prometheus ecosystem.

Cons:

- less industrial historian-oriented than TDengine for this MVP direction.

### Ingestion: MQTT-first

Pros:

- closer to IIoT event architecture.

Cons:

- more moving parts before API/data model validation,
- harder to debug in the first implementation cycle.

## Consequences

Positive consequences:

- Phase 1 can start with a clear stack.
- AI/Codex tasks can be more deterministic.
- MVP stays focused on proving data backbone and visualization binding.
- Later MQTT, rule engine and edge manager work can build on a stable API and data model.

Trade-offs:

- HTTP-first ingestion is not the final industrial architecture.
- Numeric/boolean MVP means string/event payload handling is deferred.
- TDengine schema needs careful abstraction to avoid future lock-in.

## Impacted areas

- Backend
- Frontend
- Historian Service
- Edge Simulator
- Deployment
- API Contract
- Roadmap

## Review date

After Phase 1 MVP validation.

## Notes

Any major deviation from these accepted decisions requires a new ADR or a superseding ADR.
