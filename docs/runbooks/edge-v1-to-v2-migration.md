# Migration Runbook: Edge v1 → Edge v2

> **⚠️ NOT YET ACTIVE — SA approval required before execution**
>
> Status: DRAFT — Reviewed for E2V2-9 (2026-07-09) ✅ READY FOR SA REVIEW
> Edge v1 remains PRIMARY until SA signs off.
>
> **E2V2-9 Update:** Dry-run preparation complete. Seed scripts and comparison tool
> ready. Actual switch still requires SA full approval.

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

## Phase 4: SWITCH (🔴 BLOCKED — PENDING FINAL SA APPROVAL)

> **🔴 DO NOT EXECUTE. SA has conditionally approved E2V2-9 for switch PREPARATION only.**
>
> Per SA decision (2026-07-09):
> - Edge v1 remains PRIMARY. Do NOT stop, disable, or deprecate.
> - Side-by-side comparison is THE GATE for switch discussion.
> - No production workspace switch until comparison evidence + SA full approval.
>
> **E2V2-9 Status (2026-07-09):** All preparation code/scripts merged.
> Side-by-side comparison execution blocked by: VPS deployment of seed script.
> See: `docs/reports/edge-v2-production-readiness.md`
> See: `docs/prompts/phase-edge-v2-task09-switch-execution.md`

**Goal (FUTURE):** Redirect data flow from v1 to v2 after all gates cleared.

```bash
# 🔴 DO NOT RUN — BLOCKED
# When unblocked by SA:
# 1. Edge v1 stays running as fallback (do NOT stop)
# 2. Update Center workspace config to read from EDGEV2-DEMO
# 3. Verify both v1 and v2 data reach Center (dual-write for 24h)
# 4. After 24h stable dual-write, SA may approve v1 decommission
```

**Prerequisites for unblocking (all must be met):**
```
- Side-by-side comparison: ≥3 shared signal_ids, all within ±5% tolerance
- v2 sync backlog < 50 for > 30 minutes
- All services healthy (v1, v2, Center)
- SA full approval (not conditional)
```

---

## Phase 5: VERIFY (🔴 BLOCKED — see Phase 4)

> **🔴 DO NOT EXECUTE.** Requires Phase 4 unblock first.

**Goal (FUTURE):** Confirm v2 is operating correctly with Center reading from EDGEV2-DEMO.

---

## Phase 6: COMMIT (🔴 BLOCKED — see Phase 4)

> **🔴 DO NOT EXECUTE.** Requires Phase 4-5 completion + SA sign-off.

**Goal (FUTURE):** Finalize migration. Edge v1 config preserved for rollback, NOT archived/deleted.

```bash
# When unblocked:
# 1. Keep v1 config as edge/agent/config.yaml.rollback (do NOT delete)
# 2. Tag migration in git
# 3. Document in runbook appendix
```

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
| Phase 1: Pre-migration | 2026-07-09 | AI (E2V2-9) | ✅ READY | Seed script created, comparison tool fixed |
| Phase 2: Mirror | 2026-07-09 | AI (E2V2-9) | ✅ READY | Commands updated for VPS Docker deployment |
| Phase 3: Comparison | 2026-07-09 | AI (E2V2-9) | ⏳ PENDING | Requires VPS execution of seed + comparison |
| Phase 4: Switch | — | — | 🔴 BLOCKED | WAITING SA full approval |
| Phase 5: Verify | — | — | 🔴 BLOCKED | WAITING SA full approval |
| Phase 6: Commit | — | — | 🔴 BLOCKED | WAITING SA full approval |

### E2V2-9 Artifacts

| Artifact | File | Status |
|---|---|---|
| Seed script (EDGEV2-DEMO) | `scripts/seed_edgev2_demo.py` | ✅ Created |
| VPS execution prompt | `docs/prompts/phase-edge-v2-task09-switch-execution.md` | ✅ Created |
| Production readiness report | `docs/reports/edge-v2-production-readiness.md` | ✅ Updated |
| Comparison CSV | `edge-v2/data/comparison_*.csv` | ⏳ PENDING (VPS) |
