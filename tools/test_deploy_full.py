"""Phase 8B Security Deploy — Full Pipeline Test"""
import requests, json, sys, os
from datetime import datetime, timezone, timedelta

HOST = "103.97.132.249"
NEW_KEY = os.environ.get("EDGE_API_KEY", "")
OLD_KEY = "plantos-edge-key-2026"

if not NEW_KEY:
    print("ERROR: Set EDGE_API_KEY env var from deployment/.env first!")
    print("  $env:EDGE_API_KEY='plantos-edge-xxx'")
    sys.exit(1)

def test(name, method, url, headers=None, data=None, expect=200, timeout=10):
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            r = requests.post(url, json=data, headers=headers, timeout=timeout)
        else:
            r = requests.request(method, url, headers=headers, timeout=timeout)
        ok = r.status_code == expect
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: HTTP {r.status_code}")
        return r if ok else None
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:80]}")
        return None

print("=" * 65)
print("PHASE 8B SECURITY DEPLOY — FULL PIPELINE TEST")
print(f"Time: {datetime.now(timezone.utc).isoformat()}")
print("=" * 65)

# ═══════════════════════════════════════════════
# 1. BACKEND HEALTH + AUTH
# ═══════════════════════════════════════════════
print("\n--- 1. Backend Health & Auth ---")

# 1a. Health (no auth)
r = test("Health (public)", "GET", f"http://{HOST}:8000/health")
if r: print(f"    version={r.json().get('version','?')}")

# 1b. New key works
h = {"X-API-Key": NEW_KEY}
r = test("Plants (new key)", "GET", f"http://{HOST}:8000/api/v1/plants", headers=h)
plants = []
if r:
    plants = [p['plant_id'] for p in r.json()]
    print(f"    Plants: {plants}")

# 1c. Old key REJECTED
h_old = {"X-API-Key": OLD_KEY}
test("Plants (OLD key - should FAIL)", "GET", f"http://{HOST}:8000/api/v1/plants", headers=h_old, expect=401)

# 1d. No key REJECTED
test("Plants (no key - should FAIL)", "GET", f"http://{HOST}:8000/api/v1/plants", expect=401)

# ═══════════════════════════════════════════════
# 2. SIGNAL REGISTRY
# ═══════════════════════════════════════════════
print("\n--- 2. Signal Registry ---")
for plant_id in plants:
    r = test(f"Signals ({plant_id})", "GET", 
             f"http://{HOST}:8000/api/v1/signals?plant_id={plant_id}", headers=h)
    if r:
        signals = r.json() if isinstance(r.json(), list) else r.json().get("signals", [])
        print(f"    {plant_id}: {len(signals)} signals")

# ═══════════════════════════════════════════════
# 3. DATA FLOW — VF Compressor + WTP
# ═══════════════════════════════════════════════
print("\n--- 3. Data Flow (VF + WTP) ---")

data_checks = {
    "VF Compressor": "COMP01-CORE.speed",
    "WTP Turbidity": "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "WTP Cost KPI": "PLANT-KPI-101.cost_per_m3",
    "WTP Chlorine": "DISINFECTION-QUALITY-STATION-101.free_chlorine",
    "WTP Filter DP": "FILTER-101.filter_dp",
    "VF Motor": "COMP01-MOTOR.current",
}

for label, sid in data_checks.items():
    r = test(label, "GET",
             f"http://{HOST}:8000/api/v1/measurements/history?signal_id={sid}&limit=1",
             headers=h)
    if r:
        d = r.json()
        pts = d.get("data", []) if isinstance(d, dict) else []
        if pts:
            ts = pts[0].get("timestamp", "?")
            val = pts[0].get("value", "?")
            # Check freshness
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                lag = (datetime.now(timezone.utc) - dt).total_seconds()
                fresh = "FRESH" if lag < 120 else f"STALE ({lag/60:.0f}min old)"
            except:
                fresh = "?"
            print(f"    value={val:.1f} | {fresh} | {ts[:19]}")
        else:
            print(f"    NO DATA")

# ═══════════════════════════════════════════════
# 4. EDGE AGENT
# ═══════════════════════════════════════════════
print("\n--- 4. Edge Agent ---")
r = test("Edge nodes", "GET", f"http://{HOST}:8000/api/v1/edge-nodes", headers=h)
if r:
    nodes = r.json() if isinstance(r.json(), list) else r.json().get("nodes", [])
    print(f"    Nodes: {len(nodes)}")
    for n in nodes[:3]:
        hb = n.get("last_heartbeat", "?")
        status = n.get("status", "?")
        print(f"    {n.get('node_id','?')}: status={status} | heartbeat={hb}")

# ═══════════════════════════════════════════════
# 5. VF SIMULATOR
# ═══════════════════════════════════════════════
print("\n--- 5. VF WTP Simulator ---")
for port, label in [(8100, "Scenario API"), (4841, "OPC UA WTP"), (4840, "OPC UA VF")]:
    try:
        r = requests.get(f"http://{HOST}:{port}/", timeout=3)
        print(f"  ✅ {label} ({port}): reachable")
    except:
        print(f"  ⚠️  {label} ({port}): unreachable (expected if not exposed)")

try:
    r = requests.get(f"http://{HOST}:8100/api/v1/scenarios/current", timeout=5)
    if r.status_code == 200:
        print(f"  ✅ Scenario: {r.json().get('scenario_id', '?')}")
except:
    print(f"  ❌ Scenario API: down")

# ═══════════════════════════════════════════════
# 6. FRONTEND
# ═══════════════════════════════════════════════
print("\n--- 6. Frontend ---")
test("Frontend (port 80)", "GET", f"http://{HOST}/")
test("Frontend (port 5173)", "GET", f"http://{HOST}:5173/", expect=None)

# ═══════════════════════════════════════════════
# 7. SUMMARY
# ═══════════════════════════════════════════════
print("\n" + "=" * 65)
print("TEST COMPLETE")
print("=" * 65)
print("""
Manual checks needed in browser:
  [ ] http://103.97.132.249 → Workspace dropdown shows all plants
  [ ] Select WTP-DEMO-01 → 47 Assets, 92 Signals
  [ ] Historian → time range buttons work
  [ ] Historian → graph shows data for all time ranges
  [ ] Diagrams → WTP Process Flow visible
  [ ] Logout button present
  [ ] No 401 errors in browser console (F12)
""")
