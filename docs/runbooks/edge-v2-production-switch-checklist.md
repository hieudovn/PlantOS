# Production Switch Checklist: Edge v1 → Edge v2

> **⚠️ DO NOT EXECUTE without SA approval.**
> Edge v1 remains PRIMARY until SA explicitly approves GO FOR LIMITED PRODUCTION SWITCH.
> This checklist is for execution by an operator following SA approval.

---

## Pre-Switch Checklist

Run this 24 hours before planned switch window.

- [ ] **P1** Verify all services healthy
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001   # v1 → 200
  curl -s http://localhost:8011/api/status                       # v2 → running
  curl -s http://localhost:8000/health                           # Center → 200
  ```

- [ ] **P2** Verify comparison within tolerance
  ```bash
  python3 /opt/plantos/tools/compare_v1_v2_data.py --hours 1 --center-url http://localhost:8000
  # Expected: all PASS, no FAIL
  ```

- [ ] **P3** Verify backlog stable
  ```bash
  curl -s http://localhost:8011/api/status | python3 -c "import sys,json;print(json.load(sys.stdin).get('sync',{}).get('backlog','?'))"
  # Expected: < 50
  ```

- [ ] **P4** Verify soak test completed without degradation
  - No memory leak (>50MB growth)
  - No crash loop
  - No persistent sync failure

- [ ] **P5** Verify rollback runbook is printed and accessible
  - Location: `docs/runbooks/edge-v1-to-v2-rollback.md`
  - Verified during E2V2-10 dry-run

- [ ] **P6** Verify monitoring is set up
  - `docs/runbooks/edge-v2-monitoring.md` reviewed
  - Alert thresholds configured
  - Health check commands tested

- [ ] **P7** Record baseline metrics
  ```bash
  echo "=== BASELINE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
  echo "v2 backlog: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"sync\",{}).get(\"backlog\",\"?\"))')"
  echo "v2 uptime: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"uptime\",\"?\"))')"
  ```

- [ ] **P8** Notify affected teams
  - Operations team: switch window, expected impact, rollback plan
  - SA: switch window confirmation
  - Center team: monitoring during switch

---

## During-Switch Checklist

Switch window: **5 minutes**. Execute during low-impact period.

- [ ] **D1** Announce switch start
  ```bash
  echo "=== SWITCH START $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  ```

- [ ] **D2** Verify v2 is ready
  ```bash
  curl -s http://localhost:8011/api/status | python3 -c "import sys,json;s=json.load(sys.stdin);print(f'status={s.get(\"status\")} backlog={s.get(\"sync\",{}).get(\"backlog\",\"?\")}')"
  ```

- [ ] **D3** Configure Center to read from EDGEV2-DEMO
  *(Actual command depends on Center configuration mechanism — update workspace binding)*
  ```bash
  # TODO: Center API call or config change to point primary reads to EDGEV2-DEMO
  echo "Updating Center workspace binding..."
  ```

- [ ] **D4** Verify Center data source switch
  ```bash
  # Verify Center reads from EDGEV2-DEMO
  curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=1"
  ```

- [ ] **D5** Verify v1 still running (fallback)
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001
  ```

- [ ] **D6** Verify v2 heartbeating
  ```bash
  curl -s http://localhost:8000/api/v1/edge-nodes | python3 -c "import sys,json;[print(f'{n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}') for n in json.load(sys.stdin) if isinstance(json.load(sys.stdin),list) else []"
  ```

- [ ] **D7** Record switch time
  ```bash
  echo "=== SWITCH COMPLETE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  ```

---

## Post-Switch Checklist

Run for 24 hours after switch. Edge v1 remains running as fallback.

- [ ] **O1** Verify data flowing (every 5 min for first hour, then hourly)
  ```bash
  curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=1" | python3 -c "import sys,json;print('Data flowing' if len(json.load(sys.stdin))>0 else 'NO DATA')"
  ```

