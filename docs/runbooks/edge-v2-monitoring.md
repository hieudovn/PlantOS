# Edge v2 Monitoring Runbook

> **Edge v2 Version:** E2V2-11
> **Last Updated:** 2026-07-09
> **Constraint:** Edge v1 remains PRIMARY. Edge v2 is mirror/secondary candidate.

## Overview

This runbook defines monitoring thresholds and alert responses for Edge v2 during extended pilot and production operation.

---

## Alert Thresholds

| Metric | Warning | Critical | Response |
|---|---|---|---|
| Heartbeat stale | > 30s since last heartbeat | > 60s since last heartbeat | Check v2 container → restart if needed |
| Sync backlog | > 100 | > 500 | Check Center connectivity, check v2 buffer |
| Sync failure rate | > 2% over 5 min | > 5% over 5 min | Check auth token, check Center ingest endpoint |
| Connector disconnected | Any connector disconnected > 60s | Any connector disconnected > 5 min | Check source availability, check connector config |
| Container restart | > 1 restart in 1 hour | > 3 restarts in 1 hour | Crash loop — investigate logs, escalate |
| DuckDB growth | > 500MB | > 1GB | Check backlog drain, consider buffer cleanup |
| Disk usage | > 80% | > 90% | Clean old comparison CSVs, check data retention |
| JWT refresh failure | 1 failure | > 3 consecutive failures | Check Center auth endpoint, check credentials |
| CPU usage | > 50% sustained | > 80% sustained | Check connector load, check processing engine |
| Memory usage | > 200MB | > 500MB | Check for memory leak, restart container |
| Data quality drop | > 3% deviation | > 5% deviation | Trigger rollback (see rollback runbook) |

---

## Monitoring Commands

### Quick Health Check

```bash
# One-liner health summary
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001) | v2: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;s=json.load(sys.stdin);print(f\"{s.get(\"status\")} bl={s.get(\"sync\",{}).get(\"backlog\",\"?\")}\")') | Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
```

### Detailed v2 Status

```bash
python3 -c "
import httpx, json

# v2 agent status
r = httpx.get('http://localhost:8011/api/status', timeout=10)
s = json.loads(r.text)

print('=== Edge v2 Status ===')
print(f'Status:       {s.get(\"status\")}')
print(f'Edge Node ID: {s.get(\"edge_node_id\")}')
print(f'Uptime:       {s.get(\"uptime\",\"?\")}')

# Sync
sync = s.get('sync',{})
print()
print('--- Sync ---')
print(f'Backlog:    {sync.get(\"backlog\",\"?\")}')
print(f'Last sync:  {sync.get(\"last_sync\",\"?\")}')
print(f'Sync OK:    {sync.get(\"ok\",\"?\")}')
print(f'Sync fail:  {sync.get(\"fail\",\"?\")}')

# Buffer
buf = s.get('buffer',{})
print()
print('--- Buffer ---')
print(f'Rows:    {buf.get(\"rows\",\"?\")}')
print(f'Size:    {buf.get(\"size_mb\",\"?\")}MB')

# Connectors
conns = s.get('connectors',{})
print()
print(f'--- Connectors ({len(conns)}) ---')
for c_id, c_info in conns.items():
    print(f'  {c_id}: {c_info.get(\"status\",\"?\")} (connected={c_info.get(\"connected\",\"?\")})')
"
```

### Container Resource Usage

```bash
docker stats plantos-edge-v2 --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
```

### Disk Usage

```bash
du -sh /opt/plantos/edge-v2/data/
du -sm /opt/plantos/edge-v2/data/*.duckdb 2>/dev/null
ls -la /opt/plantos/edge-v2/data/*.csv 2>/dev/null | wc -l
```

### JWT Token Health

```bash
python3 -c "
import httpx, os
api = 'http://localhost:8000/api/v1'
pw = os.environ.get('PLANTOS_CENTER_PASSWORD','')
r = httpx.post(f'{api}/auth/login', json={'username':'admin','password':pw}, timeout=10)
if r.status_code == 200:
    t = r.json().get('access_token','')
    print(f'JWT: OK (token: {t[:20]}...)')
    # Test authenticated request
    r2 = httpx.get(f'{api}/plants', headers={'Authorization': f'Bearer {t}'}, timeout=10)
    print(f'Auth API: HTTP {r2.status_code}')
else:
    print(f'JWT: FAIL ({r.status_code})')
"
```

### Heartbeat Check

