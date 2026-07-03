# Security Hardening — Bước 5: Deploy VPS + Test Pipeline

## Context

Steps 1-4 done. All code uses new credentials. Old key `plantos-edge-key-2026` is removed from all code files. Now deploy everything to VPS and verify the full pipeline works.

## ⚠️ CRITICAL — ROLLBACK PLAN

If anything breaks after deploy, revert with ONE command:

```bash
# On VPS: restore old .env with the original key
echo 'API_KEYS=plantos-edge-key-2026' >> /opt/plantos/deployment/.env
docker compose restart backend
```

Keep the old key handy until testing is complete.

---

## Step 1: Prepare Deployment Package

From local, copy ALL changed files to a staging folder:

```powershell
# Build a deployment package
mkdir d:\deploy-pkg

# .env with new credentials
copy deployment\.env d:\deploy-pkg\

# Backend changes
copy backend\app\core\config.py d:\deploy-pkg\
copy backend\app\middleware\auth.py d:\deploy-pkg\
copy backend\app\main.py d:\deploy-pkg\

# Docker compose
copy deployment\docker-compose.yml d:\deploy-pkg\

# Edge Agent
copy edge\agent\config.yaml d:\deploy-pkg\
copy edge\agent\main.py d:\deploy-pkg\
copy edge\agent\metadata.py d:\deploy-pkg\
copy edge\agent\publisher.py d:\deploy-pkg\

# Frontend src (entire directory for safety)
# (use scp -r frontend\src\* instead)
```

Actually, use the full src copy for Frontend:

```powershell
scp -r "d:\Project\Github\PlantOS\frontend\src\*" plantos@103.97.132.249:/opt/plantos/frontend/src/
scp "d:\Project\Github\PlantOS\frontend\.env" plantos@103.97.132.249:/opt/plantos/frontend/.env
```

## Step 2: Deploy Backend + Config

```bash
# SSH to VPS
ssh plantos@103.97.132.249

# 2a. Copy .env to deployment
cp ~/deploy/.env /opt/plantos/deployment/.env
# (if scp'd to home, move it)

# 2b. Copy backend files
cp ~/deploy/config.py /opt/plantos/backend/app/core/config.py
cp ~/deploy/auth.py /opt/plantos/backend/app/middleware/auth.py
cp ~/deploy/main.py /opt/plantos/backend/app/main.py  # (if modified)
cp ~/deploy/docker-compose.yml /opt/plantos/deployment/docker-compose.yml

# 2c. Restart backend container
cd /opt/plantos/deployment
docker compose restart backend

# 2d. Check logs for errors
docker logs plantos-backend --tail 30
```

Expected: Backend starts without credential errors. Look for:
- ❌ `POSTGRES_PASSWORD is not set` → .env not loaded
- ❌ `JWT_SECRET is not set` → missing config
- ✅ No errors → backend healthy

## Step 3: Rebuild Frontend

```bash
cd /opt/plantos/frontend
sudo rm -rf dist
npm run build

# Verify new key is in JS, old key is NOT
grep -c "plantos-frontend" dist/assets/*.js
# Expected: 1
grep -c "plantos-edge-key-2026" dist/assets/*.js
# Expected: 0
```

## Step 4: Restart Edge Agent

```bash
# 4a. Copy Edge config
cp ~/deploy/config.yaml /opt/plantos/edge/agent/config.yaml
cp ~/deploy/main.py /opt/plantos/edge/agent/main.py
cp ~/deploy/metadata.py /opt/plantos/edge/agent/metadata.py  
cp ~/deploy/publisher.py /opt/plantos/edge/agent/publisher.py

# 4b. Set env vars for Edge Agent
export EDGE_API_KEY=$(grep EDGE_API_KEY /opt/plantos/deployment/.env | cut -d= -f2)
export MQTT_USER=edge-agent
export MQTT_PASSWORD=$(grep MQTT_PASSWORD /opt/plantos/deployment/.env | cut -d= -f2)

# 4c. Restart Edge Agent
sudo systemctl restart plantos-edge-agent
# OR if using tmux/screen:
# kill existing, restart with env vars
```

## Step 5: Test Full Pipeline

### 5a: Backend health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### 5b: Auth with new key
```bash
NEW_KEY=$(grep EDGE_API_KEY /opt/plantos/deployment/.env | cut -d= -f2)
curl http://localhost:8000/api/v1/plants -H "X-API-Key: $NEW_KEY"
# Expected: ["VF-DEMO", "APPLY-TEST-02", "WTP-DEMO-01"]
```

### 5c: Edge Agent heartbeat
```bash
# Check Edge Fleet in Center
curl http://localhost:8000/api/v1/edge-nodes -H "X-API-Key: $NEW_KEY"
# Expected: edge-agent-01 with recent heartbeat
```

### 5d: Edge → Center data flow
```bash
# Check VF Compressor data still flowing
curl "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-CORE.speed&limit=1" \
  -H "X-API-Key: $NEW_KEY"
# Expected: recent timestamp

# Check WTP data (via HTTP ingest if still running)
curl "http://localhost:8000/api/v1/measurements/history?signal_id=RAW-WATER-QUALITY-STATION-101.raw_turbidity&limit=1" \
  -H "X-API-Key: $NEW_KEY"
# Expected: recent timestamp
```

### 5e: Frontend
```bash
# Open browser → http://103.97.132.249/
# Verify: Workspace dropdown shows 3 plants
# Verify: Historian shows data for both VF and WTP
# Verify: Diagrams show WTP process flow
# Verify: No 401 errors in browser console
```

### 5f: MQTT
```bash
# Check EMQX dashboard
curl http://localhost:18083/api/v5/status -u "admin:$MQTT_PASSWORD"
# Expected: running
```

---

## Final Verification Checklist

- [ ] Backend starts without credential errors
- [ ] `/health` returns 200
- [ ] New `EDGE_API_KEY` works for API calls
- [ ] Old key `plantos-edge-key-2026` REJECTED (401)
- [ ] Edge Agent heartbeat visible in Center
- [ ] VF Compressor data flowing (26 signals)
- [ ] WTP data accessible in historian
- [ ] Frontend loads without 401 errors
- [ ] Workspace shows VF-DEMO + WTP-DEMO-01
- [ ] Historian time range buttons work
- [ ] Logout button visible
- [ ] Diagrams show WTP process flow
- [ ] MQTT auth working
- [ ] Metadata sync works (bug fixed)

## Rollback (if needed)

```bash
# Restore old docker-compose with old key defaults
cd /opt/plantos/deployment
git checkout docker-compose.yml   # or restore from backup
docker compose restart backend

# Restart Edge Agent with old config and old key
export EDGE_API_KEY=plantos-edge-key-2026
# ... restart edge agent
```
