# Phase 5 Closure & VPS Deployment Plan

> **PM/Designer Review:** DeepSeek V4 Pro | **Date:** 2026-07-01

---

## 1. PROJECT STATUS — Phase 5 Closing

### Constitution Compliance Review

| Law | Status | Evidence |
|---|---|---|
| No raw-data coupling | ✅ | All UI accesses via asset/signal API; UNS paths; no raw tag refs |
| UI must not query DB directly | ✅ | Backend API layer enforced; Vite proxy for dev |
| UNS-native | ✅ | `avenue/{plant}/{area}/{asset}/{signal}` pattern |
| CDM-native | ✅ | Plant, Area, Asset, Signal, Event entities |
| Edge-Center separation | ✅ | Edge: DuckDB buffer + collectors + sync; Center: PostgreSQL + TDengine + API |
| Vendor-neutral | ✅ | OPC UA, Modbus, MQTT — protocol adapters, not lock-in |
| Composable | ✅ | Modbus and OPC UA collectors follow same pattern (client→mapper→collector) |

### Architecture Changes Since Phase 0

| Change | ADR | Impact |
|---|---|---|
| DuckDB for Edge local TSDB | ADR-0003 | Replaces SQLite; columnar, fast, embedded |
| OPC UA Collector | ADR-0004 | Pattern: client→mapper→collector; namespace mapping |
| Integration Data Contract | ADR-0005 | Single YAML manifest for VF↔PlantOS binding |
| EventDispatcher (in-process pub/sub) | (inline Phase 5-01) | Decouples side effects from API routers |
| Manifest-Driven Edge Mapper | (inline Phase 5-04) | Edge reads OPC UA bindings from Center manifest |

### What's Implemented (44 prompts across 5 phases)

| Phase | Tasks | Status |
|---|---|---|
| Phase 0 | Foundation docs, architecture, ADR-0001 | ✅ CLOSED |
| Phase 1 | Repo, Docker, FastAPI, PostgreSQL, TDengine, Asset/Signal/Measurement APIs, Seed, Simulator, Frontend shell, Trend, Diagram, GIS | ✅ CLOSED |
| Phase 2 | UX Polish, Edge Agent, Asset Tree, WebSocket, Diagram wrap-up | ✅ CLOSED |
| Phase 3 | Edge Web UI, Asset Sync, Modbus Adapter | ✅ CLOSED |
| Phase 4 | Alarm Engine, Calculated Signals, Alarm UI | ✅ CLOSED |
| Phase 5-01 | CDM Events + Historian Hardening + EventDispatcher + UNS Governance | ✅ CLOSED |
| Phase 5-02 | OPC UA Collector + Virtual Factory Integration (Compressor Train) | ✅ CLOSED |
| Phase 5-03 | Frontend Multi-Workspace (VF-DEMO ↔ DEMO-PLANT) | ✅ CLOSED |
| Phase 5-04 | Manifest-Driven Seed + Edge OPC UA Binding | ✅ CLOSED |
| Phase 5-05 | Signal Realtime + Historian Cross-Workspace Fix | ✅ CLOSED |

### VPS Deployed (2026-07-01)

| Service | Port | URL |
|---|---|---|
| Nginx reverse proxy | 80 | http://103.97.132.249 |
| Backend API | 8000 | http://103.97.132.249:8000 |
| Edge Dashboard | 8001 | http://103.97.132.249:8001 |
| VF OPC UA Server | 4840 | opc.tcp://103.97.132.249:4840 |

### VPS Architecture

```
Nginx :80
  ├── /            → frontend/dist (static build)
  ├── /api/*       → backend :8000
  └── /ws/*        → backend :8000 (WebSocket)

Docker Compose:
  ├── postgres:16  :5432
  ├── tdengine      :6041
  ├── emqx:5.7      :1883
  ├── backend       :8000
  └── frontend      :5173 (dev, not used publicly)

Native (systemd-ready):
  ├── Edge Agent    :8001
  └── Virtual Factory :4840 (OPC UA)
```

