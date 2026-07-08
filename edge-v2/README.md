# PlantOS Edge v2 (Edge Lite)

> Productization track for PlantOS Edge. Runs in parallel with Edge v1 (Track A).
> **Port 8011** — no conflict with Edge v1 on port 8001.

## Architecture

```
edge-v2/
  agent/              # EdgeAgentV2 — clean skeleton, DI-based
    main.py           # Entry point
    config/           # ConfigManager with ownership model
    auth/             # LocalAuthManager (stub → E2V2-1)
    connectors/       # ConnectorRegistry (stub → E2V2-2)
    processing/       # ProcessingEngine (stub → E2V2-3)
    commands/         # CommandPoller (stub → E2V2-4)
    web/              # WebServer (stub → E2V2-1)
  console/
    static/           # Local Console UI files
  simulator/          # Signal generator for testing
  tests/              # Test suite
```

## Selective Library Reuse

Edge v2 reuses these **Edge v1 libraries** without modification:

| Library | Source | Purpose |
|---|---|---|
| `DuckDBBuffer` | `edge/agent/buffer.py` | Local time-series buffer |
| `StoreAndForward` | `edge/agent/sync.py` | Sync buffered data to Center |
| `HealthReporter` | `edge/agent/health.py` | Periodic heartbeat to Center |
| `MQTTPublisher` | `edge/agent/publisher.py` | Publish measurements via MQTT |

All new code is in `edge_v2.agent.*` — no copy-paste from v1.

## Prerequisites

- Python 3.11+
- Edge v1 libraries accessible via `from edge.agent.*` — add repo root to `PYTHONPATH`

## Quick Start

```bash
# 1. Ensure PYTHONPATH includes repo root
export PYTHONPATH=$(pwd)

# 2. Install dependencies
pip install -r edge-v2/requirements.txt

# 3. Run the simulator (generates 7 signals for 5 assets)
python edge-v2/simulator/main.py

# 4. Run the Edge v2 agent (port 8011)
python edge-v2/agent/main.py \
  --config edge-v2/agent/config/config.edge-v2.yaml
```

## Seed Data

To create EDGEV2-DEMO workspace + assets in Center:

```bash
python scripts/seed_edgev2_demo.py
```

## Port Isolation

| Component | Port | Node ID | Workspace |
|---|---|---|---|
| Edge v1 (Track A) | 8001 | edge-agent-01 | WTP-DEMO-01 / VF-DEMO |
| Edge v2 (Track B) | 8011 | EDGEV2-PC-01 | EDGEV2-DEMO |

## Development

```bash
# Run tests
cd edge-v2 && python -m pytest tests/
```

## Version

Current: `2.0.0.dev` — Clean skeleton with stubs.