```bash
python3 -c "
import httpx, json
r = httpx.get('http://localhost:8000/api/v1/edge-nodes', timeout=10)
for n in r.json() if isinstance(r.json(), list) else []:
    print(f'{n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")} (last: {n.get(\"last_heartbeat\",\"?\")})')
"
```

### Comparison Check

```bash
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current
```

---

## Soak Test Monitoring (E2V2-11B)

During extended pilot, run the soak monitor:

```bash
nohup /tmp/soak_monitor.sh 240 > /tmp/soak_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

Check progress:

```bash
tail -f /opt/plantos/edge-v2/data/soak_*.csv
```

Analyze results:

```bash
python3 -c "
import csv
from glob import glob
files = sorted(glob('/opt/plantos/edge-v2/data/soak_*.csv'))
if not files: exit(0)
with open(files[-1]) as f:
    r = list(csv.DictReader(f))
print(f'Data points: {len(r)}')
print(f'Period: {r[0][\"timestamp\"]} → {r[-1][\"timestamp\"]}')
# Check for errors
errs = [x for x in r if x['v1_code']!='200' or x['center_code']!='200']
print(f'Errors: {len(errs)}')
# Resource trend
cpus = [float(x['cpu_pct']) for x in r if x['cpu_pct'] not in ('','?')]
mems = [float(x['mem_mb']) for x in r if x['mem_mb'] not in ('','?')]
if cpus: print(f'CPU: {min(cpus):.1f}-{max(cpus):.1f}%')
if mems: print(f'Mem: {min(mems):.0f}-{max(mems):.0f}MB')
"
```

---

## Alert Response Procedures

### Heartbeat Stale

1. Check v2 container: `docker ps --filter name=plantos-edge-v2`
2. Check v2 logs: `docker logs plantos-edge-v2 --tail 50`
3. If container stopped: `docker start plantos-edge-v2`
4. If unhealthy: `docker restart plantos-edge-v2`
5. Escalate if restart doesn't resolve

### Connector Disconnected

1. Check source availability (simulator, OPC UA server, MQTT broker)
2. Check v2 connector config: `curl -s http://localhost:8011/api/status | python3 -m json.tool`
3. If config issue: reload config via poller
   ```bash
   docker compose -f /opt/plantos/deployment/docker-compose.yml exec plantos-edge-v2 python /app/agent/commands/poller.py --action reload_config
   ```
4. If persistent: restart connector
   ```bash
   docker compose -f /opt/plantos/deployment/docker-compose.yml exec plantos-edge-v2 python /app/agent/commands/poller.py --action restart_connector --connector-id <id>
   ```

### Backlog Growing

1. Check Center health: `curl http://localhost:8000/health`
2. Check sync logs: `docker logs plantos-edge-v2 --tail 30 | grep -i sync`
3. If Center offline: backlog will drain automatically when Center recovers
4. If backlog > 1000 and climbing: check for sync errors

### Container Crash Loop

1. Check restart count: `docker inspect plantos-edge-v2 --format '{{.RestartCount}}'`
2. Check logs: `docker logs plantos-edge-v2 --tail 100`
3. If crash loop: stop container, investigate logs, fix config, restart
4. Rollback to v1 if needed (see rollback runbook)

### Data Quality Degradation

1. Run comparison tool to check deviation
2. If deviation > 5%: trigger rollback immediately (see rollback runbook)
3. Document deviation cause before re-attempting v2 operation

---

## Dashboard Queries

### PostgreSQL (Center)

```sql
-- Check edge node health
SELECT edge_node_id, status, last_heartbeat FROM edge_nodes;

-- Check v2 heartbeat timeliness
SELECT edge_node_id, status,
  EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) AS seconds_since_heartbeat
FROM edge_nodes
WHERE edge_node_id = 'EDGEV2-PC-01';
```

### V2 Agent API

```bash
# Health endpoint (JSON)
curl -s http://localhost:8011/api/status | python3 -m json.tool

# Metrics endpoint (if available)
curl -s http://localhost:8011/api/metrics
```

---

## Appendix: Quick Reference

```bash
# Health summary
alias v2health='echo "v1=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001) v2=$(curl -s http://localhost:8011/api/status | python3 -c "import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))") center=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)"'

# Check backlog
alias v2backlog='curl -s http://localhost:8011/api/status | python3 -c "import sys,json;print(json.load(sys.stdin).get(\"sync\",{}).get(\"backlog\",\"?\"))"'

# View logs
alias v2logs='docker logs plantos-edge-v2 --tail 50 -f'

# Restart v2
alias v2restart='docker restart plantos-edge-v2'
```
