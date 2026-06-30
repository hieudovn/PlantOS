# PlantOS Phase 0 Closure Checklist

## 1. Phase 0 objective

Phase 0 closes when PlantOS has enough foundation, design and governance documentation to start AI-assisted implementation without losing architectural control.

## 2. Phase 0 status

```text
Status: CLOSED / READY FOR PHASE 1
Decision record: docs/adr/ADR-0001-mvp-technology-decisions.md
Confirmed by Product Owner / Solution Architect: 2026-06-30
```

## 3. Documents completed

Phase 0 foundation documents:

- [x] `README.md`
- [x] `docs/00-product-vision.md`
- [x] `docs/01-project-constitution.md`
- [x] `docs/10-high-level-architecture.md`
- [x] `docs/11-repository-structure.md`
- [x] `docs/12-mvp-scope.md`
- [x] `docs/13-backend-service-design.md`
- [x] `docs/14-api-contract-mvp.md`
- [x] `docs/15-storage-and-historian-design.md`
- [x] `docs/16-frontend-ux-design.md`
- [x] `docs/17-visualization-binding-spec.md`
- [x] `docs/18-edge-simulator-design.md`
- [x] `docs/19-deployment-design.md`
- [x] `docs/20-data-model.md`
- [x] `docs/30-technology-stack.md`
- [x] `docs/40-visualization-runtime.md`
- [x] `docs/50-integration-strategy.md`
- [x] `docs/60-edge-center-strategy.md`
- [x] `docs/80-working-rules.md`
- [x] `docs/90-roadmap.md`
- [x] `docs/adr/ADR-0000-template.md`
- [x] `docs/adr/ADR-0001-mvp-technology-decisions.md`
- [x] `.github/copilot-instructions.md`

## 4. Architecture principles locked

- [x] PlantOS is an Industrial Operational Platform, not only IIoT dashboard.
- [x] PlantOS has built-in time-series/historian capability but is not only a Historian.
- [x] PlantOS is not SCADA, MES, ERP or CMMS/EAM.
- [x] PlantOS is Edge-Center hybrid.
- [x] PlantOS is UNS-native and CDM-native.
- [x] PlantOS uses asset/signal/event binding, not raw tag binding.
- [x] UI must not query database or broker directly.
- [x] Visualization must use a governed binding runtime.
- [x] Low-code/rule/flow must be governed, versioned and auditable.
- [x] Virtual Factory must use the same data model as real plant data.

## 5. MVP scope locked

MVP includes:

- [x] Backend API skeleton.
- [x] PostgreSQL metadata store.
- [x] TSDB/historian abstraction.
- [x] Asset Registry.
- [x] Signal Registry.
- [x] Measurement ingestion.
- [x] Current value query.
- [x] Historical query.
- [x] Basic UNS path generation.
- [x] Edge simulator.
- [x] Frontend product shell.
- [x] Asset/signal views.
- [x] Trend chart.
- [x] Dynamic SVG diagram demo.
- [x] GIS asset marker demo.

MVP excludes:

- [x] Full MES.
- [x] Full SCADA.
- [x] Full no-code platform.
- [x] 3D digital twin.
- [x] Enterprise SSO.
- [x] Advanced APM analytics.
- [x] Production-grade edge manager.

## 6. MVP decisions accepted

The Product Owner / Solution Architect confirmed the following decisions on 2026-06-30. Details are recorded in `docs/adr/ADR-0001-mvp-technology-decisions.md`.

### Decision 1: Backend framework

Accepted:

```text
FastAPI + Python
```

### Decision 2: First TSDB

Accepted:

```text
TDengine
```

### Decision 3: First ingestion path

Accepted:

```text
HTTP ingestion first, MQTT path second
```

### Decision 4: Frontend stack

Accepted:

```text
React + TypeScript + Vite + Tailwind + shadcn/ui + ECharts
```

### Decision 5: MVP data type scope

Accepted:

```text
numeric + boolean-like signals first
```

### Decision 6: Demo plant scenario

Accepted:

```text
Process line + electrical subsystem
```

Assets:

- PUMP-101,
- MOTOR-101,
- TANK-101,
- VALVE-101,
- TRANSFORMER-01,
- FEEDER-01,
- BREAKER-01.

## 7. Phase 1 recommended task sequence

Assign AI/Codex tasks in this sequence:

1. Create repository structure.
2. Add Docker Compose skeleton.
3. Add backend FastAPI skeleton.
4. Add PostgreSQL models and migrations.
5. Add TDengine historian abstraction.
6. Implement Asset Registry API.
7. Implement Signal Registry API.
8. Implement Measurement Ingestion API.
9. Implement Current Value and History Query APIs.
10. Add demo plant seed data.
11. Add edge simulator.
12. Add frontend Product Shell.
13. Add Assets and Signals pages.
14. Add Trend Chart page.
15. Add SVG dynamic diagram demo.
16. Add GIS map demo.
17. Add README run instructions.
18. Validate MVP acceptance criteria.

## 8. Go / No-Go checklist

Before coding starts:

- [x] Product Owner confirms pending decisions.
- [x] Codex/AI task prompt references constitution and working rules.
- [x] Phase 1 tasks are assigned sequentially.
- [x] AI is instructed to update docs when architecture changes.
- [x] Any major deviation must create an ADR.

```text
Go decision: YES — Phase 1 implementation may start.
```

## 9. Recommended Phase 1 master prompt

```text
You are working on PlantOS.

Before making changes, read:
- README.md
- docs/01-project-constitution.md
- docs/10-high-level-architecture.md
- docs/11-repository-structure.md
- docs/12-mvp-scope.md
- docs/13-backend-service-design.md
- docs/14-api-contract-mvp.md
- docs/15-storage-and-historian-design.md
- docs/16-frontend-ux-design.md
- docs/17-visualization-binding-spec.md
- docs/18-edge-simulator-design.md
- docs/19-deployment-design.md
- docs/80-working-rules.md
- docs/99-phase-0-closure-checklist.md
- docs/adr/ADR-0001-mvp-technology-decisions.md

Your task:
[insert specific Phase 1 task]

Constraints:
- Do not bypass UNS/CDM.
- Do not bind UI directly to raw tags.
- Do not let UI query TDengine, PostgreSQL, MQTT or Kafka directly.
- Keep Edge and Center responsibilities separate.
- Follow the MVP API contract.
- Prefer simple working implementation over over-engineering.
- Add tests or validation steps.
- Update documentation if the implementation changes design.
- Any major deviation must create an ADR.

Expected output:
- plan,
- changed files,
- implementation,
- validation steps,
- notes/risks.
```
