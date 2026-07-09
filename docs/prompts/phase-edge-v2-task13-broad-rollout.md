# E2V2-13: Expand to 15+ Signals — Broad Rollout

> **Role:** Coder-Executioner (V4 Flash) — run on VPS (103.97.132.249)
> **Reviewer:** PM-Designer (V4 Pro)
> **SA Gate:** >=15 signals runtime-compared (currently WAIVER_REQUIRED — only 3 compared)
> **Constraint:** Edge v1 PRIMARY throughout. No production cutover. No stopping v1.

---

## 1. Context

E2V2-12 passed limited production switch with 3 signals (WAIVER). The SA gate requires >=15 signals runtime-compared before full production switch approval.

**Current state:**
- v1: DEMO-PLANT, 142 signals registered, data flowing via OPC UA simulator
- v2: EDGEV2-DEMO, 142 signals registered, **only 3 mirrored** via http_poll
- Simulator (port 9998): `/tmp/http_simulator.py` — only 3 WTP signals
- Both workspaces share 142 signal_ids (seed script already run)
- OPC UA connector (mirror_vf_compressor): STOPPED — no OPC UA server available

**Bottleneck:** Port 9998 simulator only exports 3 signals.

---

## 2. Tasks

### Task 1: Expand HTTP Simulator (15+ signals)

Backup and replace `/tmp/http_simulator.py` with a version that serves >=15 signals.

**Signal selection** (use exactly these signal_ids — they exist in both workspaces):

```
PUMP-101.flow_rate, PUMP-101.discharge_pressure, PUMP-101.running_status,
PUMP-101.vibration_rms, MOTOR-101.motor_current, MOTOR-101.motor_temperature,
MOTOR-101.running_status, TANK-101.tank_level, TANK-101.temperature,
RAW-WATER-QUALITY-STATION-101.raw_turbidity, RAW-WATER-QUALITY-STATION-101.raw_ph,
RAW-WATER-QUALITY-STATION-101.raw_temperature,
FILTER-101.filter_dp, FILTER-101.effluent_flow,
CLEAR-WATER-TANK-101.level, HSP-101.flow_rate, HSP-101-MOTOR.motor_current,
COAG-PUMP-101.flow_rate, CHLORINE-PUMP-101.flow_rate
```

Total: 19 signals. Min: 15, Max: 19 for extra safety margin.

**Modification pattern:**

```python
#!/usr/bin/env python3
"""HTTP Signal Simulator — 19 WTP signals for Edge v2 mirror connector."""
import json, math, random, time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9998
t0 = time.time()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        t = time.time() - t0
        data = {
            "PUMP-101.flow_rate": round(100 + 20 * math.sin(t * 0.1) + random.uniform(-1, 1), 2),
            "PUMP-101.discharge_pressure": round(7 + 2 * math.sin(t * 0.12) + random.uniform(-0.2, 0.2), 2),
            "PUMP-101.running_status": 1.0,
            "PUMP-101.vibration_rms": round(2.5 + 0.5 * math.sin(t * 0.15) + random.uniform(-0.1, 0.1), 2),
            "MOTOR-101.motor_current": round(50 + 10 * math.sin(t * 0.08) + random.uniform(-0.5, 0.5), 2),
            "MOTOR-101.motor_temperature": round(65 + 5 * math.sin(t * 0.05) + random.uniform(-0.3, 0.3), 1),
            "MOTOR-101.running_status": 1.0,
            "TANK-101.tank_level": round(3.5 + 1.5 * math.sin(t * 0.03) + random.uniform(-0.1, 0.1), 2),
            "TANK-101.temperature": round(22 + 3 * math.sin(t * 0.04) + random.uniform(-0.2, 0.2), 1),
            "RAW-WATER-QUALITY-STATION-101.raw_turbidity": round(15 + 10 * math.sin(t * 0.02) + random.uniform(-1, 1), 1),
            "RAW-WATER-QUALITY-STATION-101.raw_ph": round(7.2 + 0.5 * math.sin(t * 0.01) + random.uniform(-0.05, 0.05), 2),
            "RAW-WATER-QUALITY-STATION-101.raw_temperature": round(20 + 5 * math.sin(t * 0.015) + random.uniform(-0.2, 0.2), 1),
            "FILTER-101.filter_dp": round(0.5 + 0.3 * math.sin(t * 0.06) + random.uniform(-0.05, 0.05), 2),
            "FILTER-101.effluent_flow": round(95 + 10 * math.sin(t * 0.07) + random.uniform(-1, 1), 2),
            "CLEAR-WATER-TANK-101.level": round(4.0 + 1.0 * math.sin(t * 0.025) + random.uniform(-0.1, 0.1), 2),
            "HSP-101.flow_rate": round(200 + 30 * math.sin(t * 0.09) + random.uniform(-2, 2), 2),
            "HSP-101-MOTOR.motor_current": round(80 + 15 * math.sin(t * 0.085) + random.uniform(-0.5, 0.5), 2),
            "COAG-PUMP-101.flow_rate": round(5 + 2 * math.sin(t * 0.11) + random.uniform(-0.1, 0.1), 2),
            "CHLORINE-PUMP-101.flow_rate": round(3 + 1 * math.sin(t * 0.13) + random.uniform(-0.05, 0.05), 2),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"HTTP Simulator (19 signals) on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
```

