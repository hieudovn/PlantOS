# Migration Runbook: Edge v1 → Edge v2

> **⚠️ NOT YET ACTIVE — SA approval required before production execution**
>
> Status: EXTENDED PILOT — E2V2-11 (2026-07-09)
> Edge v1 remains PRIMARY. Production switch NOT approved.
>
> **E2V2-10:** Dry-run PASSED (4/4 tasks, 3/3 comparison, 0.0% diff).
> **E2V2-11:** Extended pilot preparation complete. Phase 4-6 commands verified in dry-run.
> All dry-run evidence available in `docs/reports/edge-v2-production-readiness.md`.
> Production switch requires SA approval of complete approval matrix.

## Overview

This runbook describes the controlled migration of an Edge node from v1 to v2.
The process follows: **PRE-MIGRATION → MIRROR → COMPARISON → SWITCH → VERIFY → COMMIT**

Each step has a clear command, expected output, and rollback trigger.

---

## Prerequisites

| Item | Check |
|---|---|
| Edge v1 running on port 8001 | `curl http://localhost:8001` → 200 |
| Edge v2 running on port 8011 | `curl http://localhost:8011/api/status` → 200 |
| Center API reachable | `curl http://localhost:8000/health` → 200 |
| PostgreSQL has edge_nodes table | Verify via `docker exec -it plantos-postgres psql -U plantos -c "SELECT edge_node_id FROM edge_nodes"` |
| Common signal_ids exist in both workspaces | `python tools/compare_v1_v2_data.py --hours 1` |
| Rollback runbook printed | Available at `docs/runbooks/edge-v1-to-v2-rollback.md` |
| **VPS-specific:** Docker deployment | Edge v2 runs in Docker container. Use `docker compose` commands, NOT systemctl. |

---

## Phase 1: PRE-MIGRATION

**Goal:** Verify prerequisites, backup config, seed workspace, check signal mapping.

```bash
# 1.1 Backup Edge v1 config
cp edge/agent/config.yaml edge/agent/config.yaml.migration-backup-$(date +%Y%m%d_%H%M%S)

# 1.2 Backup Edge v2 config
cp edge-v2/agent/config/config.edge-v2.yaml edge-v2/agent/config/config.edge-v2.yaml.migration-backup-$(date +%Y%m%d_%H%M%S)

# 1.3 Seed EDGEV2-DEMO workspace with shared signals (if not already done)
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
python scripts/seed_edgev2_demo.py

# 1.4 Generate sample measurements for immediate comparison (optional)
python scripts/seed_edgev2_demo.py --generate-measurements

# 1.5 Run v1→v2 config migration in dry-run mode
python tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --dry-run

# 1.6 Verify shared signal_ids exist in both workspaces
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
python tools/compare_v1_v2_data.py --hours 1
```

**Expected output:**
```
Edge v1 not modified.
Connectors generated: 2
  - mirror_signals: type=http_poll, tags=3
  - vf_compressor: type=opcua, tags=26
v1 signals: 15, v2 signals: 15
Shared signal_ids: 15
Results: 15 PASS, 0 FAIL, 0 WARN, 0 SKIP
✅ All shared signals within tolerance.
```

**Rollback trigger:** If migration utility fails → STOP. Do not proceed.

---

## Phase 2: MIRROR

**Goal:** Edge v2 mirrors v1 signals to separate workspace. v1 remains primary.

```bash
# 2.1 Apply migrated connector config to Edge v2
python tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --output edge-v2/config/edge_config.yaml

# 2.2 Restart Edge v2 to pick up new connectors
# VPS (Docker):
docker compose -f /opt/plantos/deployment/docker-compose.yml exec plantos-edge-v2 \
  python /app/agent/commands/poller.py --action reload_config
# OR full restart:
docker compose -f /opt/plantos/deployment/docker-compose.yml restart plantos-edge-v2

# Local (Docker):
docker compose -f edge-v2/docker-compose.edge-v2.yml restart

# systemd (alternative deployment):
# sudo systemctl restart plantos-edge-v2

# 2.3 Verify Edge v2 health
curl http://localhost:8011/api/status
```

**Expected output:**
```
{"status": "running", "edge_node_id": "EDGEV2-PC-01", ...}
```

