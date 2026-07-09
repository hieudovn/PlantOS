# E2V2-14: Full Production Switch — v2 → PRIMARY

> **Role:** Coder-Executioner (V4 Flash) — run on VPS (103.97.132.249)
> **Reviewer:** PM-Designer (V4 Pro)
> **Gate:** Full production switch — v2 becomes PRIMARY edge agent, v1 → cold standby
> **⚠️ CRITICAL:** This is a ONE-WAY operation. v1 will be STOPPED. Rollback exists but requires manual intervention.

---

## 1. Context

All SA gates met (16/22 RUNTIME_PASS, 0 WAIVER). E2V2-13 confirmed 19 signals with 102 PASS, 0 FAIL over 4 hours. Edge v2 is ready to become the sole edge agent.

**Current state:**
- v1: systemd `plantos-edge.service`, PID 605301, port 8001, writes to **DEMO-PLANT** workspace
- v2: Docker `plantos-edge-v2`, port 8011, writes to **EDGEV2-DEMO** workspace
- Both write to Center (port 8000), same TDengine
- 142 shared signal_ids between both workspaces

**Goal:** Stop v1, point v2 to DEMO-PLANT workspace → v2 is the sole data collector.

**How v2 plant_id works:** In `edge-v2/agent/config/__init__.py`, if `plant_id` is NOT in the YAML config file, it defaults to `EDGEV2-DEMO`. To switch, add `plant_id: DEMO-PLANT` to the config.

---

## 2. Pre-Switch Checklist

Run ALL of these before touching v1:

```bash
# 1. v1 health
systemctl status plantos-edge --no-pager | head -5
curl -s -o /dev/null -w "v1: HTTP %{http_code}\n" http://localhost:8001

# 2. v2 health
curl -s http://localhost:8011/api/status | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'v2: {d[\"status\"]}, plant={d[\"plant_id\"]}, node={d[\"edge_node_id\"]}')
cs=d['connectors']['list']
for c in cs: print(f'  {c[\"connector_id\"]}: {c[\"status\"]}, signals={c[\"signal_count\"]}')
print(f'backlog={d[\"sync\"][\"backlog\"]}, buffer={d[\"buffer\"][\"row_count\"]}')
"

# 3. Center health
curl -s -o /dev/null -w "Center: HTTP %{http_code}\n" http://localhost:8000

# 4. Simulator
curl -s http://localhost:9998/ | python3 -c "import sys,json; print(f'Simulator: {len(json.load(sys.stdin))} signals')"

# 5. JWT auth test
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin\",\"password\":\"$PLANTOS_CENTER_PASSWORD\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "JWT token: ${TOKEN:0:20}..."

# 6. Verify DEMO-PLANT signals exist
curl -s "http://localhost:8000/api/v1/signals?plant_id=DEMO-PLANT" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'DEMO-PLANT signals: {len(d) if isinstance(d,list) else len(d.get(\"data\",[]))}')"

# 7. Backup current state
echo "=== BACKUP ==="
systemctl cat plantos-edge > /tmp/e2v2-14-v1-unit-backup.txt
docker inspect plantos-edge-v2 > /tmp/e2v2-14-v2-inspect-backup.json
docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml > /tmp/e2v2-14-v2-config-backup.yaml
echo "Backups saved to /tmp/e2v2-14-*"
```

**STOP if any check fails.** v1 must be 200, v2 must be running, Center 200, Simulator 19 signals.

---

## 3. Phase 1: Stop v1

```bash
# STOP v1 — the old edge agent
sudo systemctl stop plantos-edge

# Verify stopped
sleep 2
systemctl status plantos-edge --no-pager | head -3
curl -s --connect-timeout 3 http://localhost:8001/ 2>&1 && echo "ERROR: v1 still responding!" || echo "v1: stopped OK"

# Verify port freed
ss -tlnp | grep 8001 && echo "ERROR: port 8001 still in use" || echo "Port 8001: free"
```

**Expected:**
```
● plantos-edge.service - PlantOS Edge Agent
   Loaded: loaded
   Active: inactive (dead)
v1: stopped OK
Port 8001: free
```

---

## 4. Phase 2: Reconfigure v2 → DEMO-PLANT Workspace

### Step 4.1: Create updated config