### Running Services (Local)

| Service | Port | Container | Status |
|---|---|---|---|
| PostgreSQL 16 | 5432 | plantos-postgres | ✅ |
| TDengine 3.x | 6041 | plantos-tdengine | ✅ |
| EMQX 5.7 | 1883 | plantos-emqx | ✅ |
| Backend (FastAPI) | 8000 | plantos-backend | ✅ |
| Frontend (React+Vite) | 5173 | plantos-frontend | ✅ |
| Edge Agent | 8001 | (native python) | ✅ |
| VF OPC UA Server | 4840 | (native python) | ✅ |

### Data Flow Verified

```
VF Compressor Train → OPC UA :4840 → Edge Agent → DuckDB → MQTT → Center → TDengine → UI
                         26 signals          26 mappings     ✅         ✅       ✅
```

---

## 2. DOCUMENT UPDATE GAPS

| Document | Issue | Action |
|---|---|---|
| `docs/90-roadmap.md` | Dừng ở Phase 3; Phase 4-5 chưa cập nhật | Cập nhật |
| `docs/99-phase-0-closure-checklist.md` | Chỉ có Phase 0 | Tạo Phase-5 closure |
| `docs/19-deployment-design.md` | Chỉ có Docker Compose local | Bổ sung VPS deploy |
| `docs/12-mvp-scope.md` | Demo plant là DEMO-PLANT (cũ) | Bổ sung VF-DEMO |
| `docs/11-repository-structure.md` | Thiếu `examples/`, `edge/agent/collectors/opcua/` | Cập nhật |

---

## 3. VPS DEPLOYMENT PLAN

### Target Architecture

```
VPS (Ubuntu 22.04 / 24.04)
├── Docker Engine
│   ├── plantos-postgres    :5432
│   ├── plantos-tdengine    :6041
│   ├── plantos-emqx        :1883
│   ├── plantos-backend     :8000
│   └── plantos-frontend    :5173 → nginx reverse proxy :80/:443
│
├── Native Python (systemd service)
│   └── plantos-edge-agent  :8001
│
└── Virtual Factory (optional, cùng host hoặc VPS riêng)
    └── vf-opcua-server     :4840
```

### Prerequisites

| Item | Value |
|---|---|
| VPS IP | (user provides) |
| OS | Ubuntu 22.04 or 24.04 LTS |
| Docker | 24+ with Compose v2 |
| Python | 3.11+ (for Edge Agent) |
| Git | For repo clone |
| Firewall | Open: 80, 443, 8000, 8001, 4840, 5173 (dev) |

### Step-by-Step Deploy

#### Step 1: Clone & Setup

```bash
ssh user@VPS_IP
git clone https://github.com/<org>/PlantOS.git /opt/plantos
cd /opt/plantos
```

#### Step 2: Docker Compose (Center Services)

```bash
cd /opt/plantos/deployment

# Tạo .env file
cat > .env << 'EOF'
POSTGRES_DB=plantos
POSTGRES_USER=plantos
POSTGRES_PASSWORD=<secure_password>
POSTGRES_PORT=5432
TDENGINE_REST_PORT=6041
TDENGINE_DATABASE=plantos_ts
EMQX_MQTT_PORT=1883
BACKEND_PORT=8000
FRONTEND_PORT=5173
EOF

# Start services
docker compose up -d postgres tdengine emqx backend frontend

# Verify
docker compose ps
curl http://localhost:8000/health
```

#### Step 3: Seed VF-DEMO Data

```bash
curl -X POST http://localhost:8000/api/v1/seed/vf-demo
# Expected: {"status":"ok","plants":1,...}
```

#### Step 4: Edge Agent (systemd)

