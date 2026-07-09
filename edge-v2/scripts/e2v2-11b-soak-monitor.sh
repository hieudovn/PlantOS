#!/bin/bash
# E2V2-11B: Extended soak test monitor
# Records health metrics every 5 minutes
MAX_MINUTES=${1:-240}
INTERVAL=300
ITER=0
MAX_ITER=$((MAX_MINUTES * 60 / INTERVAL))
START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUTPUT="/opt/plantos/edge-v2/data/soak_$(date +%Y%m%d_%H%M%S).csv"
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'

echo "timestamp,v1_code,v2_status,v2_backlog,v2_buffer_rows,cpu_pct,mem_mb,disk_mb,duckdb_mb,connector_status,jwt_ok,center_code" > "$OUTPUT"

echo "=== E2V2-11B Soak Monitor ==="
echo "Duration: $MAX_MINUTES minutes ($MAX_ITER iterations, ${INTERVAL}s interval)"
echo "Started: $START_TS"
echo "Output: $OUTPUT"
echo ""

while [ $ITER -lt $MAX_ITER ]; do
  ITER=$((ITER + 1))
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  V1=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001 2>/dev/null || echo "ERR")
  CE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo "ERR")

  V2_DATA=$(python3 -c "
import httpx, json
try:
    r = httpx.get('http://localhost:8011/api/status', timeout=5)
    s = json.loads(r.text)
    status = s.get('status','?')
    bl = s.get('sync',{}).get('backlog','?')
    br = s.get('buffer',{}).get('row_count','?')
    conns = s.get('connectors',{})
    clist = conns.get('list',[])
    conn_ok = sum(1 for c in clist if c.get('status')=='running')
    conn_total = len(clist)
    print(f'{status},{bl},{br},{conn_ok}/{conn_total}')
except Exception as e:
    print(f'ERR,?,?,?')
" 2>/dev/null || echo "ERR,?,?,?")

  DOCKER_DATA=$(python3 -c "
import subprocess, httpx, json, glob, os
try:
    r = subprocess.run(['docker','stats','plantos-edge-v2','--no-stream','--format','{{.CPUPerc}} {{.MemUsage}}'], capture_output=True, text=True, timeout=5)
    parts = r.stdout.strip().split()
    cpu = parts[0].replace('%','') if len(parts)>0 else '?'
    mem = parts[1].split('/')[0] if len(parts)>1 else '?'
    mem_mb = mem.replace('MiB','').replace('GiB','000').split('.')[0] if 'i' in mem else '?'

    r2 = subprocess.run(['du','-sm','/opt/plantos/edge-v2/data/'], capture_output=True, text=True, timeout=5)
    disk = r2.stdout.split()[0] if r2.stdout else '?'

    db_files = glob.glob('/opt/plantos/edge-v2/data/*.duckdb')
    duckdb_mb = str(round(os.path.getsize(db_files[0])/1024/1024,1)) if db_files else '0'

    api = 'http://localhost:8000/api/v1'
    pw = os.environ.get('PLANTOS_CENTER_PASSWORD','PlantOS@2026!')
    r3 = httpx.post(f'{api}/auth/login', json={'username':'admin','password':pw}, timeout=5)
    jwt_ok = '1' if r3.status_code==200 and r3.json().get('access_token') else '0'

    print(f'{cpu},{mem_mb},{disk},{duckdb_mb},{jwt_ok}')
except Exception as e:
    print(f'?,?,?,?,?')
" 2>/dev/null || echo "?,?,?,?,?")

  echo "${TS},${V1},${V2_DATA},${DOCKER_DATA},${CE}" >> "$OUTPUT"

  if [ $((ITER % 6)) -eq 0 ]; then
    echo "[$TS] Iter $ITER/$MAX_ITER — v1=$V1 v2=$(echo $V2_DATA | cut -d, -f1) backlog=$(echo $V2_DATA | cut -d, -f2) cpu=$(echo $DOCKER_DATA | cut -d, -f1)% mem=$(echo $DOCKER_DATA | cut -d, -f2)MB"
  fi

  sleep $INTERVAL
done

echo ""
echo "=== SOAK MONITOR COMPLETE ==="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Output: $OUTPUT"
