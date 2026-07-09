# E2V2-12: Limited Production Switch Execution

> **SA Gate:** ✅ CONDITIONALLY APPROVED — GO FOR LIMITED PRODUCTION SWITCH (3 signals, waiver)
> **Parent Report:** `docs/reports/edge-v2-production-readiness.md`
> **Constraint:** Edge v1 PRIMARY. 3-signal switch only. No broad rollout.

## Context

SA reviewed the final evidence package and conditionally approved a limited production switch for 3 runtime-verified signals. WAIVER accepted for >=15 signal gate. This is the first production switch of Edge v2 — scope is strictly limited.

---

## Switch Scope

```
Signals:    PUMP-101.flow_rate, PUMP-101.discharge_pressure, MOTOR-101.motor_current
Workspace:  EDGEV2-DEMO
Edge v1:    Remains running on DEMO-PLANT as PRIMARY/fallback
Monitor:    60-120 minutes minimum post-switch
```

---

## Non-Negotiable Rules

```text
1. DO NOT stop Edge v1.
2. DO NOT migrate beyond 3 signals.
3. DO NOT claim full production readiness.
4. DO NOT expand protocol/features.
5. Rollback immediately if any threshold breached.
```

---

## Execution Checklist

### Phase 1: Pre-Switch Verification

- [ ] **12.1** Confirm Edge v1 health
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001  # expect 200
  ```

- [ ] **12.2** Confirm Edge v2 health
  ```bash
  curl -s http://localhost:8011/api/status  # expect status=running
  ```

- [ ] **12.3** Confirm Center health
  ```bash
  curl -s http://localhost:8000/health  # expect healthy
  ```

- [ ] **12.4** Confirm heartbeat OK
  ```bash
  docker logs plantos-edge-v2 2>&1 | grep heartbeat | tail -3  # expect 200 OK
  ```

- [ ] **12.5** Confirm ingest OK
  ```bash
  docker logs plantos-edge-v2 2>&1 | grep "Flushed" | tail -3  # expect Flushed N/10
  ```

- [ ] **12.6** Record baseline
  ```bash
  echo "=== BASELINE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  curl -s http://localhost:8011/api/status  # record buffer, backlog
  ```

### Phase 2: Limited Production Switch

- [ ] **12.7** Execute switch (v2 becomes primary data path for 3 signals)
  - v2 already running and syncing — this is a "declare primary" step
  - Confirm v2 heartbeat shows EDGEV2-PC-01 online
  - Confirm v2 data reaching Center for EDGEV2-DEMO workspace

- [ ] **12.8** Verify no disruption to v1
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001  # must be 200
  ```

### Phase 3: Post-Switch Monitoring (60-120 minutes)

Record every 15 minutes:

- [ ] **12.9** Monitor heartbeat status (every 15 min)
- [ ] **12.10** Monitor ingest status (every 15 min)
- [ ] **12.11** Monitor missing rate (< 2%)
- [ ] **12.12** Monitor duplicate count (must be 0)
- [ ] **12.13** Monitor GOOD quality rate (> 95%)
- [ ] **12.14** Monitor backlog (must be stable/decreasing)
- [ ] **12.15** Monitor CPU/memory (no sustained spikes or leaks)
- [ ] **12.16** Monitor v1 fallback health (must remain 200)

### Phase 4: Post-Switch Comparison

- [ ] **12.17** Run comparison at end of monitoring period
  ```bash
  python3 /opt/plantos/tools/compare_v1_v2_data.py \
    --hours 2 --center-url http://localhost:8000 \
    --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current
  ```
  - Expected: 3/3 PASS, diff within ±5%

### Phase 5: Post-Switch Report

- [ ] **12.18** Produce monitoring summary with all tracked metrics
- [ ] **12.19** Confirm rollback readiness (v1 still running, runbook accessible)
- [ ] **12.20** Recommend E2V2-13 or rollback

---

## Immediate Rollback Triggers

Execute rollback runbook immediately if:

| Trigger | Threshold |
|---|---|
| Heartbeat failure | Persistent > 60s |
| Ingest failure | Persistent > 2% failure rate |
| Missing rate | > 2% |
| Duplicate count | > 0 |
| Backlog growth | Continuous > 5 minutes |
| CPU/memory | Unstable or leak detected |
| Data diff | Exceeds ±5% tolerance |
| v1 affected | Any change in v1 health |

## Rollback Procedure

```bash
# 1. v2 is secondary again — v1 is PRIMARY
# 2. Stop v2 (if needed): docker stop plantos-edge-v2
# 3. Verify v1: curl localhost:8001 → 200
# 4. Document incident
# Rollback time: < 60 seconds
```

---

## Evidence to Collect

```
- Pre-switch baseline (timestamp, v1/v2/Center status, backlog)
- 60-120 min monitoring log (every 15 min)
- Post-switch comparison CSV
- Rollback readiness confirmation
```

## Files to Update

```
docs/reports/edge-v2-production-readiness.md  — add E2V2-12 results
```

## Red Flags

- STOP if: any rollback trigger fires
- STOP if: v1 is affected in any way
- STOP if: Center shows data corruption or duplicates
- STOP if: comparison shows any deviation > 5%
