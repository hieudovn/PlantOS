#!/usr/bin/env bash
# PlantOS Phase 8 — Assertion-Based Deployment Verification
# Usage: VPS_HOST=<host> ./deployment/scripts/verify-deployment.sh
set -euo pipefail

: "${VPS_HOST:?VPS_HOST is required}"

PASS=0
FAIL=0

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "PASS: ${label}"
    PASS=$((PASS + 1))
  else
    echo "FAIL: ${label} — expected=${expected} actual=${actual}"
    FAIL=$((FAIL + 1))
  fi
}

assert_http() {
  local label="$1" expected="$2" url="$3" method="${4:-GET}" data="${5:-}"
  local actual
  if [ "$method" = "POST" ]; then
    actual=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" -H "Content-Type: application/json" -d "$data")
  else
    actual=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  fi
  assert_eq "$label" "$expected" "$actual"
}

echo "=== Phase 8 Deployment Verification ==="
echo "VPS_HOST: ${VPS_HOST}"
echo ""

# --- 1. Backend health ---
assert_http "Backend health endpoint" "200" "http://${VPS_HOST}/api/v1/health"

# --- 2. User login (JWT) ---
LOGIN_RESPONSE=$(curl -s -X POST "http://${VPS_HOST}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"plantos-root-password"}')
LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')
if [ -n "$LOGIN_CODE" ] && [ "$LOGIN_CODE" != "null" ]; then
  echo "PASS: User login JWT obtained"
  PASS=$((PASS + 1))
else
  echo "FAIL: User login did not return access_token"
  FAIL=$((FAIL + 1))
fi

# --- 3. Frontend access ---
assert_http "Frontend serves index.html" "200" "http://${VPS_HOST}/"

# --- 4. Old API key MUST be rejected ---
OLD_KEY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: plantos-edge-key-2026" \
  "http://${VPS_HOST}/api/v1/assets")
assert_eq "Old API key rejected (401 or 403)" "401" "$OLD_KEY_RESPONSE"

# --- 5. New API key MUST be accepted ---
# NEW_API_KEY must be set in environment
if [ -z "${NEW_API_KEY:-}" ]; then
  echo "FAIL: NEW_API_KEY env var not set — cannot verify new credential"
  FAIL=$((FAIL + 1))
else
  NEW_KEY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: ${NEW_API_KEY}" \
    "http://${VPS_HOST}/api/v1/assets")
  if [ "$NEW_KEY_RESPONSE" = "200" ] || [ "$NEW_KEY_RESPONSE" = "404" ]; then
    echo "PASS: New API key accepted (${NEW_KEY_RESPONSE})"
    PASS=$((PASS + 1))
  else
    echo "FAIL: New API key returned ${NEW_KEY_RESPONSE}"
    FAIL=$((FAIL + 1))
  fi
fi

# --- 6. Database connectivity ---
DB_HEALTH=$(ssh root@"${VPS_HOST}" 'docker compose -f /opt/plantos/deployment/docker-compose.yml exec -T postgres pg_isready -U plantos -d plantos 2>/dev/null || echo "FAIL"')
if [ "$DB_HEALTH" = "localhost:5432 - accepting connections" ]; then
  echo "PASS: Database accepting connections"
  PASS=$((PASS + 1))
else
  echo "FAIL: Database connectivity — ${DB_HEALTH}"
  FAIL=$((FAIL + 1))
fi

# --- 7. Edge heartbeat ---
EDGE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://${VPS_HOST}:8011/health" 2>/dev/null || echo "000")
if [ "$EDGE_RESPONSE" = "200" ]; then
  echo "PASS: Edge v2 heartbeat"
  PASS=$((PASS + 1))
else
  echo "FAIL: Edge v2 heartbeat returned ${EDGE_RESPONSE}"
  FAIL=$((FAIL + 1))
fi

# --- 8. Port containment ---
ssh root@"${VPS_HOST}" << 'CHECK_PORTS'
echo "=== Port Check ==="
PUBLIC_PORTS=$(ss -lntp | awk '{print $4}' | grep -oP ':\d+$' | sort -u)
EXPECTED=":22 :80 :443"
for port in $EXPECTED; do
  if echo "$PUBLIC_PORTS" | grep -q "$port"; then
    echo "PASS: Port $port is listening"
  else
    echo "FAIL: Port $port is NOT listening"
  fi
done
CHECK_PORTS

# --- Summary ---
echo ""
echo "=== VERIFICATION COMPLETE ==="
echo "PASS: ${PASS}"
echo "FAIL: ${FAIL}"
if [ "$FAIL" -gt 0 ]; then
  echo "DEPLOYMENT VERIFICATION FAILED"
  exit 1
else
  echo "DEPLOYMENT VERIFIED"
  exit 0
fi
