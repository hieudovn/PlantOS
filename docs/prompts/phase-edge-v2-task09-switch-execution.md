# E2V2-9: Controlled Switch Preparation — VPS Execution

> **SA Gate:** ✅ CONDITIONALLY APPROVED
> **Role:** Coder-Executioner — run ONLY on VPS (103.97.132.249)
> **Constraint:** Edge v1 remains PRIMARY. NO switch operations.

## Prerequisites

```
VPS: 103.97.132.249
Repo: /opt/plantos
Center: http://localhost:8000 (JWT auth)
Edge v1: http://localhost:8001 (DEMO-PLANT)
Edge v2: http://localhost:8011 (EDGEV2-DEMO, Docker)
```

Ensure `PLANTOS_CENTER_PASSWORD` is set (export before running):

```bash
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
```

## Execution Steps

### Step 1: SCP Updated Files to VPS

Copy the new/updated scripts from local to VPS:

```bash
# From local machine:
scp scripts/seed_edgev2_demo.py root@103.97.132.249:/opt/plantos/scripts/
scp tools/compare_v1_v2_data.py root@103.97.132.249:/opt/plantos/tools/
```

### Step 2: Seed EDGEV2-DEMO Workspace

On VPS:

```bash
cd /opt/plantos
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
python scripts/seed_edgev2_demo.py --generate-measurements
```

**Expected output:**

```
Auth: logged in
Seeding EDGEV2-DEMO workspace...
  [1/4] Creating plant...
  [2/4] Creating areas...
  [3/4] Creating assets...
  [4/4] Creating signals...
  Done! Created 1 plant, 2 areas, 9 assets, 15 signals.
  Generating sample measurements...
  Ingested 900 sample measurements for EDGEV2-DEMO
```

### Step 3: Verify Workspace

```bash
# Check signals
curl -s "http://localhost:8000/api/v1/signals?plant_id=EDGEV2-DEMO" | python -c "import sys,json; d=json.load(sys.stdin); print(f'Signals: {len(d)}')"

# Check measurements exist
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=3" | python -c "import sys,json; d=json.load(sys.stdin); print(f'Measurements: {len(d)}')"
```

**Expected:** Signals >= 15, Measurements > 0

### Step 4: Health Check

```bash
# v1 running
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001

# v2 Docker running
curl -s http://localhost:8011/api/status | python -m json.tool

# Center healthy
curl -s http://localhost:8000/health

# v2 sync backlog
curl -s http://localhost:8011/api/status | python -c "import sys,json; print(json.load(sys.stdin).get('sync',{}).get('backlog','?'))"
```

**Expected:** v1=200, v2={"status":"running",...}, Center=200, backlog < 50

### Step 5: Run Side-by-Side Comparison (SA GATE)

```bash
cd /opt/plantos
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
python tools/compare_v1_v2_data.py --hours 1
```

**Expected output (SA gate condition):**

```
v1 signals: 15, v2 signals: 15
Shared signal_ids: 15
...
Results: 15 PASS, 0 FAIL, 0 WARN, 0 SKIP
✅ All shared signals within tolerance.
```

If FAIL > 0 → STOP. Document which signals exceeded ±5%.

### Step 6: Save Comparison Report

```bash
python tools/compare_v1_v2_data.py --hours 1 --output /tmp/comparison_$(date +%Y%m%d_%H%M%S).csv
```

Copy report to persistent location:

```bash
cp /tmp/comparison_*.csv /opt/plantos/edge-v2/data/
```

### Step 7: Verify Backlog Cleared

```bash
curl -s http://localhost:8011/api/status | python -c "import sys,json; s=json.load(sys.stdin); print(f\"backlog={s.get('sync',{}).get('backlog','?')}\")"
```

**Acceptance:** backlog < 50

## Red Flags

- 🔴 STOP if any shared signal exceeds ±5% tolerance
- 🔴 STOP if v2 backlog > 100 for > 5 minutes
- 🔴 STOP if v1 affected by any v2 operation
- 🔴 STOP if comparison returns 0 shared signals

## Expected Output Artifacts

```
/opt/plantos/edge-v2/data/comparison_YYYYMMDD_HHMMSS.csv
```

## Rollback

If anything goes wrong:

```bash
# STOP v2 if it's causing issues
docker compose -f /opt/plantos/edge-v2/docker-compose.edge-v2.yml stop

# Verify v1 still running
curl http://localhost:8001
```

## After Execution

1. Copy comparison CSV from VPS to local:
   ```bash
   scp root@103.97.132.249:/opt/plantos/edge-v2/data/comparison_*.csv edge-v2/data/
   ```
2. Update `docs/reports/edge-v2-production-readiness.md` with results
3. Commit and push to GitHub for SA final review