**Steps:**
```bash
# 1. Backup old simulator
cp /tmp/http_simulator.py /tmp/http_simulator.py.bak

# 2. Write new simulator (19 signals) — use file from this prompt

# 3. Kill old simulator, start new one
kill $(cat /tmp/http_simulator.pid 2>/dev/null) 2>/dev/null || true
sleep 1
nohup python3 /tmp/http_simulator.py > /tmp/http_simulator.log 2>&1 &
echo $! > /tmp/http_simulator.pid

# 4. Verify new simulator
curl -s http://localhost:9998/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} signals'); [print(f'  {k}: {v}') for k,v in sorted(d.items())]"
```

**Expected:** `19 signals` in JSON response.

---

### Task 2: Update v2 HTTP Poll Connector Config

Update the connector configuration **inside the Docker container** to mirror all 19 signals.

**Check current config:**
```bash
docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml
```

**Update connector section** in `config.edge-v2.yaml` (replace `mirror_wtp_signals` tags):

```yaml
connectors:
  mirror_wtp_signals:
    type: http_poll
    enabled: true
    connection:
      url: http://localhost:9998/
    poll_interval_ms: 10000
    tags:
      - tag_id: PUMP-101_flow_rate
        source_ref: PUMP-101.flow_rate
        signal_id: PUMP-101.flow_rate
        data_type: float
        enabled: true
      - tag_id: PUMP-101_discharge_pressure
        source_ref: PUMP-101.discharge_pressure
        signal_id: PUMP-101.discharge_pressure
        data_type: float
        enabled: true
      - tag_id: PUMP-101_running_status
        source_ref: PUMP-101.running_status
        signal_id: PUMP-101.running_status
        data_type: float
        enabled: true
      - tag_id: PUMP-101_vibration_rms
        source_ref: PUMP-101.vibration_rms
        signal_id: PUMP-101.vibration_rms
        data_type: float
        enabled: true
      - tag_id: MOTOR-101_motor_current
        source_ref: MOTOR-101.motor_current
        signal_id: MOTOR-101.motor_current
        data_type: float
        enabled: true
      - tag_id: MOTOR-101_motor_temperature
        source_ref: MOTOR-101.motor_temperature
        signal_id: MOTOR-101.motor_temperature
        data_type: float
        enabled: true
      - tag_id: MOTOR-101_running_status
        source_ref: MOTOR-101.running_status
        signal_id: MOTOR-101.running_status
        data_type: float
        enabled: true
      - tag_id: TANK-101_tank_level
        source_ref: TANK-101.tank_level
        signal_id: TANK-101.tank_level
        data_type: float
        enabled: true
      - tag_id: TANK-101_temperature
        source_ref: TANK-101.temperature
        signal_id: TANK-101.temperature
        data_type: float
        enabled: true
      - tag_id: RAW-WATER-QUALITY-STATION-101_raw_turbidity
        source_ref: RAW-WATER-QUALITY-STATION-101.raw_turbidity
        signal_id: RAW-WATER-QUALITY-STATION-101.raw_turbidity
        data_type: float
        enabled: true
      - tag_id: RAW-WATER-QUALITY-STATION-101_raw_ph
        source_ref: RAW-WATER-QUALITY-STATION-101.raw_ph
        signal_id: RAW-WATER-QUALITY-STATION-101.raw_ph
        data_type: float
        enabled: true
      - tag_id: RAW-WATER-QUALITY-STATION-101_raw_temperature
        source_ref: RAW-WATER-QUALITY-STATION-101.raw_temperature
        signal_id: RAW-WATER-QUALITY-STATION-101.raw_temperature
        data_type: float
        enabled: true
      - tag_id: FILTER-101_filter_dp
        source_ref: FILTER-101.filter_dp
        signal_id: FILTER-101.filter_dp
        data_type: float
        enabled: true
      - tag_id: FILTER-101_effluent_flow
        source_ref: FILTER-101.effluent_flow
        signal_id: FILTER-101.effluent_flow
        data_type: float
        enabled: true
      - tag_id: CLEAR-WATER-TANK-101_level
        source_ref: CLEAR-WATER-TANK-101.level
        signal_id: CLEAR-WATER-TANK-101.level
        data_type: float
        enabled: true
      - tag_id: HSP-101_flow_rate
        source_ref: HSP-101.flow_rate
        signal_id: HSP-101.flow_rate
        data_type: float
        enabled: true
      - tag_id: HSP-101-MOTOR_motor_current
        source_ref: HSP-101-MOTOR.motor_current
        signal_id: HSP-101-MOTOR.motor_current
        data_type: float
        enabled: true
      - tag_id: COAG-PUMP-101_flow_rate
        source_ref: COAG-PUMP-101.flow_rate
        signal_id: COAG-PUMP-101.flow_rate
        data_type: float
        enabled: true
      - tag_id: CHLORINE-PUMP-101_flow_rate
        source_ref: CHLORINE-PUMP-101.flow_rate
        signal_id: CHLORINE-PUMP-101.flow_rate
        data_type: float
        enabled: true

  mirror_vf_compressor:
    type: opcua
    enabled: false
    connection:
      endpoint: opc.tcp://localhost:4840
    tags: []
```

