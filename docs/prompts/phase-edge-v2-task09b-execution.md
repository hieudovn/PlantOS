# E2V2-7b: Controlled Migration — VPS Execution (5 tasks)

> **Parent Phase:** E2V2-7 (7/12 tasks done ✅ — see `docs/prompts/phase-edge-v2-task09-migration.md`)
> **This Prompt:** Remaining 5 VPS execution tasks only
> **SA Gate:** ✅ CONDITIONALLY APPROVED 2026-07-09
> **EV2-STAB:** ✅ CLOSED — 3/3 gates passed (Data E2E, Command E2E, Docker Smoke)
> **Constraint:** Edge v1 remains PRIMARY. Mirror-first. No production switch.

---

## Phase 0: What's Already Done (DO NOT RE-CREATE)

Before starting, read these files to understand current state:

| Done? | Task | Artifact |
|---|---|---|
| ✅ | 7.0 Docker smoke | Edge v2 running in Docker, port 8011, health OK |
| ✅ | 7.1-7.2 Mirror config | Merged in `edge-v2/agent/config/config.edge-v2.yaml` (2 connectors, 29 tags) |
| ✅ | 7.3 Migration utility | `tools/migrate_v1_config_to_v2.py` (fixed, tested) |
| ✅ | 7.5 Comparison script | `tools/compare_v1_v2_data.py` (ready to run) |
| ✅ | 7.7 Migration runbook | `docs/runbooks/edge-v1-to-v2-migration.md` (SA-aligned, Phase 4-6 BLOCKED) |
| ✅ | 7.8 Rollback runbook | `docs/runbooks/edge-v1-to-v2-rollback.md` (SA-aligned) |
| ✅ | 7.9 Seed script | `scripts/seed_edgev2_test.py` (creates EDGEV2-TEST workspace) |

---

## Phase 1: Pre-flight Check

Before executing any task, verify VPS state:

```bash
ssh plantos@103.97.132.249   # pass: PlantOS@2026!

# 1.1 Edge v1 still running?
curl -s http://localhost:8001 | head -5
# Expected: HTML dashboard or 200

# 1.2 Edge v2 Docker running?
docker ps --filter name=plantos-edge-v2
curl -s http://localhost:8011/api/status
# Expected: {"status":"running","edge_node_id":"EDGEV2-PC-01",...}

# 1.3 Center API reachable?
curl -s http://localhost:8000/health
# Expected: 200

# 1.4 Config has mirror connectors?
docker exec plantos-edge-v2 cat /app/config/config.edge-v2.yaml | grep -A2 "connectors:"
# Expected: mirror_wtp_signals + mirror_vf_compressor
```

**Red flag:** If Edge v1 is stopped → STOP. v1 must remain PRIMARY.

---

## Phase 2: Side-by-Side Comparison (Task 7.4)

**Goal:** Run v1 and v2 simultaneously for 1 hour, compare data quality.

```bash
# 2.1 Wait for both to accumulate data (1 hour)
# Check v2 is ingesting:
watch -n 30 'curl -s http://localhost:8011/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"buffer_rows={d[\"buffer\"][\"row_count\"]} backlog={d[\"sync\"][\"backlog\"]}\")"'

# 2.2 After 1 hour, run comparison
python3 tools/compare_v1_v2_data.py --hours 1 --center-url http://localhost:8000

# 2.3 Expected output
# All shared signals within ±5% tolerance
# v2 data point count >= 80% of v1 count
# No quality degradation
```

**Red flag:** Any signal exceeds ±5% → STOP, report to PM.

---

## Phase 3: Center Offline Simulation (Task 7.6)

**Goal:** Verify both v1 and v2 buffer correctly when Center is unreachable.

```bash
# 3.1 Record baseline
curl -s http://localhost:8011/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"backlog_before={d['sync']['backlog']}\")"

# 3.2 Stop Center backend for 5 minutes
docker stop plantos-backend
echo "Center stopped at $(date)"
# v1 and v2 should continue buffering

# 3.3 Wait 5 minutes — check buffers grow
sleep 300

# 3.4 Check v2 backlog
curl -s http://localhost:8011/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"backlog_after={d['sync']['backlog']}\")"
# Expected: backlog > 0 (data was buffered)

# 3.5 Restore Center
docker start plantos-backend
echo "Center restored at $(date)"

# 3.6 Wait for flush (up to 2 minutes)
sleep 120

# 3.7 Verify backlog cleared
curl -s http://localhost:8011/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"backlog_final={d['sync']['backlog']}\")"
# Expected: backlog ≈ 0 (flushed successfully)
```

