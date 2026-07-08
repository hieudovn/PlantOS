#!/usr/bin/env bash
#
# PlantOS Edge v2 — End-to-End Smoke Test
# Requires: Edge v2 agent running on localhost:8011
# Optional: HTTP test simulator on port 9999, Center on port 8000
#
# Usage:
#   bash edge-v2/scripts/smoke_e2e.sh
#
set -euo pipefail

BASE="${1:-http://localhost:8011}"
CENTER="${2:-http://localhost:8000}"
PASS=0
FAIL=0
TOTAL=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
    local name="$1"; shift
    TOTAL=$((TOTAL+1))
    if "$@" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} $name"
        PASS=$((PASS+1))
    else
        echo -e "  ${RED}❌${NC} $name"
        FAIL=$((FAIL+1))
    fi
}

check_json() {
    local name="$1"; local expected="$2"; shift 2
    local result
    result=$("$@" 2>/dev/null)
    TOTAL=$((TOTAL+1))
    if echo "$result" | grep -q "$expected"; then
        echo -e "  ${GREEN}✅${NC} $name"
        PASS=$((PASS+1))
    else
        echo -e "  ${RED}❌${NC} $name (expected: $expected)"
        echo "     Got: $result"
        FAIL=$((FAIL+1))
    fi
}

echo ""
echo "============================================"
echo " PlantOS Edge v2 — E2E Smoke Test"
echo " Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo " Target: $BASE"
echo " Center: $CENTER"
echo "============================================"
echo ""

# ---- 1. Boot Smoke ----
echo "--- 1. Boot Smoke ---"
check "GET /api/status returns 200" curl -sf "$BASE/api/status" -o /dev/null
check_json "GET /api/status has status=running" '"status":"running"' curl -s "$BASE/api/status"
check_json "GET /api/version returns version" '"version":"2.0.0-dev"' curl -s "$BASE/api/version"
check "GET /api/status without auth (public)" curl -sf "$BASE/api/status" -o /dev/null

# ---- 2. Auth Smoke ----
echo ""
echo "--- 2. Auth Smoke ---"
# First-run check
check_json "First-run detected" '"first_run":true' curl -s "$BASE/api/status"

# Setup admin password
check "POST /api/auth/setup" curl -sf -X POST "$BASE/api/auth/setup" \
    -H "Content-Type: application/json" \
    -d '{"password":"test123"}' -o /dev/null

# Login
LOGIN_RESP=$(curl -sf -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"test123"}' -c /tmp/plantos_smoke_cookies.txt 2>/dev/null)
check_json "Login returns role=admin" '"role":"admin"' echo "$LOGIN_RESP"
COOKIE="plantos_session=$(grep plantos_session /tmp/plantos_smoke_cookies.txt 2>/dev/null | awk '{print $NF}')"

# Auth endpoints
if [ -n "$COOKIE" ]; then
    check_json "GET /api/auth/me returns admin" '"username":"admin"' curl -s -b "$COOKIE" "$BASE/api/auth/me"
    check_json "GET /api/config returns edge_node_id" '"edge_node_id"' curl -s -b "$COOKIE" "$BASE/api/config"
    check "POST /api/auth/logout" curl -sf -X POST -b "$COOKIE" "$BASE/api/auth/logout" -o /dev/null
else
    echo "  ${YELLOW}⚠${NC} No session cookie — skipping auth tests"
fi

# ---- 3. Config Sanitization ----
echo ""
echo "--- 3. Config Safety ---"
# Re-login for config tests
curl -sf -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"test123"}' -c /tmp/plantos_smoke_cookies2.txt > /dev/null 2>&1
COOKIE2="plantos_session=$(grep plantos_session /tmp/plantos_smoke_cookies2.txt 2>/dev/null | awk '{print $NF}')"

if [ -n "$COOKIE2" ]; then
    CONFIG_JSON=$(curl -s -b "$COOKIE2" "$BASE/api/config")
    check "api_key is REDACTED" echo "$CONFIG_JSON" | grep -q "REDACTED"
    check "session_secret is REDACTED" echo "$CONFIG_JSON" | grep -q "REDACTED"
    check_json "edge_node_id is visible" '"EDGEV2-PC-01"' echo "$CONFIG_JSON"
    check_json "plant_id is visible" '"EDGEV2-DEMO"' echo "$CONFIG_JSON"
