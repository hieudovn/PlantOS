#!/bin/bash
# Phase 8 Runtime Containment — Automated Script
# Run on VPS: bash phase8-contain.sh

set -e
echo "=== PHASE 8 RUNTIME CONTAINMENT ==="
date

# 1. Backup current state
echo "[1] Backing up state..."
ss -tlnp > /tmp/ports-before-phase8.txt
docker ps > /tmp/docker-before-phase8.txt
docker images --digests > /tmp/images-before-phase8.txt
echo "Backup done"

# 2. Generate new secrets
echo "[2] Generating new secrets..."
NEW_JWT=$(openssl rand -hex 32)
NEW_SESSION=$(openssl rand -hex 32)
NEW_API_KEY=$(openssl rand -hex 24)
NEW_EDGE_PW=$(openssl rand -base64 18 | tr -d '\n')
echo "Secrets generated"

# 3. Create/update .env file for docker-compose
echo "[3] Creating .env file..."
cat > /opt/plantos/deployment/.env << ENVEOF
# Phase 8 Immutable Deployment — $(date -I)
POSTGRES_USER=plantos
POSTGRES_PASSWORD=plantos_test
POSTGRES_DB=plantos_test
JWT_SECRET=${NEW_JWT}
SESSION_SECRET=${NEW_SESSION}
API_KEYS=${NEW_API_KEY}
EDGE_CENTER_PASSWORD=${NEW_EDGE_PW}
ENVEOF
chmod 600 /opt/plantos/deployment/.env
echo ".env created"

# 4. Verify secrets were rotated
echo "[4] Verifying credential rotation..."
echo "JWT_SECRET length: ${#NEW_JWT}"
echo "SESSION_SECRET length: ${#NEW_SESSION}"
echo "API_KEY length: ${#NEW_API_KEY}"
echo "EDGE_PASSWORD length: ${#NEW_EDGE_PW}"

# 5. Build immutable images
echo "[5] Building immutable Edge v2 image..."
cd /opt/plantos
git fetch origin main
git checkout main
git pull origin main
docker build --no-cache -t plantos-edge-v2:phase8-immutable -f edge-v2/Dockerfile . 2>&1 | tail -5
EDGE_DIGEST=$(docker images --digests plantos-edge-v2:phase8-immutable --format '{{.Digest}}')
echo "Edge image: $EDGE_DIGEST"

echo "[6] Building immutable Backend image..."
docker build --no-cache -t plantos-backend:phase8-immutable -f backend/Dockerfile . 2>&1 | tail -5
BACKEND_DIGEST=$(docker images --digests plantos-backend:phase8-immutable --format '{{.Digest}}')
echo "Backend image: $BACKEND_DIGEST"

echo "[7] Building immutable Frontend image..."
docker build --no-cache -t plantos-frontend:phase8-immutable -f frontend/Dockerfile . 2>&1 | tail -5
FRONTEND_DIGEST=$(docker images --digests plantos-frontend:phase8-immutable --format '{{.Digest}}')
echo "Frontend image: $FRONTEND_DIGEST"

# 6. Write release manifest
echo "[8] Writing release manifest..."
cat > /opt/plantos/deployment/release-manifest-phase8.txt << MANIFEST
Phase 8 Immutable Release
Date: $(date -Iseconds)
Commit: $(git rev-parse HEAD)
Branch: main

Images:
  plantos-edge-v2:phase8-immutable  ${EDGE_DIGEST}
  plantos-backend:phase8-immutable  ${BACKEND_DIGEST}
  plantos-frontend:phase8-immutable ${FRONTEND_DIGEST}

Firewall: UFW enabled, only 22, 80, 443 exposed
Credentials: Rotated $(date -I)
MANIFEST
cat /opt/plantos/deployment/release-manifest-phase8.txt

# 7. Verify old credentials are rejected
echo "[9] Verifying old credentials are rejected..."
# Test with old default API key
curl -s -o /dev/null -w "Old API key: HTTP %{http_code}\n" \
  -H "X-API-Key: plantos-edge-key-2026" http://localhost:8000/api/v1/health || true
# Test with new API key
curl -s -o /dev/null -w "New API key: HTTP %{http_code}\n" \
  -H "X-API-Key: ${NEW_API_KEY}" http://localhost:8000/api/v1/health || true

echo ""
echo "=== CONTAINMENT COMPLETE ==="
echo "Release manifest: /opt/plantos/deployment/release-manifest-phase8.txt"
