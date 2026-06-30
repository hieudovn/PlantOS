# PlantOS Deployment Design

## 1. Purpose

This document defines the initial deployment approach for PlantOS MVP.

The goal is to make the platform easy to run locally for development, demo and AI-assisted coding.

## 2. MVP deployment profile

Use Docker Compose for MVP.

Initial services:

```text
postgres
emqx
tdengine
backend
frontend
edge-simulator
```

Optional later:

```text
redis
minio
grafana
keycloak
```

## 3. Docker Compose target

```text
deployment/docker-compose.yml
```

Expected commands:

```bash
docker compose -f deployment/docker-compose.yml up -d
```

or from repo root later:

```bash
docker compose up -d
```

## 4. Service responsibilities

### PostgreSQL

Stores metadata:

- assets,
- signals,
- devices,
- edge nodes,
- UNS paths,
- alarm metadata,
- visualization bindings.

### EMQX

MVP role:

- prepare MQTT backbone,
- support future simulator/edge publishing,
- support UNS message flow.

HTTP ingestion can be implemented first if faster.

### TDengine

Stores measurement time-series data.

Backend must access TDengine through Historian Service abstraction.

### Backend

Provides PlantOS API.

### Frontend

Provides PlantOS product shell and MVP UI.

### Edge Simulator

Generates demo plant telemetry.

## 5. Environment configuration

Create:

```text
deployment/env.example
```

Suggested variables:

```text
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=plantos
POSTGRES_USER=plantos
POSTGRES_PASSWORD=plantos

TDENGINE_HOST=tdengine
TDENGINE_PORT=6041
TDENGINE_DATABASE=plantos_ts

EMQX_HOST=emqx
EMQX_MQTT_PORT=1883
EMQX_DASHBOARD_PORT=18083

BACKEND_PORT=8000
FRONTEND_PORT=5173
```

## 6. Development workflow

Recommended first workflow:

1. Start infrastructure services.
2. Run database migrations.
3. Load demo plant metadata.
4. Start backend.
5. Start frontend.
6. Start simulator.
7. Verify data ingestion and UI visualization.

## 7. Seed data

Seed data should create:

- DEMO-PLANT,
- PROCESS-AREA,
- ELECTRICAL-AREA,
- initial assets,
- initial signals,
- initial visualization bindings,
- optional sample alarms.

Recommended paths:

```text
examples/demo-plant/demo-plant.yaml
examples/demo-plant/seed.sql or seed.py
```

## 8. Health checks

Each service should expose or support a health check:

```text
backend: /health
frontend: HTTP root
postgres: pg_isready
tdengine: HTTP/connection check
emqx: dashboard/API or TCP port
edge-simulator: heartbeat to backend
```

## 9. Future deployment profiles

### Plant local deployment

Center runs on plant server.
Edge nodes run near production areas.

### Hybrid deployment

Center runs on cloud/private datacenter.
Edge nodes remain on site.

### Multi-site deployment

One Center governs multiple plants/sites.
Requires tenant/site isolation.

### Kubernetes/KubeEdge deployment

Future production direction after MVP stabilizes.

## 10. Deployment rules

- MVP must be runnable by a developer from documentation.
- Infrastructure credentials must not be hardcoded in source code.
- Docker Compose must not become the only production architecture.
- Deployment must support simulation first.
- Deployment must preserve service boundaries.

## 11. MVP acceptance criteria

- `docker compose up` starts infrastructure.
- Backend connects to PostgreSQL and TSDB.
- Frontend connects to backend.
- Simulator can publish data.
- Seed/demo data can be loaded.
- Run instructions are documented.