**Red flag:** Backlog remains > 100 after 2 minutes → sync failure, investigate.

---

## Phase 4: Dry-Run Migration (Tasks 7.9)

**Goal:** Test full migration cycle on isolated EDGEV2-TEST workspace.

```bash
# 4.1 Create test workspace
python3 scripts/seed_edgev2_test.py --api-url http://localhost:8000
# Expected: Created 1 plant, 1 area, 3 assets, 5 signals

# 4.2 Verify test workspace exists
curl -s http://localhost:8000/api/v1/plants/EDGEV2-TEST
# Expected: 200 with plant data

# 4.3 Follow migration runbook Phase 1-3 ONLY (PRE-MIGRATION, MIRROR, COMPARISON)
# Phases 4-6 are BLOCKED per SA
cat docs/runbooks/edge-v1-to-v2-migration.md

# 4.4 Run config migration in dry-run mode
python3 tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --dry-run
# Expected: 2 connectors printed, no files modified

# 4.5 Compare v1 and v2 for test signals
python3 tools/compare_v1_v2_data.py --v1-workspace EDGEV2-TEST --v2-workspace EDGEV2-DEMO --hours 1
```

**Red flag:** If rollback cannot restore v1 state → STOP.

---

## Phase 5: Rollback Dry-Run (Task 7.10)

**Goal:** Simulate v2 failure, verify v1 is unaffected.

```bash
# 5.1 Record v1 state before test
curl -s http://localhost:8001 | head -3
# Expected: v1 responding

# 5.2 Stop Edge v2 Docker
docker stop plantos-edge-v2
echo "v2 stopped at $(date)"

# 5.3 Verify v1 still running (was NEVER stopped — mirror mode)
curl -s http://localhost:8001 | head -3
# Expected: v1 still responding ✅

# 5.4 Verify v1 data still flowing to Center
# Check Center for recent v1 data:
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3"

# 5.5 Follow rollback runbook
cat docs/runbooks/edge-v1-to-v2-rollback.md
# Step 2: VERIFY v1 still running (mirror mode, v1 never stopped)

# 5.6 Restart Edge v2
docker start plantos-edge-v2
sleep 5
curl -s http://localhost:8011/api/status
# Expected: {"status":"running",...}

# 5.7 Record results
# Data gap: should be 0 (v1 never stopped)
# Recovery time: measured from v2 stop to v2 restart
```

**Red flag:** If v1 is affected in any way → STOP, v1 is PRIMARY.

---

## Phase 6: Final Report (Task 7.12)

Update `docs/reports/edge-v2-migration-prep.md`:

- [ ] Fill in side-by-side comparison results (Phase 2)
- [ ] Fill in Center offline simulation results (Phase 3)
- [ ] Fill in dry-run migration results (Phase 4)
- [ ] Fill in rollback dry-run results (Phase 5)
- [ ] Update status to "Execution Complete" or "Execution Partial"
- [ ] Update recommendation section

---

## VPS Reference

```text
Host:    103.97.132.249
User:    plantos
Pass:    PlantOS@2026!
Edge v1: native Python, port 8001
Edge v2: Docker container plantos-edge-v2, port 8011
Center:  Docker containers (backend port 8000, postgres, tdengine, emqx)
Config:  /home/plantos/edge-v2/agent/config/config.edge-v2.yaml
Repo:    /home/plantos/
```

---

## SA Constraints (READ CAREFULLY)

```text
1. DO NOT disable, stop, or deprecate Edge v1.
2. DO NOT claim production readiness.
3. DO NOT switch any production workspace to Edge v2.
4. DO NOT execute migration runbook Phase 4-6 (BLOCKED).
5. Rollback dry-run only — v1 must remain running throughout.
```

## Red Flags

- STOP if: Edge v1 is stopped or affected
- STOP if: side-by-side shows data quality regression >5%
- STOP if: rollback dry-run shows v1 dependency on v2
- STOP if: any production workspace is switched to v2