The v2 config inside Docker is at `/app/agent/config/config.edge-v2.yaml`. We need to ADD `plant_id` and `edge_node_id` to the top of the file.

```bash
# Create updated config on VPS host
cat > /tmp/config-v2-demoplant.yaml << 'YEOF'
edge_node_id: EDGEV2-PC-01
plant_id: DEMO-PLANT
api_key: plantos-edge-key-2026
auth: null
buffer:
  path: edge-v2/data/edge_data.duckdb
  retention_days: 7
center_url: http://localhost:8000
connectors:
  mirror_vf_compressor:
    connection:
      endpoint: opc.tcp://localhost:4840
    enabled: false
    tags: []
    type: opcua
  mirror_wtp_signals:
    connection:
      url: http://localhost:9998/
    enabled: true
    poll_interval_ms: 10000
    tags:
    - data_type: float
      enabled: true
      signal_id: PUMP-101.flow_rate
      source_ref: PUMP-101.flow_rate
      tag_id: PUMP-101_flow_rate
    - data_type: float
      enabled: true
      signal_id: PUMP-101.discharge_pressure
      source_ref: PUMP-101.discharge_pressure
      tag_id: PUMP-101_discharge_pressure
    - data_type: float
      enabled: true
      signal_id: PUMP-101.running_status
      source_ref: PUMP-101.running_status
      tag_id: PUMP-101_running_status
    - data_type: float
      enabled: true
      signal_id: PUMP-101.vibration_rms
      source_ref: PUMP-101.vibration_rms
      tag_id: PUMP-101_vibration_rms
    - data_type: float
      enabled: true
      signal_id: MOTOR-101.motor_current
      source_ref: MOTOR-101.motor_current
      tag_id: MOTOR-101_motor_current
    - data_type: float
      enabled: true
      signal_id: MOTOR-101.motor_temperature
      source_ref: MOTOR-101.motor_temperature
      tag_id: MOTOR-101_motor_temperature
    - data_type: float
      enabled: true
      signal_id: MOTOR-101.running_status
      source_ref: MOTOR-101.running_status
      tag_id: MOTOR-101_running_status
    - data_type: float
      enabled: true
      signal_id: TANK-101.tank_level
      source_ref: TANK-101.tank_level
      tag_id: TANK-101_tank_level
    - data_type: float
      enabled: true
      signal_id: TANK-101.temperature
      source_ref: TANK-101.temperature
      tag_id: TANK-101_temperature
    - data_type: float
      enabled: true
      signal_id: RAW-WATER-QUALITY-STATION-101.raw_turbidity
      source_ref: RAW-WATER-QUALITY-STATION-101.raw_turbidity
      tag_id: RAW-WATER-QUALITY-STATION-101_raw_turbidity
    - data_type: float
      enabled: true
      signal_id: RAW-WATER-QUALITY-STATION-101.raw_ph
      source_ref: RAW-WATER-QUALITY-STATION-101.raw_ph
      tag_id: RAW-WATER-QUALITY-STATION-101_raw_ph
    - data_type: float
      enabled: true
      signal_id: RAW-WATER-QUALITY-STATION-101.raw_temperature
      source_ref: RAW-WATER-QUALITY-STATION-101.raw_temperature
      tag_id: RAW-WATER-QUALITY-STATION-101_raw_temperature
    - data_type: float
      enabled: true
      signal_id: FILTER-101.filter_dp
      source_ref: FILTER-101.filter_dp
      tag_id: FILTER-101_filter_dp
    - data_type: float
      enabled: true
      signal_id: FILTER-101.effluent_flow
      source_ref: FILTER-101.effluent_flow
      tag_id: FILTER-101_effluent_flow
    - data_type: float
      enabled: true
      signal_id: CLEAR-WATER-TANK-101.level
      source_ref: CLEAR-WATER-TANK-101.level
      tag_id: CLEAR-WATER-TANK-101_level
    - data_type: float
      enabled: true
      signal_id: HSP-101.flow_rate
      source_ref: HSP-101.flow_rate
      tag_id: HSP-101_flow_rate
    - data_type: float
      enabled: true
      signal_id: HSP-101-MOTOR.motor_current
      source_ref: HSP-101-MOTOR.motor_current
      tag_id: HSP-101-MOTOR_motor_current
    - data_type: float
      enabled: true
      signal_id: COAG-PUMP-101.flow_rate
      source_ref: COAG-PUMP-101.flow_rate
      tag_id: COAG-PUMP-101_flow_rate
    - data_type: float
      enabled: true
      signal_id: CHLORINE-PUMP-101.flow_rate
      source_ref: CHLORINE-PUMP-101.flow_rate
      tag_id: CHLORINE-PUMP-101_flow_rate
YEOF

echo "Config file created: /tmp/config-v2-demoplant.yaml"
wc -l /tmp/config-v2-demoplant.yaml
```

