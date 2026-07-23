#!/usr/bin/env bash
# PlantOS Phase 8 — Deploy from Exact Release SHA
# Usage: RELEASE_SHA=<full-sha> VPS_HOST=<host> ./deployment/scripts/deploy-from-release.sh
set -euo pipefail

# --- Validate inputs ---
: "${RELEASE_SHA:?RELEASE_SHA is required}"
: "${VPS_HOST:?VPS_HOST is required}"

RELEASE_SHORT="${RELEASE_SHA:0:7}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
MANIFEST_FILE="deployment/release-manifest-${RELEASE_SHORT}.txt"

echo "=== PlantOS Release Deploy ==="
echo "RELEASE_SHA:  ${RELEASE_SHA}"
echo "RELEASE_SHORT: ${RELEASE_SHORT}"
echo "VPS_HOST:     ${VPS_HOST}"
echo "TIMESTAMP:    ${TIMESTAMP}"

# --- 1. Checkout exact SHA ---
git fetch origin "${RELEASE_SHA}"
git checkout --detach "${RELEASE_SHA}"
CURRENT_SHA="$(git rev-parse HEAD)"
if [ "${CURRENT_SHA}" != "${RELEASE_SHA}" ]; then
  echo "FATAL: SHA mismatch — HEAD=${CURRENT_SHA} expected=${RELEASE_SHA}"
  exit 1
fi
echo "CHECKOUT_OK: ${RELEASE_SHA}"

# --- 2. Build images with OCI labels ---
echo "=== Building images ==="

docker build \
  --label "org.opencontainers.image.revision=${RELEASE_SHA}" \
  --label "org.opencontainers.image.created=${TIMESTAMP}" \
  --label "org.opencontainers.image.version=phase8-${RELEASE_SHORT}" \
  -t "plantos-backend:${RELEASE_SHORT}" \
  -f backend/Dockerfile .

docker build \
  --label "org.opencontainers.image.revision=${RELEASE_SHA}" \
  --label "org.opencontainers.image.created=${TIMESTAMP}" \
  --label "org.opencontainers.image.version=phase8-${RELEASE_SHORT}" \
  -t "plantos-frontend:${RELEASE_SHORT}" \
  -f frontend/Dockerfile .

docker build \
  --label "org.opencontainers.image.revision=${RELEASE_SHA}" \
  --label "org.opencontainers.image.created=${TIMESTAMP}" \
  --label "org.opencontainers.image.version=phase8-${RELEASE_SHORT}" \
  -t "plantos-edge-v2:${RELEASE_SHORT}" \
  -f edge-v2/Dockerfile .

# --- 3. Capture image digests ---
BACKEND_DIGEST="$(docker inspect plantos-backend:${RELEASE_SHORT} --format='{{.Id}}')"
FRONTEND_DIGEST="$(docker inspect plantos-frontend:${RELEASE_SHORT} --format='{{.Id}}')"
EDGE_DIGEST="$(docker inspect plantos-edge-v2:${RELEASE_SHORT} --format='{{.Id}}')"

echo "BUILD_OK"

# --- 4. Save images for transfer ---
docker save "plantos-backend:${RELEASE_SHORT}" -o "plantos-backend-${RELEASE_SHORT}.tar"
docker save "plantos-frontend:${RELEASE_SHORT}" -o "plantos-frontend-${RELEASE_SHORT}.tar"
docker save "plantos-edge-v2:${RELEASE_SHORT}" -o "plantos-edge-v2-${RELEASE_SHORT}.tar"

# --- 5. Transfer to VPS ---
echo "=== Transferring images to VPS ==="
scp "plantos-backend-${RELEASE_SHORT}.tar" "root@${VPS_HOST}:/tmp/"
scp "plantos-frontend-${RELEASE_SHORT}.tar" "root@${VPS_HOST}:/tmp/"
scp "plantos-edge-v2-${RELEASE_SHORT}.tar" "root@${VPS_HOST}:/tmp/"

# --- 6. Deploy on VPS using immutable release compose ---
echo "=== Deploying on VPS ==="
ssh root@"${VPS_HOST}" << DEPLOY
set -e
cd /opt/plantos/deployment

# Load new images
docker load -i "/tmp/plantos-backend-${RELEASE_SHORT}.tar"
docker load -i "/tmp/plantos-frontend-${RELEASE_SHORT}.tar"
docker load -i "/tmp/plantos-edge-v2-${RELEASE_SHORT}.tar"

# Verify existing DB connection (do NOT overwrite credentials)
docker compose exec -T postgres pg_isready -U plantos -d plantos
echo "DB_CONNECTION_OK"

# Deploy using immutable release compose (no build: directives)
RELEASE_SHORT=${RELEASE_SHORT} docker compose -f docker-compose.yml -f docker-compose.release.yml up -d backend frontend edge-v2

# Clean up tar files
rm -f "/tmp/plantos-backend-${RELEASE_SHORT}.tar" "/tmp/plantos-frontend-${RELEASE_SHORT}.tar" "/tmp/plantos-edge-v2-${RELEASE_SHORT}.tar"
DEPLOY

echo "DEPLOY_OK"

# --- 7. Write release manifest ---
cat > "${MANIFEST_FILE}" << MANIFEST
Release SHA:      ${RELEASE_SHA}
Release Short:    ${RELEASE_SHORT}
Timestamp:        ${TIMESTAMP}
Backend Image ID: ${BACKEND_DIGEST}
Frontend Image ID: ${FRONTEND_DIGEST}
Edge v2 Image ID: ${EDGE_DIGEST}
Backend Tag:      plantos-backend:${RELEASE_SHORT}
Frontend Tag:     plantos-frontend:${RELEASE_SHORT}
Edge v2 Tag:      plantos-edge-v2:${RELEASE_SHORT}
OCI Revision:     ${RELEASE_SHA}
VPS Host:         ${VPS_HOST}
MANIFEST

echo "=== Manifest written to ${MANIFEST_FILE} ==="
cat "${MANIFEST_FILE}"
echo "=== DONE ==="
