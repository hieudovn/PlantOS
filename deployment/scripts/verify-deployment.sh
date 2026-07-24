#!/usr/bin/env bash
# PlantOS Phase 8 — Assertion-Based Deployment Verification
# Usage:
#   VPS_HOST=<host> ADMIN_USERNAME=<user> ADMIN_PASSWORD=<pass> NEW_API_KEY=<key> ./deployment/scripts/verify-deployment.sh
set -euo pipefail

: "${VPS_HOST:?required}"
: "${ADMIN_USERNAME:?required}"
: "${ADMIN_PASSWORD:?required}"
: "${NEW_API_KEY:?required}"

PASS=0
FAIL=0
BASE="https://${VPS_HOST}"

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
    actual=$(curl -sk -o /dev/null -w "%{http_code}" -X POST "$url" -H "Content-Type: application/json" -d "$data")
  else
    actual=$(curl -sk -o /dev/null -w "%{http_code}" "$url")
  fi
  assert_eq "$label" "$expected" "$actual"
}

echo "=== Phase 8 Deployment Verification ==="
echo "VPS_HOST: ${VPS_HOST}"
echo ""

# 1. Backend health via HTTPS
assert_http "Backend health (HTTPS)" "200" "${BASE}/api/v1/health"

# 2. Frontend via HTTPS
assert_http "Frontend (HTTPS)" "200" "${BASE}/"

# 3. HTTP redirects to HTTPS
assert_http "HTTP→HTTPS redirect" "301" "http://${VPS_HOST}/"

# 4. User login
LOGIN_JSON=$(printf '{"username":"%s","password":"%s"}' "$ADMIN_USERNAME" "$ADMIN_PASSWORD")
LOGIN_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" -X POST "${BASE}/api/v1/auth/login" \
  -H "Content-Type: application/json" -d "$LOGIN_JSON")
if [ "$LOGIN_STATUS" = "200" ]; then
  echo "PASS: User login (${LOGIN_STATUS})"
  PASS=$((PASS + 1))
else
  echo "FAIL: User login returned ${LOGIN_STATUS}"
  FAIL=$((FAIL + 1))
fi

# 5. Old default API key rejected
OLD_KEY_CODE=$(curl -sk -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: plantos-edge-key-2026" \
  "${BASE}/api/v1/assets")
if [ "$OLD_KEY_CODE" = "401" ] || [ "$OLD_KEY_CODE" = "403" ]; then
  echo "PASS: Old API key rejected (${OLD_KEY_CODE})"
  PASS=$((PASS + 1))
else
  echo "FAIL: Old API key returned ${OLD_KEY_CODE}, expected 401/403"
  FAIL=$((FAIL + 1))
fi

# 6. New API key accepted
NEW_KEY_CODE=$(curl -sk -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: ${NEW_API_KEY}" \
  "${BASE}/api/v1/assets")
if [ "$NEW_KEY_CODE" = "200" ] || [ "$NEW_KEY_CODE" = "404" ]; then
  echo "PASS: New API key accepted (${NEW_KEY_CODE})"
  PASS=$((PASS + 1))
else
  echo "FAIL: New API key returned ${NEW_KEY_CODE}"
  FAIL=$((FAIL + 1))
fi

# 7. PostgreSQL healthy
if ssh -o ConnectTimeout=5 root@"${VPS_HOST}" 'docker exec plantos-postgres pg_isready -U plantos -d plantos' 2>/dev/null; then
  echo "PASS: PostgreSQL healthy"
  PASS=$((PASS + 1))
else
  echo "FAIL: PostgreSQL not reachable"
  FAIL=$((FAIL + 1))
fi

# 8. Edge v2 health (via SSH, edge bound to localhost)
if ssh -o ConnectTimeout=5 root@"${VPS_HOST}" 'curl -sf http://localhost:8011/health' 2>/dev/null; then
  echo "PASS: Edge v2 health"
  PASS=$((PASS + 1))
else
  echo "FAIL: Edge v2 health check failed"
  FAIL=$((FAIL + 1))
fi

# 9. Port 8011 rejected externally
EDGE_EXT=$(curl -sk -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://${VPS_HOST}:8011/" 2>/dev/null || echo "000")
assert_eq "Port 8011 rejected externally" "000" "$EDGE_EXT"

# 10. Port 8001 rejected externally
PORT8001=$(curl -sk -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://${VPS_HOST}:8001/" 2>/dev/null || echo "000")
assert_eq "Port 8001 rejected externally" "000" "$PORT8001"

# 11. No unexpected public ports
echo "=== External Port Scan ==="
UNEXPECTED=0
for port in 4840 4841 7000 8002 8100 9998 9999; do
  code=$(curl -sk -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://${VPS_HOST}:${port}/" 2>/dev/null || echo "000")
  if [ "$code" != "000" ]; then
    echo "  UNEXPECTED: port ${port} returned ${code}"
    UNEXPECTED=$((UNEXPECTED + 1))
  fi
done
if [ "$UNEXPECTED" -eq 0 ]; then
  echo "PASS: No unexpected public ports"
  PASS=$((PASS + 1))
else
  echo "FAIL: ${UNEXPECTED} unexpected public port(s)"
  FAIL=$((FAIL + 1))
fi

# Summary
echo ""
echo "=== VERIFICATION COMPLETE ==="
echo "PASS: ${PASS}"
echo "FAIL: ${FAIL}"
if [ "$FAIL" -gt 0 ]; then
  echo "DEPLOYMENT VERIFICATION FAILED"
  exit 1
fi
echo "DEPLOYMENT VERIFIED"
exit 0
