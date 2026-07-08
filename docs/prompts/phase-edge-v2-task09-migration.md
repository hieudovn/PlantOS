# E2V2-7: Controlled Migration (Edge v1 → Edge v2)

## Context

After Edge v2 has been validated through all acceptance gates (E2V2-0 through E2V2-6), we can migrate selected demo workspaces from Edge v1 to Edge v2. This must be a controlled, reversible process: side-by-side comparison, blue-green switch, and documented rollback.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §16 (Migration Strategy)
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Edge v1 must remain runnable until Edge v2 stability is proven
- [x] No data loss during migration
- [x] Rollback path must exist and be tested
- [x] Workspace isolation maintained during comparison
- [x] All changes documented

## Implementation Checklist

### Side-by-Side Validation

- [ ] **7.1** Configure Edge v2 to mirror WTP-DEMO-01 signals:
  - Create matching OPC UA / Modbus tag configuration
  - Use same signal_ids as Edge v1
  - Apply equivalent processing profiles (if any)
  - Run against EDGEV2-DEMO workspace (NOT WTP-DEMO-01)

- [ ] **7.2** Configure Edge v2 to mirror VF-DEMO signals:
  - Same approach as above
  - Run against EDGEV2-DEMO workspace

- [ ] **7.3** Run side-by-side for minimum 24 hours:
  - Both Edge v1 and Edge v2 running simultaneously
  - Collect data quality metrics:
    - Value accuracy (v1 vs v2 comparison)
    - Timestamp accuracy (within 1s tolerance)
    - Missing data points
    - Backlog behavior
    - Sync latency

- [ ] **7.4** Simulate Center offline during comparison:
  - Stop Center for 5 minutes
  - Verify both v1 and v2 buffer correctly
  - Restore Center
  - Verify both flush backlog without duplicates

- [ ] **7.5** Generate comparison report:
  - Data quality: values match within tolerance
  - Timestamps: no drift
  - Backlog: v2 ≤ v1 backlog during outage
  - Sync: v2 syncs at least as fast as v1

### Migration Runbook

- [ ] **7.6** Create migration runbook (`docs/runbooks/edge-v1-to-v2-migration.md`):
  ```text
  1. PRE-MIGRATION
     - Verify Edge v1 status: running, healthy
     - Verify Edge v2 status: running against EDGEV2-DEMO, healthy
     - Backup Edge v1 config
     - Notify stakeholders

  2. SWITCH
     - Stop Edge v1 data publishing to WTP workspace
     - Start Edge v2 publishing to WTP workspace
     - Verify data flow: measurements arriving in Center
     - Verify heartbeat: WTP workspace shows Edge v2
     - Monitor for 1 hour

  3. VERIFICATION
     - Compare last v1 measurement vs first v2 measurement
     - Verify no data gap > 10 seconds
     - Verify asset/signal context intact
     - Verify Process View, Trend, Diagram, GIS all functional
     - Verify alarm rules still firing (if applicable)

  4. COMMIT
     - Mark migration as complete
     - Keep Edge v1 stopped but NOT uninstalled
     - Document new edge_node_id for WTP workspace
  ```

### Rollback Runbook

- [ ] **7.7** Create rollback runbook (`docs/runbooks/edge-v1-to-v2-rollback.md`):
  ```text
  1. TRIGGER
     - Data quality degradation detected
     - Sync failure rate > 5%
     - Backlog growing faster than v1
     - Center cannot see Edge v2 heartbeat

  2. EXECUTE
     - Stop Edge v2
     - Start Edge v1
     - Verify Edge v1 heartbeat reaches Center
     - Verify Edge v1 sync resumes
     - Verify data flow: measurements arriving

  3. RECOVERY
     - Check for data gap between v2 stop and v1 start
     - If gap < 30s: acceptable, no backfill needed
     - If gap > 30s: trigger manual sync for gap period (if available)
     - Notify stakeholders
     - Document incident

  4. POST-MORTEM
     - Analyze root cause
     - Fix Edge v2 issue
     - Re-run side-by-side comparison
     - Re-attempt migration after fix validated
  ```

### Execution

- [ ] **7.8** Execute migration for WTP-DEMO-01:
  - Follow migration runbook exactly
  - Record timestamps of each step
  - Document any deviations

- [ ] **7.9** Execute migration for VF-DEMO:
  - Follow migration runbook
  - Only after WTP-DEMO-01 is stable for 24+ hours

- [ ] **7.10** Monitor for 1 week post-migration:
  - Daily check: data flow, backlog, errors
  - Weekly comparison report

### Documentation

- [ ] **7.11** Update `edge/README.md`:
  - Add deprecation notice: "Edge v1 is deprecated. Use Edge v2."
  - Link to migration guide
  - Keep v1 run instructions for reference

- [ ] **7.12** Create migration report:
  - Summary of side-by-side comparison results
  - Migration execution log
  - Rollback test results
  - Lessons learned
  - Recommendations for future migrations

### Tests

- [ ] **7.13** Dry-run migration on test workspace:
  - Create test workspace with 3 assets
  - Run through full migration + rollback cycle
  - Verify rollback restores v1 with no data loss
  - Verify re-migration after rollback works

- [ ] **7.14** Rollback test:
  - During side-by-side, simulate v2 failure
  - Execute rollback runbook
  - Verify v1 resumes within 60 seconds
  - Verify data gap < 30 seconds

## Files to Create

```
docs/runbooks/
  edge-v1-to-v2-migration.md
  edge-v1-to-v2-rollback.md
```

## Files to Modify

```
edge/README.md — add deprecation notice
```

## Acceptance Criteria

```text
✅ Side-by-side comparison shows equivalent data quality
✅ Migration runbook is clear and tested (dry-run)
✅ Rollback runbook is clear and tested (simulated failure)
✅ WTP-DEMO-01 migrated with no data loss
✅ VF-DEMO migrated with no data loss
✅ Rollback recovers v1 within 60 seconds
✅ Edge v1 stopped but NOT uninstalled (rollback path preserved)
✅ Migration report published
✅ Edge v1 README updated with deprecation notice
```

## Red Flags

- Stop if: side-by-side comparison shows any data quality regression
- Stop if: rollback test fails to restore v1 within 60 seconds
- Stop if: migration causes any data loss in Center
- Stop if: constitution violation (Edge v1 completely removed before v2 proven stable)
