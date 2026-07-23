# PlantOS Phase 8 — VPS Runtime Runbook

> **Sanitized runbook** — no IPs, no hardcoded PIDs, no `StrictHostKeyChecking=no`.
> Replace `${VPS_HOST}` with the actual VPS hostname or IP at runtime.

---

## Prerequisites

- SSH key pair configured on VPS (no password-only auth)
- Docker and Docker Compose installed on VPS
- UFW installed on VPS
- Git access to repository on VPS

---

## 1. Runtime Containment

### 1.1 Enable UFW firewall

```bash
ssh root@${VPS_HOST} << 'EOF'
  ufw --force enable
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw status verbose
EOF
```

### 1.2 Kill test/debug servers

```bash
ssh root@${VPS_HOST} << 'EOF'
  # Kill any test servers on ephemeral ports
  for port in 9998 9999; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then kill "$pid"; echo "Killed PID $pid on port $port"; fi
  done
  ss -lntp | grep -E ':(9998|9999|4840|4841|7000|8002|8100)' || echo "No unauthorized ports listening"
EOF
```

### 1.3 Verify firewall

```bash
ssh root@${VPS_HOST} 'ss -lntp; ufw status; docker ps --format "table {{.Names}}\t{{.Ports}}"'
```

---

## 2. Credential Rotation

### 2.1 Generate new secrets

```bash
echo "JWT_SECRET=$(openssl rand -hex 32)"
echo "API_KEY=$(openssl rand -hex 24)"
echo "EDGE_SESSION_SECRET=$(openssl rand -hex 32)"
```

### 2.2 Update .env on VPS

```bash
scp deployment/.env root@${VPS_HOST}:/opt/plantos/deployment/.env
ssh root@${VPS_HOST} 'chmod 600 /opt/plantos/deployment/.env'
```

### 2.3 Verify old credentials rejected

```bash
# Old API key should return 401
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: REPLACE_WITH_OLD_KEY" \
  http://${VPS_HOST}/api/v1/health
# Expected: 401

# New API key should return 200
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: ${NEW_API_KEY}" \
  http://${VPS_HOST}/api/v1/health
# Expected: 200
```

---

## 3. Health Checks

```bash
# Backend health
curl -sf http://${VPS_HOST}/api/v1/health | jq .

# User login
curl -sf -X POST http://${VPS_HOST}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<REDACTED>","password":"<REDACTED>"}' | jq -r '.access_token'

# Frontend access
curl -sf -o /dev/null -w "%{http_code}" http://${VPS_HOST}/
# Expected: 200

# Edge v2 health
curl -sf http://${VPS_HOST}:8011/health | jq .
```

---

## 4. Rollback Procedure

```bash
ssh root@${VPS_HOST} << 'EOF'
  cd /opt/plantos/deployment
  # Stop new containers
  docker compose stop backend frontend
  # Start previous images
  docker compose -f docker-compose.yml -f docker-compose.previous.yml up -d
  # Verify
  sleep 5
  curl -sf http://localhost/api/v1/health
EOF
```