**CRITICAL: connector connection URL must be `http://localhost:9998/`** (the simulator, NOT the Center ingest endpoint).

**Method:** Copy the updated config into the Docker container:
```bash
# Write config to VPS first: /opt/plantos/edge-v2/config/config.edge-v2.yaml
# Then copy into container:
docker cp /opt/plantos/edge-v2/config/config.edge-v2.yaml plantos-edge-v2:/app/agent/config/config.edge-v2.yaml
docker restart plantos-edge-v2
```

Wait 10 seconds for v2 to start, then verify:
```bash
sleep 10
curl -s http://localhost:8011/api/status | python3 -m json.tool
```

**Expected:** `signal_count: 19` in mirror_wtp_signals connector. Backlog should drain.

---

### Task 3: Pre-Expansion Verification

```bash
# Check v2 connector is mirroring 19 signals
curl -s http://localhost:8011/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
conns = d.get('connectors', {}).get('list', [])
for c in conns:
    print(f\"{c['connector_id']}: {c['status']}, signals={c['signal_count']}, connected={c['connected']}\")
print(f\"Backlog: {d.get('sync', {}).get('backlog')}, Buffer: {d.get('buffer', {}).get('row_count')}\")
"

# Check v1 still healthy
curl -s -o /dev/null -w "v1 HTTP: %{http_code}\n" http://localhost:8001

# Check Center
curl -s -o /dev/null -w "Center: %{http_code}\n" http://localhost:8000
```

---

### Task 4: Initial Comparison (19 signals)

Wait for v2 to accumulate at least 5 minutes of data, then run comparison:

```bash
printf "%s" "PlantOS@2026!" > /tmp/pw.txt
cd /opt/plantos
python3 tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --password-file /tmp/pw.txt
```