**Rollback trigger:** If Edge v2 fails to start → remove connector config, restart v2 without mirror.

---

## Phase 3: COMPARISON

**Goal:** Compare v1 and v2 data quality for at least 1 hour.

```bash
# 3.1 Run initial comparison
python tools/compare_v1_v2_data.py --hours 1

# 3.2 Wait 30 minutes, run again
sleep 1800
python tools/compare_v1_v2_data.py --hours 0.5 --output /tmp/comparison_30min.csv

# 3.3 Wait another 30 minutes, final comparison
sleep 1800
python tools/compare_v1_v2_data.py --hours 1 --output /tmp/comparison_final.csv
```

**Acceptance criteria:**
```
- All shared signals within ±5% tolerance
- v2 backlog < v1 backlog at same time point
- v2 data point count >= 80% of v1 count
- No quality degradation in v2
```

**Rollback trigger:**
- Any signal exceeds ±5% tolerance → STOP
- v2 data point count < 50% of v1 → STOP

---

## Phase 4: SWITCH

> **🟡 DRY-RUN ONLY — SA approved limited controlled switch dry-run (E2V2-10)**
>
> SA decision (2026-07-09):
> - ✅ Dry-run APPROVED for testing switch procedure.
> - 🔴 Edge v1 remains PRIMARY. Do NOT stop v1.
> - 🔴 Production switch NOT approved — requires separate SA review.
> - This phase verified in dry-run only. Rollback must follow (see Phase 6).

**Goal (DRY-RUN):** Shadow-switch — v2 acts as primary while v1 still runs.

```bash
# 🟡 DRY-RUN — SA APPROVED
# 4.1 Verify v2 is ingesting and healthy
curl http://localhost:8011/api/status

# 4.2 Verify v2 heartbeat reaches Center
curl -s http://localhost:8000/api/v1/edge-nodes | python3 -c "
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f\"  {n['edge_node_id']}: {n.get('status','?')}\")
"

# 4.3 Verify both v1 and v2 data reaching Center (dual-write)
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=1" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'v1 DEMO-PLANT: {len(d)} points')"
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=1" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'v2 EDGEV2-DEMO: {len(d)} points')"

# 4.4 Run comparison during shadow mode
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
python3 /opt/plantos/tools/compare_v1_v2_data.py --hours 0.5 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current
```

**Expected output:**
```
v1 DEMO-PLANT: > 0 points
v2 EDGEV2-DEMO: > 0 points
Results: 3 PASS, 0 FAIL, 0 WARN, 0 SKIP
✅ All shared signals within tolerance.
```

**Rollback trigger:** Any signal exceeds ±5% tolerance → STOP → run Phase 6 rollback.

---

## Phase 5: VERIFY

> **🟡 DRY-RUN ONLY — Run after Phase 4 dry-run comparison passes.**

**Goal (DRY-RUN):** Confirm no data loss during shadow mode — both workspaces healthy.

```bash
# 🟡 DRY-RUN
# 5.1 Verify v1 unchanged
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"

# 5.2 Verify v2 unchanged
echo "v2: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))')"

# 5.3 Verify Center still healthy
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

# 5.4 Record final state
echo "=== VERIFY $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
curl -s http://localhost:8000/api/v1/edge-nodes | python3 -c "
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f\"  {n['edge_node_id']}: {n.get('status','?')}\")
"
```

**Expected:**
```
v1: 200
v2: running
Center: 200
edge-agent-01: online
EDGEV2-PC-01: online
```

---

## Phase 6: ROLLBACK & RESTORE (Dry-Run Cleanup)

> **🟡 DRY-RUN ONLY — Restore mirror mode after dry-run completes.**

**Goal:** Stop shadow mode, restore v2 to mirror mode, verify v1 unaffected.

