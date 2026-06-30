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
