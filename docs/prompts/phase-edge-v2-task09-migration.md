# E2V2-7: Controlled Migration Preparation (SA Conditionally Approved)

> **SA Gate:** ✅ CONDITIONALLY APPROVED 2026-07-09
> **Constraint:** Do NOT disable Edge v1. Mirror-first. Docker smoke pending.
> **See:** `docs/reports/edge-v2-stab-final-sa-review.md`

## Context

Edge v2 passed Data E2E + Command E2E on VPS (103.97.132.249). SA approved preparation for controlled migration with constraints:
- Edge v1 remains PRIMARY. Edge v2 runs as MIRROR only.
- No production switch. No deprecation of v1.
- Docker smoke pending (blocked by Docker Hub TLS on VPS, code ready).
- Rollback must be tested before any switch decision.

## Plan References

- `docs/phase-edge-v2-productization-plan.md` §16, §18 (E2V2-7)
- `docs/reports/edge-v2-stab-final-sa-review.md` — SA decision
- `docs/runbooks/` — migration + rollback runbooks (to be created)

## Constitution Checklist

- [x] Edge v1 must remain PRIMARY — do NOT stop, disable, or deprecate
- [x] Edge v2 runs as mirror/sidecar only against EDGEV2-DEMO workspace
- [x] No data loss — v1 continues publishing to its own workspace
- [x] Rollback path must exist and be tested (dry-run only)
- [x] All changes documented

---

## SA Constraints (READ CAREFULLY)

```text
1. DO NOT disable, stop, or deprecate Edge v1.
2. DO NOT claim Docker/package readiness (blocked by infra).
3. DO NOT switch any production workspace to Edge v2.
4. Migration = mirror-first: v2 mirrors v1 signals, publishes to separate workspace.
5. Rollback runbook must be tested via dry-run only.
6. Docker smoke can be verified on another environment if VPS blocked.
```

---

## Implementation Checklist (12 tasks)

### Phase A: Docker Smoke (when infra allows)

- [ ] **7.0** Attempt Docker smoke on VPS or alternative environment:
  ```bash
  docker compose -f edge-v2/docker-compose.edge-v2.yml up -d --build
  ```
  - If VPS Docker Hub still blocked: try local Windows Docker or another Linux host
  - Verify Edge v2 starts, health endpoint responds, DuckDB created
  - If all environments blocked: document status and skip (not a code issue)
  - **Red flag:** Do NOT claim Docker readiness even if smoke passes locally.
    Production Docker approval requires SA re-review after infra restored.

### Phase B: Mirror Configuration  

- [ ] **7.1** Create mirror config for WTP-DEMO-01 signals:
  - Read Edge v1 config (`edge/agent/config.yaml`) signals section
  - Translate to Edge v2 connector format (`edge-v2/config/edge_config.yaml`)
  - Use v2's HTTP Poll connector to mirror v1's simulator signals
  - Signal IDs MUST be identical to v1 (e.g., `PUMP-101.flow_rate`)
  - Workspace: `EDGEV2-DEMO` (NOT `WTP-DEMO-01`)
  - Plant ID: `EDGEV2-DEMO`
  - Edge node ID: `EDGEV2-PC-01`

- [ ] **7.2** Create mirror config for VF-DEMO signals:
  - Same approach as 7.1 but for VF compressor signals
  - Map v1 OPC UA tags → v2 OPC UA connector config
  - Keep identical signal_ids, scale factors, polling intervals
  - Workspace: `EDGEV2-DEMO`

- [ ] **7.3** Create config migration utility (`tools/migrate_v1_config_to_v2.py`):
  - Reads `edge/agent/config.yaml`
  - Outputs equivalent Edge v2 `edge-v2/config/edge_config.yaml` sections
  - Handles: signals → connectors, mqtt → mqtt connector, opcua → opcua connector
  - Reports unmappable fields (e.g., v1-only features)
  - Dry-run mode: prints what WOULD be generated

### Phase C: Side-by-Side Comparison

- [ ] **7.4** Run side-by-side for minimum 1 hour (VPS):
  - Edge v1 → WTP-DEMO-01 workspace (unchanged)
  - Edge v2 → EDGEV2-DEMO workspace (mirror signals)
  - Collect comparison metrics:
    - Value accuracy (v1 raw vs v2 raw for same signal_id)
    - Timestamp accuracy (within 2s tolerance)
    - Data point count (v1 vs v2 per signal per minute)
    - Backlog behavior during normal operation