```bash
# 🟡 DRY-RUN — Rollback shadow switch
# 6.1 Stop Edge v2 (shadow)
docker compose -f /opt/plantos/deployment/docker-compose.yml stop plantos-edge-v2

# 6.2 Verify Edge v1 never stopped
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"

# 6.3 Verify v1 heartbeat reaches Center
sleep 5
curl -s http://localhost:8000/api/v1/edge-nodes | python3 -c "
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f\"  {n['edge_node_id']}: {n.get('status','?')}\")
"

# 6.4 Restart Edge v2 (back to mirror mode)
docker compose -f /opt/plantos/deployment/docker-compose.yml start plantos-edge-v2
sleep 10

# 6.5 Final verification
echo "=== FINAL STATE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
echo "v2: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))')"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

# 6.6 Record recovery time
echo "Recovered to mirror mode."
```

**Expected:**
```
v1: 200 (never stopped)
edge-agent-01: online
EDGEV2-PC-01: offline → online (after restart)
v2: running
Center: 200
Recovery time: < 60 seconds
```

**Rollback trigger (red):** If v1 goes to anything other than 200 at any point → CRITICAL FAILURE. Notify SA immediately.

---

## Appendix: Quick Reference

| Action | Command |
|---|---|
| Check v1 status | `curl http://localhost:8001` |
| Check v2 status | `curl http://localhost:8011/api/status` |
| Restart v2 (systemd) | `sudo systemctl restart plantos-edge-v2` |
| Restart v2 (Docker local) | `docker compose -f edge-v2/docker-compose.edge-v2.yml restart` |
| Restart v2 (VPS Docker) | `docker compose -f /opt/plantos/deployment/docker-compose.yml restart plantos-edge-v2` |
| Reload v2 config (VPS) | `docker compose -f /opt/plantos/deployment/docker-compose.yml exec plantos-edge-v2 python /app/agent/commands/poller.py --action reload_config` |
| View v2 logs (systemd) | `journalctl -u plantos-edge-v2 -f` |
| View v2 logs (Docker) | `docker logs plantos-edge-v2 -f` |
| Run comparison | `python tools/compare_v1_v2_data.py` |
| Run migration tool | `python tools/migrate_v1_config_to_v2.py --dry-run` |

---

## Appendix: Dry-Run Results

| Step | Date | Tester | Result | Notes |
|---|---|---|---|---|
| Phase 1: Pre-migration | 2026-07-09 | E2V2-9 | ✅ DONE | Seed script created, comparison tool fixed |
| Phase 2: Mirror | 2026-07-09 | E2V2-9 | ✅ DONE | Commands updated for VPS Docker |
| Phase 3: Comparison | 2026-07-09 | E2V2-9 | ✅ PASS | 3/3 signals, 357pts each, 0.0% diff |
| Phase 4: Switch (dry-run) | 2026-07-09 | E2V2-10 | ✅ PASS | Shadow switch — v1=200, v2=running, both data flowing |
| Phase 5: Verify (dry-run) | 2026-07-09 | E2V2-10 | ✅ PASS | 3/3 comparison PASS, 0.0% diff, 178pts each |
| Phase 6: Rollback (dry-run) | 2026-07-09 | E2V2-10 | ✅ PASS | v2 stop→v1=200 unchanged→v2 restart→healthy |

### E2V2-10 Evidence (VPS 2026-07-09 04:34-04:37 UTC)

```
Pre-switch:   v1=200, v2=running, Center=200, backlog=3
Switch:       v2 heartbeat=200, v2 sync=200, v1 unchanged (200)
Comparison:   3/3 PASS within ±5% (178pts each, 0.00% diff)
Rollback:     recovery_time=<60s, data_gap=0s (v1 never stopped)
Post-restore: v1=200, v2=running (healthy), Center=200
```

Comparison CSV: `edge-v2/data/dry_run_comparison_20260709_113528.csv`

### E2V2-9 Artifacts

| Artifact | File | Status |
|---|---|---|
| Seed script (EDGEV2-DEMO) | `scripts/seed_edgev2_demo.py` | ✅ Created |
| VPS execution prompt (E2V2-9) | `docs/prompts/phase-edge-v2-task09-switch-execution.md` | ✅ Created |
| VPS execution prompt (E2V2-10) | `docs/prompts/phase-edge-v2-task10-dry-run-execution.md` | ✅ Created |
| Production readiness report | `docs/reports/edge-v2-production-readiness.md` | ✅ Updated |
| Comparison CSV | `edge-v2/data/comparison_*.csv` | ⏳ PENDING (VPS) |
