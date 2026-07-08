# E2V2-0: Isolation + Clean Skeleton

## Context

Edge v2 must run in parallel with Edge v1 without any interference. This phase creates the `edge-v2/` folder, a clean `EdgeAgentV2` skeleton (NOT a copy of v1), imports reusable v1 libraries, and sets up the EDGEV2-DEMO workspace. Code reuse: selective import of DuckDB buffer, sync, health reporter, and MQTT publisher from v1 as libraries. Everything else (web server, config manager, connectors, auth, processing) is built fresh.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §6, §7, §17
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Edge v1 unchanged (Track A stable baseline)
- [x] Clean architecture, dependency injection (no global module variables)
- [x] Separate workspace EDGEV2-DEMO (no contamination)
- [x] Separate port 8011 (no conflict)
- [x] Selective library reuse from v1, NOT copy-paste
- [x] Backward-compatible heartbeat format

## Implementation Checklist

### Repository Setup

- [ ] **0.1** Create `feature/edge-v2` branch from main (after CF-0 merged)
- [ ] **0.2** Create `edge-v2/` directory structure:
  ```
  edge-v2/
    agent/
      __init__.py
      main.py
      config/
        __init__.py
      auth/
        __init__.py
      connectors/
        __init__.py
      processing/
        __init__.py
      commands/
        __init__.py
      web/
        __init__.py
    console/
      static/
        css/
        js/
    simulator/
      __init__.py
      scenarios/
      protocol_servers/
    tests/
      __init__.py
  ```

### Clean EdgeAgentV2 Skeleton

- [ ] **0.2** Create `edge-v2/agent/main.py` with `EdgeAgentV2` class:
  ```python
  class EdgeAgentV2:
      def __init__(self, config_path: str):
          self.config = ConfigManager(config_path)     # Stub for now
          self.buffer = DuckDBBuffer(...)              # Import from edge.agent.buffer
          self.sync = StoreAndForward(...)             # Import from edge.agent.sync
          self.health = HealthReporter(...)            # Import from edge.agent.health
          # Auth, connectors, processing, commands, web — stubs for now
  ```
  - NO global module variables
  - All dependencies injected via constructor
  - Config path from `EDGE_CONFIG_PATH` env var or CLI arg

- [ ] **0.3** Verify import of `DuckDBBuffer` from `edge.agent.buffer`:
  - Add `edge-v2/requirements.txt` with duckdb dependency
  - Verify `from edge.agent.buffer import DuckDBBuffer` works
  - If import path issue, document workaround in README

- [ ] **0.4** Verify import of `StoreAndForward` from `edge.agent.sync`:
  - Verify `from edge.agent.sync import StoreAndForward` works
  - Configure with EDGEV2 center URL + ingest endpoint

- [ ] **0.5** Verify import of `HealthReporter` from `edge.agent.health`:
  - Verify `from edge.agent.health import HealthReporter` works
  - Configure with EDGEV2 node_id and heartbeat URL

### Config

- [ ] **0.6** Create `edge-v2/agent/config/config.edge-v2.yaml`:
  ```yaml
  edge_node_id: EDGEV2-PC-01
  plant_id: EDGEV2-DEMO
  center_url: http://localhost:8000
  api_key: plantos-edge-key-2026
  buffer:
    path: edge-v2/data/edge_data.duckdb
    retention_days: 7
  mqtt:
    host: localhost
    port: 1883
    topic_prefix: avenue/edgev2-demo
  http:
    ingest_url: http://localhost:8000/api/v1/measurements/ingest
  heartbeat:
    url: http://localhost:8000/api/v1/edge-nodes/heartbeat
    interval_seconds: 10
  publish:
    interval_seconds: 10
    batch_size: 10
  web:
    port: 8011
  ```
  - Port MUST be 8011 (not 8001)
  - node_id MUST be EDGEV2-PC-01 (not edge-agent-01)

### Simulator

- [ ] **0.7** Create `edge-v2/simulator/main.py` with basic sine generator:
  - Generate sine waves for 5 assets × varying # of signals = 7 signals
  - Signals: flow_rate, discharge_pressure, vibration, level, running_status, turbidity, active_power
  - Configurable amplitude, frequency, noise
  - Output to stdout for now (will connect to buffer in E2V2-1)
  - Create scenario file: `simulator/scenarios/normal_operation.yaml`

### Center Seed Data

- [ ] **0.8** Create seed script `scripts/seed_edgev2_demo.py`:
  - Workspace: EDGEV2-DEMO
  - Plant: EDGEV2-DEMO
  - 5 assets: PUMP-101, TANK-101, MOTOR-101, QUALITY-STATION-101, ENERGY-METER-101
  - 7 signals with units
  - All prefixed with EDGEV2- (e.g., EDGEV2-PUMP-101)

### Tests

- [ ] **0.9** Verify Edge v1 unchanged:
  - Run Edge v1 agent on port 8001
  - Verify heartbeat reaches Center
  - Verify sync works
  - Verify local UI on port 8001

- [ ] **0.10** Verify Edge v2 skeleton:
  - Run `python -m edge_v2.agent.main` from repo root
  - Verify agent starts on port 8011
  - Verify heartbeat reaches Center (visible in fleet as EDGEV2-PC-01)
  - Verify simulator generates data to stdout
  - Verify no port conflicts

## Files to Create

```
edge-v2/
  agent/
    __init__.py
    main.py
    config/
      __init__.py
    auth/__init__.py
    connectors/__init__.py
    processing/__init__.py
    commands/__init__.py
    web/__init__.py
  console/static/css/ (empty dir)
  console/static/js/ (empty dir)
  simulator/
    __init__.py
    main.py
    scenarios/normal_operation.yaml
    protocol_servers/__init__.py
  tests/__init__.py
  requirements.txt
  README.md

edge-v2/agent/config/config.edge-v2.yaml
scripts/seed_edgev2_demo.py
```

## Files to Modify

None (all new files in edge-v2/)

## Acceptance Criteria

```text
✅ Edge v1: unchanged, running on port 8001, node=edge-agent-01
✅ Edge v2: clean skeleton running on port 8011, node=EDGEV2-PC-01
✅ Edge v2: simulator generates 7 signals for 5 assets
✅ Edge v2: heartbeat reaches Center, distinguishable from v1
✅ Center: EDGEV2-DEMO workspace visible after running seed script
✅ No regression in Edge v1 functionality
✅ No global module variables in Edge v2
✅ Import from edge.agent.* works without modifying v1 code
```

## Red Flags

- Stop if: need to modify Edge v1 code for imports to work
- Stop if: port 8011 conflicts with any running service
- Stop if: heartbeat reaches Center but overwrites Edge v1 data
- Stop if: constitution violation (raw DB access, bypassing UNS/CDM)
