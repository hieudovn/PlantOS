# E2V2-9: Controlled Switch Preparation

> **SA Gate:** ✅ CONDITIONALLY APPROVED 2026-07-09
> **Parent Report:** `docs/reports/edge-v2-production-readiness.md`
> **Constraint:** Edge v1 remains PRIMARY. Switch NOT approved until evidence complete.

## Context

E2V2-8 hardening complete. 5/5 SA checks PASS. JWT heartbeat/sync working (200 OK). SA approves preparation for controlled switch with one blocking condition: **side-by-side comparison must produce valid evidence with shared signals and acceptable data quality metrics.**

---

## SA Conditions (READ FIRST)

```text
1. Edge v1 remains PRIMARY. NO switch without SA full approval.
2. Side-by-side comparison MUST show shared signals within ±5% tolerance.
3. Comparison results are the GATE for switch discussion.
4. Docker runtime must remain healthy throughout.
```

---

## Implementation Checklist (6 tasks)

### Task 1: Seed EDGEV2-DEMO with Shared Signals

- [ ] **9.1** Ensure EDGEV2-DEMO has same signal_ids as DEMO-PLANT in Center
  - Run `scripts/seed_edgev2_demo.py` with JWT auth
  - Signals: `PUMP-101.flow_rate`, `PUMP-101.discharge_pressure`, `MOTOR-101.motor_current`
  - Verify via `GET /api/v1/signals?plant_id=EDGEV2-DEMO`

- [ ] **9.2** Verify v2 data is reaching Center measurements
  - Check `GET /api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=5`
  - Should return non-empty after seeding + data accumulation

### Task 2: Side-by-Side Comparison (SA GATE)

- [ ] **9.3** Wait for minimum 30 minutes of data accumulation
  - v2 must be running and syncing to Center (heartbeat 200, sync 200)
  - Both DEMO-PLANT and EDGEV2-DEMO should have measurement data

- [ ] **9.4** Run comparison tool
  ```bash
  export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
  python tools/compare_v1_v2_data.py --hours 1 --center-url http://localhost:8000
  ```
  - Expected: ≥3 shared signal_ids, all within ±5% tolerance
  - Output must include: count, min, max, avg, stddev per signal

- [ ] **9.5** Document comparison results
  - CSV output saved to `edge-v2/data/comparison_$(date).csv`
  - Screenshot or terminal output captured in report

### Task 3: Pre-Switch Health Check

- [ ] **9.6** Verify all services healthy
  ```bash
  # v1 running
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001  # expect 200
  # v2 Docker running
  curl -s http://localhost:8011/api/status  # expect running, healthy
  # Center healthy
  curl -s http://localhost:8000/health  # expect 200
  ```

- [ ] **9.7** Verify backlog cleared
  - v2 sync backlog should be < 50 (actively flushing to Center)

### Task 4: Switch Plan (DRY-RUN ONLY)

- [ ] **9.8** Review migration runbook Phase 4-6
  - Verify all commands are correct against current VPS state
  - Update any outdated paths or service names
  - Mark runbook as "READY FOR SA REVIEW" (still not active)

- [ ] **9.9** Document switch timeline
  - Estimated switch window: 5 minutes
  - Rollback time: < 60 seconds
  - Expected data gap: < 30 seconds

### Task 5: Final Evidence Report

- [ ] **9.10** Update `docs/reports/edge-v2-production-readiness.md`
  - Add comparison results table
  - Update Gate 3 status with evidence
  - Update recommendation based on comparison outcome

### Task 6: Commit & Push

- [ ] **9.11** Commit all changes with comparison evidence
- [ ] **9.12** Push to GitHub for SA final review

---

## Files to Create/Update

```
docs/reports/edge-v2-production-readiness.md  — update with comparison evidence
docs/runbooks/edge-v1-to-v2-migration.md       — review Phase 4-6, update commands
edge-v2/data/                                  — comparison CSV output
```

---

## Acceptance Criteria

```text
✅ EDGEV2-DEMO has ≥3 signals matching DEMO-PLANT
✅ Side-by-side comparison: ≥3 shared signal_ids
✅ All shared signals within ±5% tolerance
✅ v2 sync backlog < 50
✅ All services healthy (v1, v2, Center)
✅ Migration runbook reviewed for current VPS state
✅ Switch plan documented with timeline
✅ Final report updated with comparison evidence
✅ 0 P0/P1 open
```

## Red Flags

- STOP if: any shared signal exceeds ±5% tolerance
- STOP if: v2 backlog > 100 for > 5 minutes
- STOP if: v1 affected by any v2 operation
- STOP if: comparison returns 0 shared signals after seeding
