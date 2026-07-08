# PlantOS Edge v2 (Edge Lite)

> **🔴 MIRROR MODE — Edge v1 is PRIMARY.**
>
> Edge v2 runs as a mirror/sidecar against the `EDGEV2-DEMO` workspace.
> **Do NOT stop, disable, or deprecate Edge v1.** No production switch has been made.
>
> **SA Status:** ✅ CONDITIONALLY APPROVED 2026-07-09 (mirror-only; Docker smoke pending)
> See: [`docs/reports/edge-v2-stab-final-sa-review.md`](../docs/reports/edge-v2-stab-final-sa-review.md)
> **Productization track** for PlantOS Edge. Runs in parallel with Edge v1 (Track A).
> **Port 8011** — no conflict with Edge v1 on port 8001.

## Architecture

```
edge-v2/
  agent/              # EdgeAgentV2 — clean skeleton, DI-based
    main.py           # Entry point
    config/           # ConfigManager with ownership model
    auth/             # LocalAuthManager
    connectors/       # OPC UA, Modbus TCP/RTU, MQTT, HTTP Poll
    processing/       # 7 MVP processing steps
    commands/         # Pull-based command execution
    web/              # Local Console on port 8011
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

All new code is in `edge-v2/agent/` — no copy-paste from v1.

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

## Port & Workspace Isolation

| Component | Port | Node ID | Workspace |
|---|---|---|---|
| Edge v1 (Track A) | 8001 | edge-agent-01 | WTP-DEMO-01 / VF-DEMO |
| Edge v2 (Track B) | 8011 | EDGEV2-PC-01 | EDGEV2-DEMO |

## Migration Tools

Located in `tools/`:

| Tool | Purpose |
|---|---|
| `migrate_v1_config_to_v2.py` | Translate v1 config to v2 connector format. Use `--dry-run` first. |
| `compare_v1_v2_data.py` | Compare v1 vs v2 measurement data (±5% tolerance) |

Runbooks available in `docs/runbooks/`:
- `edge-v1-to-v2-migration.md` — Full migration procedure (⚠️ NOT YET ACTIVE)
- `edge-v1-to-v2-rollback.md` — Rollback procedure

## Known Limitations

| Limitation | Status | Details |
|---|---|---|
| Docker smoke | 🔴 Blocked | Docker Hub TLS timeout on VPS. Code ready. |
| Production switch | 🔴 Not approved | Requires SA GO decision after Docker smoke + side-by-side comparison. |
| restart_agent | ✅ Works | Via Docker restart policy or systemd `Restart=on-failure` |

## Development

```bash
# Run tests
cd edge-v2 && python -m pytest tests/
```

## Version

Current: `2.0.0.dev` — All E2V2 phases implemented (0-7). Stabilization complete.