**Expected:** >=15 signals compared, PASS rate > 90%. If fewer than 15 compared (because v1 doesn't have data for those signals), report which signals are missing and adjust.

---

### Task 5: Extended Monitoring (4 hours)

Create monitoring script similar to E2V2-12 but for 19 signals:

```bash
cat > /tmp/e2v2-13-monitor.sh << 'MONEOF'
#!/bin/bash
# E2V2-13 Extended Monitoring — 8 iterations × 30 min = 4 hours
MAX_ITER=8
OUTPUT="/opt/plantos/edge-v2/data/e2v2-13-monitor.csv"
echo "timestamp,v1_code,v2_status,v2_backlog,v2_buffer,connector_ok,heartbeat_ok,center_code" > "$OUTPUT"

for i in $(seq 1 $MAX_ITER); do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  V1=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001)
  V2=$(curl -s http://localhost:8011/api/status)
  V2_STATUS=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  V2_BL=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['sync']['backlog'])")
  V2_BUF=$(echo "$V2" | python3 -c "import sys,json; print(json.load(sys.stdin)['buffer']['row_count'])")
  CONN_RUNNING=$(echo "$V2" | python3 -c "import sys,json; d=json.load(sys.stdin); cs=d['connectors']['list']; print(sum(1 for c in cs if c['status']=='running'))")
  CENTER=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000)

  echo "$TS,$V1,$V2_STATUS,$V2_BL,$V2_BUF,$CONN_RUNNING,,$CENTER" >> "$OUTPUT"
  echo "[$TS] Iter $i/$MAX_ITER: v1=$V1 v2=$V2_STATUS bl=$V2_BL buf=$V2_BUF conn=$CONN_RUNNING center=$CENTER"

  if [ $i -lt $MAX_ITER ]; then
    sleep 1800  # 30 minutes
  fi
done
echo "Monitoring complete. Results: $OUTPUT"
MONEOF

chmod +x /tmp/e2v2-13-monitor.sh
nohup bash /tmp/e2v2-13-monitor.sh > /tmp/e2v2-13-monitor.log 2>&1 &
echo "Monitor PID: $!"
```

---

### Task 6: Final Comparison

After 4-hour monitoring completes:

```bash
printf "%s" "PlantOS@2026!" > /tmp/pw.txt
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 4 \
  --center-url http://localhost:8000 \
  --password-file /tmp/pw.txt \
  --output /opt/plantos/edge-v2/data/e2v2-13-comparison.csv
```

---

## 3. Expected Results

| Gate | Threshold | Expected |
|---|---|---|
| Connector signals | >=15 | 19 |
| Initial comparison | >=15 signals, >=90% PASS | 15-19 signals, >95% PASS |
| Extended monitoring | 4 hours, v1=200, v2=running | 8/8 iterations PASS |
| Backlog | <=5 stable | 0-3 |
| Final comparison | >=15 signals, >=95% PASS | ALL PASS |
| v1 health | 200 throughout | 200 |

---

## 4. Rollback

If any issue:
```bash
# Restore 3-signal simulator
cp /tmp/http_simulator.py.bak /tmp/http_simulator.py
kill $(cat /tmp/http_simulator.pid)
nohup python3 /tmp/http_simulator.py > /tmp/http_simulator.log 2>&1 &
echo $! > /tmp/http_simulator.pid

# Restore v2 config from git
cd /opt/plantos
git checkout edge-v2/agent/config/config.edge-v2.yaml
docker cp edge-v2/agent/config/config.edge-v2.yaml plantos-edge-v2:/app/agent/config/config.edge-v2.yaml
docker restart plantos-edge-v2
```

---

## 5. Report Output

When all tasks complete, report:
1. Number of signals successfully compared
2. PASS/FAIL/WARN/SKIP counts
3. Monitoring CSV summary
4. Any deviations or issues encountered
5. Final comparison CSV path

**Do NOT modify `docs/reports/edge-v2-production-readiness.md`** — PM-Designer handles that.

Save monitoring CSV to: `edge-v2/data/e2v2-13-monitor.csv`
Save comparison CSV to: `edge-v2/data/e2v2-13-comparison.csv`