**CRITICAL:** Verify the first 3 lines are exactly:
```yaml
edge_node_id: EDGEV2-PC-01
plant_id: DEMO-PLANT
api_key: plantos-edge-key-2026
```

### Step 4.2: Deploy config to Docker container

```bash
# Copy config into container
docker cp /tmp/config-v2-demoplant.yaml plantos-edge-v2:/app/agent/config/config.edge-v2.yaml

# Verify it took effect
docker exec plantos-edge-v2 head -3 /app/agent/config/config.edge-v2.yaml
```

**Expected output:**
```
edge_node_id: EDGEV2-PC-01
plant_id: DEMO-PLANT
api_key: plantos-edge-key-2026
```

### Step 4.3: Restart v2

```bash
docker restart plantos-edge-v2
echo "Waiting 15s for v2 startup..."
sleep 15
```

---

## 5. Phase 3: Post-Switch Verification

```bash
# 1. v2 status — must show plant_id=DEMO-PLANT
curl -s http://localhost:8011/api/status | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Status: {d[\"status\"]}')
print(f'Plant: {d[\"plant_id\"]}')   # MUST be DEMO-PLANT
print(f'Node: {d[\"edge_node_id\"]}') # MUST be EDGEV2-PC-01
cs=d['connectors']['list']
for c in cs: print(f'  {c[\"connector_id\"]}: {c[\"status\"]}, signals={c[\"signal_count\"]}, connected={c[\"connected\"]}')
print(f'Backlog: {d[\"sync\"][\"backlog\"]}')
print(f'Buffer: {d[\"buffer\"][\"row_count\"]}')
"

# 2. v1 must be DOWN
curl -s --connect-timeout 3 http://localhost:8001/ 2>&1 && echo "ERROR: v1 still running!" || echo "v1: DOWN ✓"

# 3. Center health
curl -s -o /dev/null -w "Center: HTTP %{http_code}\n" http://localhost:8000

# 4. Heartbeat test — wait for next cycle (~10s) then check
sleep 12
docker logs plantos-edge-v2 2>&1 | grep -E "heartbeat|Flushed|ERROR" | tail -5

# 5. Verify new data arriving in DEMO-PLANT workspace
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin\",\"password\":\"$PLANTOS_CENTER_PASSWORD\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Check latest signal data for PUMP-101.flow_rate in DEMO-PLANT
curl -s "http://localhost:8000/api/v1/measurements?signal_id=PUMP-101.flow_rate&plant_id=DEMO-PLANT&limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null | head -20
```

**Success criteria:**
- v2 status: `running`, `plant_id: DEMO-PLANT` ✅
- v2 connector: `mirror_wtp_signals=running, signal_count=19` ✅
- v1: DOWN (port 8001 closed) ✅
- Center: 200 ✅
- Heartbeat: `POST /heartbeat "HTTP/1.1 200 OK"` ✅
- Ingest: `Flushed X/10 measurements"` ✅
- Latest measurements arriving in DEMO-PLANT ✅

---

## 6. Phase 4: Monitoring (60 minutes)