- [ ] **O2** Check backlog (every 5 min for first hour)
  ```bash
  curl -s http://localhost:8011/api/status | python3 -c "import sys,json;print(json.load(sys.stdin).get('sync',{}).get('backlog','?'))"
  ```

- [ ] **O3** Run comparison (at 1h, 4h, 12h, 24h post-switch)
  ```bash
  python3 /opt/plantos/tools/compare_v1_v2_data.py --hours 1 --center-url http://localhost:8000
  ```

- [ ] **O4** Monitor resource usage
  ```bash
  docker stats plantos-edge-v2 --no-stream
  du -sh /opt/plantos/edge-v2/data/
  ```

- [ ] **O5** Verify v1 fallback still healthy
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001
  ```

- [ ] **O6** Document any anomalies
  - Timestamp: _____
  - Issue: _____
  - Action: _____
  - Resolution: _____

---

## Rollback Triggers

Execute rollback runbook immediately if any trigger fires.

| Severity | Trigger | Action |
|---|---|---|
| 🔴 Critical | Data quality drop >5% | Immediate rollback |
| 🔴 Critical | Sync failure >5% of attempts | Immediate rollback |
| 🟡 Warning | Backlog > 1000 and climbing | Evaluate, prepare rollback |
| 🟡 Warning | Heartbeat loss > 60s | Evaluate, prepare rollback |
| 🔴 Critical | v2 container crash loop | Immediate rollback |
| 🔴 Critical | v1 affected by switch | Immediate rollback |

---

## Rollback Procedure (Quick Reference)

Full details: `docs/runbooks/edge-v1-to-v2-rollback.md`

```bash
# 1. Stop Edge v2
docker compose -f /opt/plantos/deployment/docker-compose.yml stop plantos-edge-v2 2>/dev/null || docker stop plantos-edge-v2

# 2. Verify v1 still running
curl http://localhost:8001

# 3. Revert Center config to read from DEMO-PLANT
# TODO: Center API call to revert workspace binding

# 4. Verify data flow from v1
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=1"

# 5. Record data gap
echo "Rollback complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

---

## Support Bundle

If escalation is needed, collect:

```bash
SUPPORT_DIR="/tmp/plantos-support-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SUPPORT_DIR"

# v2 logs
docker logs plantos-edge-v2 --tail 200 > "$SUPPORT_DIR/v2-logs.txt"

# v2 status
curl -s http://localhost:8011/api/status > "$SUPPORT_DIR/v2-status.json"

# Center health
curl -s http://localhost:8000/health > "$SUPPORT_DIR/center-health.json"

# Edge nodes
curl -s http://localhost:8000/api/v1/edge-nodes > "$SUPPORT_DIR/edge-nodes.json"

# Container metrics
docker inspect plantos-edge-v2 > "$SUPPORT_DIR/container-inspect.json"

# Disk usage
du -sh /opt/plantos/edge-v2/data/ > "$SUPPORT_DIR/disk-usage.txt"

# System resources
free -h > "$SUPPORT_DIR/memory.txt"
df -h > "$SUPPORT_DIR/disk.txt"
uptime > "$SUPPORT_DIR/uptime.txt"

tar czf "${SUPPORT_DIR}.tar.gz" -C /tmp "$(basename $SUPPORT_DIR)"
echo "Support bundle: ${SUPPORT_DIR}.tar.gz"
```

---

## Switch Timeline

| Phase | Duration | Cumulative |
|---|---|---|
| Pre-switch checks | 30 min | 30 min |
| Center config change | 2 min | 32 min |
| Verify data flow | 5 min | 37 min |
| Monitoring period | 24 hours | 24h 37 min |
| Post-switch verification | 1 hour | 25h 37 min |
| **Total** | **~26 hours** | |

---

## Approval Sign-Off

| Role | Name | Signature | Date |
|---|---|---|---|
| PM | | | |
| SA | | | |
| Operations | | | |
| Center Team | | | |
