# E2V2-11: Extended Pilot & Production Switch Preparation

> **Current Status:** E2V2-10 DRY-RUN PASSED. NOT production switch ready.
> **Parent Report:** `docs/reports/edge-v2-production-readiness.md`
> **Constraint:** Edge v1 PRIMARY. No production cutover until SA approves.

---

## Context

E2V2-10 limited controlled switch dry-run passed (4/4 tasks, 3/3 comparison, 0.0% diff). The next phase is Extended Pilot to prove Edge v2 can safely become the primary runtime for a defined production subset. Production switch requires all necessary (N1-N6) and sufficient (S1-S6) conditions.

---

## Non-Negotiable Constraints

```text
1. Edge v1 remains PRIMARY.
2. Edge v1 must not be stopped.
3. Edge v2 may run as mirror/secondary candidate.
4. No full production cutover.
5. No broad signal/plant migration.
6. No new protocol/feature expansion.
7. No destructive action without safety gate.
8. Rollback path must remain available at all times.
```

---

## Necessary Conditions (Pre-Switch Baseline)

These must be true before switch can be considered:

- [ ] **N1** Open P0 = 0, Open P1 = 0, no unresolved security/data/rollback blockers
- [ ] **N2** Edge v1 healthy (200), data path available, rollback tested
- [ ] **N3** Edge v2 healthy, connectors connected, buffer OK, sync active, no crash loop
- [ ] **N4** Center integration: heartbeat 200, ingest 200, JWT refresh works, backlog drains
- [ ] **N5** Security: no hardcoded creds, non-root container, session_secret enforced, safety gates
- [ ] **N6** Evidence discipline: every PASS claim has command + timestamp + output

---

## Sufficient Conditions (5 Sub-Phases)

### E2V2-11A — Expand Signal Coverage

**Objective:** Move from 3-signal proof to 15+ signals.

- [ ] **11A.1** Confirm 15 shared signals exist in DEMO-PLANT and EDGEV2-DEMO
- [ ] **11A.2** Run v1/v2 side-by-side for minimum 4 hours (preferred 8-12h)
- [ ] **11A.3** Produce comparison CSV with all 15 signals
- [ ] **11A.4** Verify metrics:
  - Missing rate < 2%
  - Duplicate count = 0
  - GOOD quality rate > 95%
  - Value delta within tolerance per signal
  - Timestamp drift < 5s (or justified if N/A)
  - Backlog stable or decreasing

### E2V2-11B — Extended Soak Test

**Objective:** Prove Edge v2 runs stably for extended period.

- [ ] **11B.1** Run Edge v2 container continuously (minimum 4h, preferred 8-12h)
- [ ] **11B.2** Record health every 5-15 minutes
- [ ] **11B.3** Track: CPU, memory, disk, DuckDB size, buffer rows, backlog
- [ ] **11B.4** Track: connector status, JWT refresh, sync success/failure, heartbeat
- [ ] **11B.5** Verify: no memory leak, no crash loop, no uncontrolled disk growth, no persistent sync failure

### E2V2-11C — Failure-Mode Validation

**Objective:** Prove Edge v2 behaves safely under imperfect conditions.

- [ ] **11C.1** Center offline 10-30 minutes → backlog grows → Center restored → backlog drains
- [ ] **11C.2** Edge v2 container restart → recovers healthy
- [ ] **11C.3** JWT token refresh (wait for or force expiry window)
- [ ] **11C.4** Source/simulator unavailable → connector degrades gracefully (not crash)
- [ ] **11C.5** Invalid connector config applied → rejected with clear error
- [ ] **11C.6** Rollback verified after all failure tests

### E2V2-11D — Operational Readiness Pack

**Objective:** Ensure operators can safely run and recover Edge v2.

- [ ] **11D.1** Review `docs/runbooks/edge-v1-to-v2-migration.md` (all phases, commands verified)
- [ ] **11D.2** Review `docs/runbooks/edge-v1-to-v2-rollback.md` (all steps, recovery verified)
- [ ] **11D.3** Create `docs/runbooks/edge-v2-monitoring.md` with alert thresholds:
  - heartbeat stale, backlog warning/critical, sync failure, connector disconnected, disk usage, JWT refresh failure, container restart
- [ ] **11D.4** Create `docs/runbooks/edge-v2-production-switch-checklist.md`:
  - Pre-switch, during-switch, post-switch, rollback, monitoring, support bundle

### E2V2-11E — Final Switch Readiness Report

**Objective:** Submit contradiction-free report for SA production switch decision.

- [ ] **11E.1** Fill production switch approval matrix (all gates + thresholds + results)
- [ ] **11E.2** Document production switch scope (signals, workspace, assets, time window, rollback)
- [ ] **11E.3** PM self-verification: no contradictions, all PASS has evidence, precise language
- [ ] **11E.4** Recommendation: one of NO-GO / CONDITIONAL GO FOR MORE PILOT / GO FOR LIMITED PRODUCTION SWITCH

---

## Production Switch Approval Matrix

PM must fill this before SA review:

| Gate | Threshold | Result | Evidence | PASS/FAIL |
|---|---|---|---|---|
| Open P0 | 0 | | | |
| Open P1 | 0 | | | |
| Edge v1 fallback | healthy | | | |
| Edge v2 health | healthy | | | |
| Center health | healthy | | | |
| Heartbeat | 200 OK | | | |
| Measurement ingest | 200 OK | | | |
| Shared signals | >= 15 | | | |
| Comparison window | >= 4h (pref 8-12h) | | | |
| Missing rate | < 2% | | | |
| Duplicate count | 0 | | | |
| GOOD quality rate | > 95% | | | |
| Backlog | stable/decreasing | | | |
| Soak test | >= 4h (pref 8-12h) | | | |
| Center offline recovery | PASS | | | |
| Container restart recovery | PASS | | | |
| JWT refresh | PASS | | | |
| Rollback time | < 60s | | | |
| Data gap | < 30s | | | |
| Docker non-root | PASS | | | |
| Migration runbook | ready | | | |
| Rollback runbook | ready | | | |
| Monitoring checklist | ready | | | |

---

## Files to Create

```
docs/runbooks/edge-v2-monitoring.md
docs/runbooks/edge-v2-production-switch-checklist.md
docs/reports/edge-v2-e2v2-11-extended-pilot.md
```

## Files to Update

```
docs/reports/edge-v2-production-readiness.md  — add E2V2-11 results
docs/runbooks/edge-v1-to-v2-migration.md       — update dry-run results
```

---

## Red Flags

- STOP if: Edge v1 is affected in any way
- STOP if: any P0/P1 is open
- STOP if: comparison shows any signal > tolerance
- STOP if: soak test shows crash loop or memory leak
- STOP if: rollback fails after any test
- STOP if: production switch is claimed before SA approval

## Definition of Done

```
Production switch readiness achieved only when:
1. All necessary conditions N1-N6 satisfied.
2. All sufficient conditions S1-S6 satisfied.
3. Final approval matrix complete.
4. PM self-verification passes.
5. SA receives contradiction-free report.
6. SA explicitly approves GO FOR LIMITED PRODUCTION SWITCH.
```
