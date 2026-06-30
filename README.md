# PlantOS

**PlantOS** is an open, composable Industrial Operational Platform for modern plants.

It provides the foundation for edge data acquisition, operational time-series storage, Unified Namespace (UNS), Canonical Data Model (CDM), semantic context, visualization runtime, rule/alarm services, and integration with applications such as MES, Virtual Factory, AHM/APM, AI assistants, and industrial analytics.

PlantOS is not intended to be only an IIoT dashboard, a pure Historian, a SCADA replacement, a MES, or a no-code tool. It is a plant-level operational data and runtime foundation.

## Core positioning

```text
PlantOS = Edge + Operational Data Foundation + UNS + CDM + Visualization + Governance
```

## Initial product modules

```text
PlantOS
├── Edge Runtime
├── Center Platform
├── Time-Series & Historian Service
├── Unified Namespace
├── Canonical Data Model
├── Asset & Signal Registry
├── Semantic Context Layer
├── Rule & Alarm Engine
├── Visualization Runtime
│   ├── Dynamic P&ID
│   ├── One-line Diagram
│   └── GIS Map
├── Edge Manager
├── API Gateway
└── Integration Layer
```

## Recommended first reading

1. [`docs/00-product-vision.md`](docs/00-product-vision.md)
2. [`docs/01-project-constitution.md`](docs/01-project-constitution.md)
3. [`docs/10-high-level-architecture.md`](docs/10-high-level-architecture.md)
4. [`docs/20-data-model.md`](docs/20-data-model.md)
5. [`docs/30-technology-stack.md`](docs/30-technology-stack.md)
6. [`docs/40-visualization-runtime.md`](docs/40-visualization-runtime.md)
7. [`docs/50-integration-strategy.md`](docs/50-integration-strategy.md)
8. [`docs/80-working-rules.md`](docs/80-working-rules.md)
9. [`docs/90-roadmap.md`](docs/90-roadmap.md)

## Design philosophy

PlantOS should be:

- **Open-source based**, but not a simple fork of ThingsBoard, Node-RED, Grafana, or EdgeX.
- **Industrial-first**, using plant, area, asset, device, signal, event, alarm, and workflow as primary concepts.
- **UNS-native**, where data is organized through an enterprise namespace instead of isolated device dashboards.
- **CDM-native**, so MES, Virtual Factory, AI and analytics can share common operational objects.
- **Edge-center hybrid**, supporting local resilience and central governance.
- **Governed low-code**, allowing configurable flows and rules without breaking data architecture.
- **Brandable and productizable**, with a custom UI shell, design system, license model, and Avenue product identity.

## Repository purpose

This repository is the source of truth for PlantOS product architecture, technical design, rules, roadmap, and later implementation.

Other repositories such as MES, Virtual Factory, and analytics applications should align with PlantOS instead of redefining their own operational data foundation.

## Quick Start

### Prerequisites

- Docker Desktop 4.30+
- Python 3.11+
- Node.js 20+

### 1. Start Infrastructure

```bash
docker compose -f deployment/docker-compose.yml up -d postgres tdengine
```

Wait for healthy (~20s):
```bash
docker ps --filter "name=plantos"
```

### 2. Setup Backend

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_demo_plant.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:
```bash
curl http://localhost:8000/health
# → {"status":"healthy","version":"0.1.0"}
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Run Simulator

```bash
cd edge/simulator
pip install -r requirements.txt
python simulator.py --config ../../examples/demo-plant/demo-plant.yaml
```

### 5. Run Tests

```bash
cd backend
python -m pytest tests/ -v
# Expected: 44 passed
```

## Architecture

- **Backend**: FastAPI + PostgreSQL (metadata) + TDengine (time-series)
- **Frontend**: React + Vite + Tailwind CSS + shadcn/ui
- **Edge**: Python simulator → HTTP ingestion
- **API**: REST `/api/v1/*`, all data through API (no direct DB access)
- **Principles**: UNS-native, CDM-native, Asset/Signal binding

## MVP Features

- Asset & Signal Registry (CRUD)
- Measurement Ingestion & Query
- Historian (TDengine-backed)
- Dynamic SVG P&ID Diagram
- GIS Map with Asset Markers
- Trend Chart (multi-signal, ECharts)
- Edge Simulator (15 signals, 4 scenarios)

## Phase 2 Features

- **Edge Agent** — DuckDB local buffer, MQTT publisher, store-and-forward sync
- **Edge Fleet UI** — Real-time node status, heartbeat monitoring
- **Asset Tree View** — UNS hierarchy navigation (Plant → Area → Asset)
- **WebSocket Real-time** — Live data push for Asset Detail + Diagrams
- **UX Polish** — Chart state persistence, tab rename, chart type selector
- **Diagram Enhancement** — Click element → asset detail, state-driven colors, hover tooltip

## Phase 4 Features

- **Alarm Rule Engine** — Threshold-based alarm rules, form-based editor
- **Alarm State Machine** — Active → Acknowledged → Cleared lifecycle
- **Calculated Signals** — Virtual signals via formula (e.g., power = V × I)
- **Notification Service** — Webhook dispatch for alarm events

## Known Limitations (Phase 2 Backlog)

| # | Issue | Severity | Plan |
|---|---|---|---|
| 1 | **Historian state lost on navigation** — chart setups (signals, time range, panels) reset khi chuyển menu | High | Phase 2: persist state via URL params hoặc React context |
| 2 | **Chart tabs cannot be renamed** — auto-named from first signal, no manual rename | Medium | Phase 2: inline edit on tab label |
| 3 | **No chart type selector** — always line chart, no bar/scatter/area toggle | Low | Phase 2: add chart type dropdown |
| 4 | **GIS OSM tiles blocked in some environments** — VS Code browser blocks external tile requests | Low | Works in real browser; Phase 2: add tile fallback |
| 5 | **Datetime inputs use local time** — no UTC indicator, may confuse cross-timezone users | Low | Phase 2: add timezone label |

## Phase 2 Priorities

1. **Edge Agent** — DuckDB local buffer + MQTT publish + store-and-forward
2. **UX Polish** — State persistence, chart rename, chart type selector
3. **Asset Tree View** — Hierarchy navigation (Plant → Area → Asset)
4. **Diagram Enhancement** — Click element → navigate detail, alarm overlay
5. **Real-time Updates** — WebSocket for live data push (diagram, current values)
