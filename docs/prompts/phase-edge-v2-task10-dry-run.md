# E2V2-10: Limited Controlled Switch Dry-Run

> **SA Gate:** ✅ APPROVED 2026-07-09
> **Parent Report:** `docs/reports/edge-v2-production-readiness.md`
> **Constraint:** Edge v1 remains PRIMARY. Production switch NOT approved.
> **Scope:** Dry-run only — test switch procedure, NOT permanent.

## Context

All 6 SA gates have runtime evidence. SA approved limited controlled switch dry-run. This phase executes the migration runbook Phase 4-6 as a **controlled test** — verify the switch procedure works, then immediately verify rollback works. v1 remains primary throughout.

---

## Dry-Run Procedure (4 tasks)

### Task 1: Pre-Switch Verification

- [ ] **10.1** Verify all services healthy before starting
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001   # v1 → 200
  curl -s http://localhost:8011/api/status                        # v2 → running
  curl -s http://localhost:8000/health                            # Center → 200
  ```

- [ ] **10.2** Record baseline metrics
  - v2 backlog count
  - v2 buffer row count
  - Current time

### Task 2: Execute Switch (Migration Runbook Phase 4)

- [ ] **10.3** Follow migration runbook `docs/runbooks/edge-v1-to-v2-migration.md` Phase 4
  - Step 4.2: Verify Edge v2 is ingesting data
  - Step 4.3: Verify heartbeat reaches Center
  - **DO NOT** stop Edge v1 (this is a dry-run — v1 remains running)
  - This is a "shadow switch" — v2 acts as if it were primary, but v1 is still running

- [ ] **10.4** Verify switch state
  - v2 heartbeat: Center shows EDGEV2-PC-01 as online
  - v2 sync: measurements reaching Center for EDGEV2-DEMO
  - v1 unchanged: still running, still heartbeating

### Task 3: Verify Dry-Run Success

- [ ] **10.5** Run comparison during dry-run
  ```bash
  PLANTOS_CENTER_PASSWORD='...' python3 /opt/plantos/tools/compare_v1_v2_data.py \
    --hours 0.5 --center-url http://localhost:8000 \
    --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current
  ```
  - Expected: 3/3 PASS, diff within ±5%

- [ ] **10.6** Verify no data loss
  - v1 measurements still arriving in Center
  - v2 measurements still arriving in Center
  - Both workspaces have recent data

### Task 4: Execute Rollback (Migration Runbook Phase Rollback)

- [ ] **10.7** Follow rollback runbook `docs/runbooks/edge-v1-to-v2-rollback.md`
  - Step 1: Stop Edge v2
  - Step 2: Verify Edge v1 still running (was never stopped)
  - Step 3: Verify v1 heartbeat reaches Center
  - Step 4: Verify v1 data flow
  - Record: recovery time, data gap

- [ ] **10.8** Restore dry-run state
  - Restart Edge v2 (return to mirror mode)
  - Verify both v1 and v2 healthy

---

## Evidence to Collect

```
Pre-switch:   v1 status, v2 status, v2 backlog, timestamp
Switch:       v2 heartbeat 200, v2 sync 200, v1 unchanged
Comparison:   3/3 PASS within ±5%
Rollback:     recovery time, data gap, v1 unaffected
Post-restore: v1 healthy, v2 healthy
```

---

## Files to Update

```
docs/reports/edge-v2-production-readiness.md  — add E2V2-10 dry-run evidence
docs/runbooks/edge-v1-to-v2-migration.md       — record dry-run results
```

---

## Red Flags

- STOP if: v1 is affected in any way
- STOP if: v2 switch causes data loss or gap > 30s
- STOP if: rollback fails to restore state within 60s
- STOP if: comparison shows any deviation > 5%

## SA Constraints

```text
1. Edge v1 remains PRIMARY. Do NOT stop v1.
2. This is a DRY-RUN, not a production switch.
3. Rollback must be verified before any switch discussion.
4. Production switch requires separate SA review after dry-run evidence.
```
