# Rollback Runbook: Edge v2 → Edge v1

> **⚠️ Execute immediately when any rollback trigger fires.**
>
> Edge v1 must resume within **60 seconds**.
> Data gap must be **< 30 seconds**.

## Rollback Triggers

| Severity | Trigger | Action |
|---|---|---|
| 🔴 Critical | Data quality drop >5% | Immediate rollback |
| 🔴 Critical | Sync failure >5% of attempts | Immediate rollback |
| 🟡 Warning | Backlog growth >1000 and climbing | Evaluate, prepare rollback |
| 🟡 Warning | Heartbeat loss >60s | Evaluate, prepare rollback |
| 🔴 Critical | Edge v2 process crash | Auto-recovery via supervisor; if fails twice → manual rollback |

---

## Rollback Procedure

### Step 1: STOP Edge v2

```bash
# systemd:
sudo systemctl stop plantos-edge-v2

# Docker:
docker compose -f edge-v2/docker-compose.edge-v2.yml stop
```

**Expected output:** Edge v2 process stopped.

---

### Step 2: VERIFY Edge v1 is still running

```bash
# v1 should still be running as primary (mirror mode):
curl http://localhost:8001

# If v1 was somehow stopped (should not happen in mirror mode):
# Docker:
docker start edge-agent-01
# Native:
cd edge && python main.py --config agent/config.yaml &
```

**Expected output:** Edge v1 running on port 8001. If v1 was never stopped, this step is a no-op.

---

### Step 3: VERIFY Edge v1 heartbeat

```bash
# Check Center:
curl -s http://localhost:8000/api/v1/edge-nodes | grep edge-agent-01

# Expected: {"edge_node_id": "edge-agent-01", "status": "online", ...}
```

**Expected output:** Edge v1 node shows as "online" within 30 seconds.

---

### Step 4: VERIFY data flow

```bash
# Check Center data (WTP or VF workspace):
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=5"

# Check v1 backlog:
# (v1 API — depends on deployment)
```

**Expected output:** Data flowing with timestamp within last 60 seconds.

---

### Step 5: RECORD data gap

```bash
# Check latest v1 vs v2 data timestamp
echo "v1 last: $(curl -s 'http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=1' | grep -oP '"timestamp":"[^"]*' | tail -1)"
echo "v2 last: $(curl -s 'http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=1' | grep -oP '"timestamp":"[^"]*' | tail -1)"

# Calculate gap in seconds
```

**Acceptance:** Gap < 30 seconds.

---

### Step 6: BACKFILL if needed

If data gap > 30 seconds, backfill from Edge v2 DuckDB:

```bash
# Dump v2 buffer for gap period
python -c "
from edge.agent.buffer import DuckDBBuffer
buffer = DuckDBBuffer('edge-v2/data/edge_data.duckdb')
rows = buffer.get_unsynced(limit=10000)
print(f'Unsynced rows: {len(rows)}')
# TODO: backfill to Center via ingest endpoint
"
```

**Expected output:** Backfill completes without errors.

---

### Step 7: NOTIFY

- Log rollback reason, timestamp, data gap
- Notify: PM, SA, operations team
- Document in runbook appendix

---

## Rollback Recovery Checklist

- [ ] Edge v1 process running (port 8001 responding)
- [ ] Edge v1 heartbeat visible in Center (`/api/v1/edge-nodes` → status="online")
- [ ] Data flowing to Center (check latest measurements)
- [ ] Data gap measured and documented
- [ ] Backfill completed (if needed)
- [ ] Rollback reason documented
- [ ] Stakeholders notified

---

## Post-Rollback Analysis

After rollback is complete, investigate root cause before re-attempting migration:

```bash
# 1. Collect Edge v2 logs
journalctl -u plantos-edge-v2 -n 200 --no-pager > /tmp/v2-rollback-logs.txt

# 2. Check v2 config
cat /etc/plantos-edge-v2/config.yaml

# 3. Check v2 buffer state
python -c "
from edge.agent.buffer import DuckDBBuffer
buffer = DuckDBBuffer('edge-v2/data/edge_data.duckdb')
print('Backlog:', buffer.count_unsynced())
"

# 4. Check system resources
free -h
df -h
uptime
```

---

## Appendix: Dry-Run Test Results

*To be filled after dry-run test:*

| Scenario | Trigger | v1 Resume Time | Data Gap | Result | Notes |
|---|---|---|---|---|---|
| v2 crash | Heartbeat loss | | | | |
| Data quality drop | >5% tolerance | | | | |
| Sync failure | >5% errors | | | | |
| Center offline | Backlog growth | | | | |
| **Full rollback** | Manual trigger | | | | |

---

## Appendix: Quick Commands

```bash
# Stop v2
sudo systemctl stop plantos-edge-v2

# Verify v1 alive
curl -s http://localhost:8001 | head -5

# Check Center heartbeat
curl -s http://localhost:8000/api/v1/edge-nodes | python -m json.tool

# Check data freshness
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=1"

# Check v2 backlog
curl -s http://localhost:8011/api/status | python -c "import sys,json; print(json.load(sys.stdin).get('sync',{}).get('backlog','?'))"
```
