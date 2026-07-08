# Migration Runbook: Edge v1 → Edge v2

> **⚠️ NOT YET ACTIVE — SA approval required before execution**
>
> Status: DRAFT for dry-run testing only
> Edge v1 remains PRIMARY until SA signs off.

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
| Common signal_ids exist in both workspaces | `python tools/compare_v1_v2_data.py --dry-run` |
| Rollback runbook printed | Available at `docs/runbooks/edge-v1-to-v2-rollback.md` |

---

## Phase 1: PRE-MIGRATION

**Goal:** Verify prerequisites, backup config, check signal mapping.

```bash
# 1.1 Backup Edge v1 config
cp edge/agent/config.yaml edge/agent/config.yaml.migration-backup-$(date +%Y%m%d_%H%M%S)

# 1.2 Backup Edge v2 config
cp edge-v2/agent/config/config.edge-v2.yaml edge-v2/agent/config/config.edge-v2.yaml.migration-backup-$(date +%Y%m%d_%H%M%S)

# 1.3 Run v1→v2 config migration in dry-run mode
python tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --dry-run

# 1.4 Verify shared signal_ids exist in both workspaces
python tools/compare_v1_v2_data.py --hours 1
```

**Expected output:**
```
Edge v1 not modified.
Connectors generated: 2
  - mirror_signals: type=http_poll, tags=3
  - vf_compressor: type=opcua, tags=26
All shared signals within tolerance.
```

**Rollback trigger:** If migration utility fails → STOP. Do not proceed.

---

## Phase 2: MIRROR

**Goal:** Edge v2 mirrors v1 signals to separate workspace. v1 remains primary.

```bash
# 2.1 Apply migrated connector config to Edge v2
python tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --output edge-v2/config/edge_config.yaml

# 2.2 Restart Edge v2 to pick up new connectors
# systemd:
sudo systemctl restart plantos-edge-v2
# Docker:
docker compose -f edge-v2/docker-compose.edge-v2.yml restart

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

## Phase 4: SWITCH (🔴 BLOCKED — SA CONDITIONAL APPROVAL)

> **🔴 DO NOT EXECUTE. SA has conditionally approved E2V2-7 for mirror/preparation only.**
>
> Per SA decision (2026-07-09):
> - Edge v1 remains PRIMARY. Do NOT stop, disable, or deprecate.
> - No production workspace switch until Docker smoke passes + full SA approval.
> - This phase requires a NEW SA gate review before execution.
>
> See: `docs/reports/edge-v2-stab-final-sa-review.md`

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
- Docker smoke passed on production environment
- Side-by-side comparison passed for 24+ hours
- Dry-run migration + rollback passed on test workspace
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
| Restart v2 (Docker) | `docker compose -f edge-v2/docker-compose.edge-v2.yml restart` |
| View v2 logs (systemd) | `journalctl -u plantos-edge-v2 -f` |
| View v2 logs (Docker) | `docker logs plantos-edge-v2 -f` |
| Run comparison | `python tools/compare_v1_v2_data.py` |
| Run migration tool | `python tools/migrate_v1_config_to_v2.py --dry-run` |

---

## Appendix: Dry-Run Results

*To be filled after dry-run test:*

| Step | Date | Tester | Result | Notes |
|---|---|---|---|---|
| Phase 1: Pre-migration | | | | |
| Phase 2: Mirror | | | | |
| Phase 3: Comparison | | | | |
| Phase 4: Switch | | | N/A | SA not yet approved |
| Phase 5: Verify | | | | |
| Phase 6: Commit | | | | |