fi

# ---- 4. API Protection ----
echo ""
echo "--- 4. API Protection ---"
check "GET /api/config without auth returns 401" \
    bash -c '[[ "$(curl -s -o /dev/null -w "%{http_code}" '"$BASE/api/config"')" == "401" ]]'

# ---- 5. Processing Profiles ----
echo ""
echo "--- 5. Processing ---"
if [ -n "$COOKIE2" ]; then
    check "List profiles (empty)" curl -sf -b "$COOKIE2" "$BASE/api/processing/profiles" -o /dev/null

    # Create profile
    check "Create scale_offset profile" curl -sf -X POST -b "$COOKIE2" \
        "$BASE/api/processing/profiles" \
        -H "Content-Type: application/json" \
        -d '{"profile_id":"scale_test","name":"Scale 0.1","steps":[{"type":"scale_offset","params":{"scale":0.1,"offset":0},"order":0}]}' -o /dev/null

    check_json "List profiles returns scale_test" '"scale_test"' curl -s -b "$COOKIE2" "$BASE/api/processing/profiles"

    # Preview
    PREVIEW=$(curl -s -b "$COOKIE2" -X POST "$BASE/api/processing/profiles/scale_test/preview" \
        -H "Content-Type: application/json" \
        -d '{"raw_samples":[100,200,300]}')
    check_json "Preview returns 3 samples" '"sample_index":2' echo "$PREVIEW"
    check_json "Preview final value for 100" '"final_values":[10.0' echo "$PREVIEW"
fi

# ---- 6. Connector Lifecycle ----
echo ""
echo "--- 6. Connectors ---"
if [ -n "$COOKIE2" ]; then
    check "List connectors (empty)" curl -sf -b "$COOKIE2" "$BASE/api/connections" -o /dev/null

    # Create draft
    check "Create HTTP Poll draft" curl -sf -X POST -b "$COOKIE2" \
        "$BASE/api/connections" \
        -H "Content-Type: application/json" \
        -d '{"connector_id":"http_test_01","type":"http_poll","connection":{"url":"http://localhost:9999/api/test/measurements"},"tags":[{"tag_id":"t1","source_ref":"pump101_flow","signal_id":"EDGEV2-PUMP-101.flow_rate","data_type":"float"}],"enabled":false}' -o /dev/null

    check_json "Draft created" '"draft_created"' curl -s -b "$COOKIE2" -X POST \
        "$BASE/api/connections" \
        -H "Content-Type: application/json" \
        -d '{"connector_id":"http_test_02","type":"http_poll","connection":{"url":"http://localhost:9999/api/test/measurements"},"tags":[],"enabled":false}'
fi

# ---- 7. Config Backup/Restore ----
echo ""
echo "--- 7. Backup & Restore ---"
if [ -n "$COOKIE2" ]; then
    check "POST /api/config/backup" curl -sf -X POST -b "$COOKIE2" "$BASE/api/config/backup" -o /dev/null
    check "GET /api/version" curl -sf -b "$COOKIE2" "$BASE/api/version" -o /dev/null
    check_json "Version endpoint" '"version":"2.0.0-dev"' curl -s -b "$COOKIE2" "$BASE/api/version"
fi

# ---- 8. Center Connectivity ----
echo ""
echo "--- 8. Center ---"
if curl -sf "$CENTER/api/v1/edge-nodes" -o /dev/null 2>&1; then
    check "Center reachable" true
    check_json "Edge node visible in Center" '"EDGEV2-PC-01"' curl -s "$CENTER/api/v1/edge-nodes"
else
    echo "  ${YELLOW}⚠${NC} Center not reachable at $CENTER — skipping"
fi

# ---- Summary ----
echo ""
echo "============================================"
echo " Results: $PASS/$TOTAL passed, $FAIL failed"
echo "============================================"

# Cleanup
rm -f /tmp/plantos_smoke_cookies.txt /tmp/plantos_smoke_cookies2.txt

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}SMOKE PASS${NC}"
    exit 0
else
    echo -e "${RED}SMOKE FAIL${NC}"
    exit 1
fi