```bash
cd /opt/plantos/edge/agent
pip install -r requirements.txt

# Update config.yaml:
#   center_url: http://localhost:8000
#   mqtt.host: localhost
#   opcua.endpoint: opc.tcp://<VF_IP>:4840

# Create systemd service
sudo cat > /etc/systemd/system/plantos-edge.service << 'EOF'
[Unit]
Description=PlantOS Edge Agent
After=network.target docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/plantos/edge/agent
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable plantos-edge
sudo systemctl start plantos-edge
sudo systemctl status plantos-edge
```

#### Step 5: Nginx Reverse Proxy (Production)

```bash
sudo apt install nginx certbot python3-certbot-nginx -y

sudo cat > /etc/nginx/sites-available/plantos << 'EOF'
server {
    listen 80;
    server_name plantos.example.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Edge Dashboard
    location /edge/ {
        proxy_pass http://localhost:8001/;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/plantos /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### Step 6: SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d plantos.example.com
```

### Docker Compose VPS Adjustments

```yaml
# deployment/docker-compose.prod.yml (PROPOSED)
services:
  postgres:
    restart: always
    volumes:
      - /data/plantos/postgres:/var/lib/postgresql/data

  tdengine:
    restart: always
    volumes:
      - /data/plantos/tdengine:/var/lib/taos

  backend:
    restart: always
    environment:
      HISTORIAN_MODE: tdengine  # Force TDengine in production

  frontend:
    restart: always
    # Production build (not dev server)
    build:
      target: production
```

### Firewall Rules

```bash
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 8000/tcp   # Backend (internal/tunnel)
sudo ufw allow 8001/tcp   # Edge dashboard
sudo ufw allow 4840/tcp   # OPC UA (if VF on separate host)
sudo ufw enable
```

### Health Check Script

```bash
#!/bin/bash
# /opt/plantos/scripts/health-check.sh

echo "=== PlantOS Health Check ==="
echo -n "PostgreSQL: "; docker exec plantos-postgres pg_isready -U plantos && echo "OK" || echo "FAIL"
echo -n "TDengine:   "; curl -s http://localhost:6041/rest/sql -d "show databases" | grep -q plantos_ts && echo "OK" || echo "FAIL"
echo -n "Backend:    "; curl -s http://localhost:8000/health | grep -q ok && echo "OK" || echo "FAIL"
echo -n "Frontend:   "; curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -q 200 && echo "OK" || echo "FAIL"
echo -n "Edge Agent: "; curl -s http://localhost:8001/api/status | grep -q node_id && echo "OK" || echo "FAIL"
echo -n "OPC UA:     "; curl -s http://localhost:8001/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('opcua',{}).get('connected') else 'DISCONNECTED')"
```

---

## 4. NEXT PHASE — Phase 6: Industrial Hardening

| Task | Priority |
|---|---|
| Authentication (JWT / API key) | HIGH |
| Role-based access control | HIGH |
| Database backup (PostgreSQL + TDengine) | HIGH |
| Monitoring (Prometheus + Grafana) | MEDIUM |
| API rate limiting | MEDIUM |
| Audit logging | MEDIUM |
| CI/CD pipeline (GitHub Actions) | MEDIUM |
| Docker image versioning | LOW |

---

## 5. CONSTITUTION VIOLATIONS TO ADDRESS

| Issue | Severity | Plan |
|---|---|---|
| No authentication on API | HIGH | Phase 6-01: JWT auth |
| Edge Agent uses plain config.yaml | MEDIUM | Phase 5-04: manifest-driven (done) |
| No backup strategy | HIGH | Phase 6-02: pg_dump + TDengine backup |
| Frontend v0.1.0 displayed (not v0.2.0) | LOW | Bump version in frontend |
| `edge_node_id` hardcoded per agent | LOW | Future: dynamic registration |

---

## Files Created/Updated

| File | Action |
|---|---|
| `docs/status-phase5-closure-deploy.md` | CREATE — this document |
| `docs/90-roadmap.md` | UPDATE — add Phase 4-6 status |
| `docs/12-mvp-scope.md` | UPDATE — add VF-DEMO as demo plant |
| `deployment/docker-compose.yml` | (already has volume mount for manifest) |
