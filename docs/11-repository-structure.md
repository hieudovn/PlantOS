# PlantOS Repository Structure Design

## 1. Purpose

This document defines the target repository structure for the first implementation phase of PlantOS.

The structure must make module boundaries clear from the start so that AI coding assistants do not create random folders, duplicate concepts or mix Edge, Center and UI responsibilities.

## 2. Target structure

```text
PlantOS
├── README.md
├── docs/
│   ├── adr/
│   ├── api/
│   ├── architecture/
│   ├── data-model/
│   └── modules/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── modules/
│   │   │   ├── assets/
│   │   │   ├── signals/
│   │   │   ├── measurements/
│   │   │   ├── historian/
│   │   │   ├── uns/
│   │   │   ├── alarms/
│   │   │   └── edge_nodes/
│   │   └── main.py
│   ├── tests/
│   ├── migrations/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── assets/
│   │   │   ├── signals/
│   │   │   ├── historian/
│   │   │   ├── visualization/
│   │   │   ├── alarms/
│   │   │   └── edge-fleet/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── styles/
│   ├── storybook/
│   ├── package.json
│   └── Dockerfile
│
├── edge/
│   ├── simulator/
│   ├── agent/
│   ├── collectors/
│   └── README.md
│
├── deployment/
│   ├── docker-compose.yml
│   ├── env.example
│   └── init/
│
├── examples/
│   ├── demo-plant/
│   ├── diagrams/
│   ├── gis/
│   └── sample-data/
│
├── packages/
│   ├── shared-types/
│   └── visualization-sdk/
│
└── .github/
    └── copilot-instructions.md
```

## 3. Folder responsibilities

### `backend/`

Owns PlantOS Center APIs, metadata management, ingestion services, historical query service, registry services and integration endpoints.

Backend must not contain frontend rendering logic.

### `frontend/`

Owns Product Shell, UI components, visualization runtime, dashboards, diagrams, GIS views and user workflows.

Frontend must not directly query PostgreSQL, TDengine, MQTT or Kafka.

### `edge/`

Owns Edge simulator, future Edge Agent, protocol collector prototypes and local edge runtime components.

Edge modules must be able to run independently from the Center for local buffering and simulation tests.

### `deployment/`

Owns reproducible local deployment and later production deployment templates.

MVP starts with Docker Compose.

### `examples/`

Owns demo plant data, sample diagrams, GIS files and synthetic signals.

Examples must follow the official PlantOS data model.

### `packages/`

Optional shared libraries for types and visualization SDK.

Do not use this folder as a dumping ground. Only create shared packages when at least two major modules need the same contract.

## 4. Naming rules

Use domain names consistently:

```text
asset
signal
measurement
event
alarm
edge_node
uns_path
cdm_object
visualization_binding
```

Avoid synonyms unless documented:

```text
tag vs signal
machine vs asset
device vs gateway
metric vs measurement
```

## 5. Implementation sequence

Recommended sequence for Codex/AI implementation:

1. Create repository structure.
2. Add Docker Compose skeleton.
3. Add backend skeleton.
4. Add PostgreSQL connection and migrations.
5. Add TDengine connection abstraction.
6. Add Asset Registry API.
7. Add Signal Registry API.
8. Add Measurement Ingestion API.
9. Add Historical Query API.
10. Add simulator publisher.
11. Add frontend product shell.
12. Add asset/signal table views.
13. Add trend chart.
14. Add first SVG diagram demo.
15. Add GIS demo.

## 6. Guardrails for AI assistants

AI assistants must not:

- create new root-level folders without reason,
- mix Edge and Center code,
- place API types only inside frontend,
- create duplicate data model definitions,
- build UI directly against storage,
- introduce heavy frameworks before Phase 1 validates the data backbone.