```bash
cat > /tmp/e2v2-14-monitor.sh << 'MONEOF'
#!/bin/bash
# E2V2-14 Post-Switch Monitor — 4 iterations x 15 min = 60 minutes
MAX_ITER=4
OUTPUT="/opt/plantos/edge-v2/data/e2v2-14-monitor.csv"
echo "timestamp,v1_down,v2_plant,v2_status,v2_backlog,v2_buffer,connector_signals,center_code" > "$OUTPUT"

for i in $(seq 1 $MAX_ITER); do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  V1_DOWN=$(curl -s --connect-timeout 2 http://localhost:8001/ >/dev/null 2>&1 && echo "UP" || echo "DOWN")
  V2=$(curl -s http://localhost:8011/api/status)
  V2_PLANT=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['plant_id'])")
  V2_STATUS=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  V2_BL=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['sync']['backlog'])")
  V2_BUF=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['buffer']['row_count'])")
  V2_SIG=$(echo "$V2" | python3 -c "import sys,json; cs=json.load(sys.stdin)['connectors']['list']; print(sum(c['signal_count'] for c in cs if c['status']=='running'))")
  CENTER=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000)

  echo "$TS,$V1_DOWN,$V2_PLANT,$V2_STATUS,$V2_BL,$V2_BUF,$V2_SIG,$CENTER" >> "$OUTPUT"
  echo "[$TS] Iter $i/$MAX_ITER: v1=$V1_DOWN plant=$V2_PLANT v2=$V2_STATUS bl=$V2_BL buf=$V2_BUF sig=$V2_SIG center=$CENTER"

  if [ $i -lt $MAX_ITER ]; then sleep 900; fi  # 15 min
done
echo "E2V2-14 monitoring complete: $OUTPUT"
MONEOF

chmod +x /tmp/e2v2-14-monitor.sh
nohup bash /tmp/e2v2-14-monitor.sh > /tmp/e2v2-14-monitor.log 2>&1 &
echo "Monitor PID: $!"
```

---

## 7. Phase 5: Final Verification (after monitoring)

After 60 minutes:

```bash
# Run comparison — only v2 data now exists in DEMO-PLANT
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 1 \
  --center-url http://localhost:8000 \
  --v1-workspace DEMO-PLANT \
  --v2-workspace DEMO-PLANT \
  --output /opt/plantos/edge-v2/data/e2v2-14-post-switch-comparison.csv

# Check monitoring CSV
cat /opt/plantos/edge-v2/data/e2v2-14-monitor.csv

# Final status
echo "=== FINAL STATUS ==="
echo "v1: $(systemctl is-active plantos-edge 2>/dev/null || echo 'inactive')"
curl -s http://localhost:8011/api/status | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'v2: {d[\"status\"]}, plant={d[\"plant_id\"]}, backlog={d[\"sync\"][\"backlog\"]}, buffer={d[\"buffer\"][\"row_count\"]}')
cs=d['connectors']['list']
for c in cs: print(f'  {c[\"connector_id\"]}: {c[\"status\"]}, signals={c[\"signal_count\"]}')
"
```

---

## 8. Rollback Plan

If v2 fails after switch:

```bash
# Step 1: Revert v2 config to EDGEV2-DEMO
docker cp /tmp/e2v2-14-v2-config-backup.yaml plantos-edge-v2:/app/agent/config/config.edge-v2.yaml
docker restart plantos-edge-v2

# Step 2: Start v1
sudo systemctl start plantos-edge

# Step 3: Verify v1 is back
sleep 5
curl -s -o /dev/null -w "v1: HTTP %{http_code}\n" http://localhost:8001
systemctl status plantos-edge --no-pager | head -3
```

**Recovery time: < 30 seconds. Data gap: minimal (v2 buffer drains to EDGEV2-DEMO during switch-back).**

---

## 9. Expected Results

| Gate | Threshold | Expected |
|---|---|---|
| v1 stopped | inactive + port free | ✅ |
| v2 plant_id | DEMO-PLANT | ✅ |
| v2 connector | running, 19 signals | ✅ |
| Heartbeat to Center | 200 OK | ✅ |
| Data ingest to DEMO-PLANT | 200 OK | ✅ |
| 60-min monitoring | 4/4 iterations stable | ✅ |
| v1 cold standby | can be restarted if needed | ✅ |

---

## 10. Report Output

Save results to:
- `edge-v2/data/e2v2-14-monitor.csv` — monitoring data (4 iterations)
- `edge-v2/data/e2v2-14-post-switch-comparison.csv` — final comparison
- `/tmp/e2v2-14-*-backup.*` — backup files (keep on VPS)

**Do NOT modify `docs/reports/`** — PM-Designer handles that.

Report summary:
1. Did v2 successfully switch to DEMO-PLANT workspace?
2. Did data continue flowing without interruption?
3. Any errors in Docker logs?
4. Monitoring CSV summary
5. Comparison results