- [ ] **7.5** Create comparison script (`tools/compare_v1_v2_data.py`):
  - Queries Center PostgreSQL: measurements for WTP-DEMO-01 vs EDGEV2-DEMO
  - For matching signal_ids, compares: count, min, max, avg, stddev
  - Output: CSV report + console summary
  - Acceptable tolerance: ±5% for simulated signals, ±1% for real tags

- [ ] **7.6** Simulate Center offline during comparison:
  - Stop Center backend for 5 minutes
  - Verify both v1 and v2 buffer correctly (DuckDB backlog grows)
  - Restore Center
  - Verify both flush backlog without duplicates
  - Compare backlog flush time: v2 ≤ v1

### Phase D: Runbooks

- [ ] **7.7** Create migration runbook (`docs/runbooks/edge-v1-to-v2-migration.md`):
  ```text
  ⚠️ NOT YET ACTIVE — SA approval required before execution
  Phases: PRE-MIGRATION → MIRROR → COMPARISON → SWITCH → VERIFY → COMMIT
  Each step has: command, expected output, rollback trigger
  ```

- [ ] **7.8** Create rollback runbook (`docs/runbooks/edge-v1-to-v2-rollback.md`):
  ```text
  Triggers: data quality drop, sync failure >5%, backlog growth, heartbeat loss
  Execute: stop v2 → start v1 → verify v1 heartbeat → verify data flow
  Recovery: check data gap, backfill if needed, notify, document
  ```

### Phase E: Dry-Run Test

- [ ] **7.9** Dry-run migration on test workspace:
  - Create test workspace `EDGEV2-TEST` with 3 assets
  - Run through full migration + rollback cycle (using runbooks)
  - Verify rollback restores v1 state with no data loss
  - Verify re-migration after rollback works

- [ ] **7.10** Rollback dry-run test:
  - Simulate v2 failure (stop Edge v2 process)
  - Execute rollback runbook
  - Verify v1 resumes within 60 seconds
  - Verify data gap < 30 seconds
  - Document results in runbook appendix

### Phase F: Documentation

- [ ] **7.11** Update `edge-v2/README.md`:
  - Add: "Edge v2 is in MIRROR mode. Edge v1 is PRIMARY."
  - Link to migration + rollback runbooks
  - Add SA conditional approval status
  - Document known limitation: Docker smoke pending

- [ ] **7.12** Create migration preparation report (`docs/reports/edge-v2-migration-prep.md`):
  - Mirror config status (WTP + VF)
  - Side-by-side comparison results
  - Dry-run test results
  - Rollback test results
  - Docker smoke status
  - Remaining gates before production switch
  - Recommendation for SA

---

## Files to Create

```
docs/runbooks/
  edge-v1-to-v2-migration.md
  edge-v1-to-v2-rollback.md
docs/reports/
  edge-v2-migration-prep.md
tools/
  migrate_v1_config_to_v2.py
  compare_v1_v2_data.py
edge-v2/
  README.md (if not exists)
```

## Files to Modify

```
edge-v2/config/edge_config.yaml — mirror WTP + VF signals (new connectors)
```

---

## Acceptance Criteria

```text
✅ Docker smoke attempted (or documented as blocked)
✅ Mirror config created for WTP-DEMO-01 and VF-DEMO signals
✅ Config migration utility works (dry-run tested)
✅ Side-by-side comparison shows equivalent data (within tolerance)
✅ Center offline simulation: both buffer and flush correctly
✅ Migration runbook written (marked NOT ACTIVE)
✅ Rollback runbook written and dry-run tested
✅ Dry-run: full cycle passes on test workspace
✅ Rollback: v1 resumes within 60s, data gap < 30s
✅ Edge v1 NEVER stopped, disabled, or deprecated during this phase
✅ Migration prep report published with SA recommendation
```

## Red Flags

- STOP if: any task attempts to stop/disable Edge v1
- STOP if: side-by-side shows data quality regression >5%
- STOP if: rollback dry-run fails to restore v1 within 60s
- STOP if: any production workspace is switched to Edge v2
- STOP if: documentation claims Docker/package readiness
