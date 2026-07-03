"""WTP-DEMO-01 End-to-End Demo Test Suite.
Runs baseline + 7 scenarios + historian query. Saves all results to /tmp/e2e_results.json
"""
import json, os, time, sys

import requests

EDGE_API_KEY = os.environ.get("EDGE_API_KEY", "")
if not EDGE_API_KEY:
    print("ERROR: EDGE_API_KEY environment variable not set.", file=sys.stderr)
    sys.exit(1)

PLANTOS = "http://localhost:8000"
VF = "http://localhost:8100"
HEADERS = {"X-API-Key": EDGE_API_KEY}


def get_current(signal_id):
    """Get current value for a signal."""
    try:
        r = requests.get(f"{PLANTOS}/api/v1/measurements/current", headers=HEADERS, params={"signal_id": signal_id}, timeout=5)
        if r.status_code == 200 and r.json():
            d = r.json()[0]
            return d["value"]
        return f"ERR:{r.status_code}"
    except Exception as e:
        return f"ERR:{e}"


def switch_scenario(scenario_id):
    """Switch VF scenario."""
    r = requests.post(f"{VF}/api/v1/scenarios/{scenario_id}", timeout=5)
    return r.json()


def get_current_scenario():
    r = requests.get(f"{VF}/api/v1/scenarios/current", timeout=5)
    return r.json()


def query_signals(signal_ids, label=""):
    """Query multiple signals and return dict."""
    results = {}
    print(f"\n--- {label} ---")
    for sid in signal_ids:
        val = get_current(sid)
        results[sid] = val
        print(f"  {sid}: {val}")
    return results


def test_scenario(name, scenario_id, signal_ids, wait=35):
    """Run a scenario test."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name} ({scenario_id})")
    print(f"{'='*60}")
    r = switch_scenario(scenario_id)
    print(f"  Switch response: {r.get('status')} -> {scenario_id}")
    print(f"  Waiting {wait}s for transition...")
    time.sleep(wait)
    results = query_signals(signal_ids, f"After {name}")
    return results


# ============ MAIN ============
results = {}

# ---- Part A: Baseline ----
print("\n\n")
print("=" * 60)
print("PART A: BASELINE (Normal Operation)")
print("=" * 60)

# Ensure normal
switch_scenario("normal_operation")
time.sleep(5)

results["baseline"] = {}
results["baseline"]["scenario"] = get_current_scenario()

results["baseline"]["turbidity_chain"] = query_signals([
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "CLARIFIER-101.settled_turbidity",
    "FILTER-QUALITY-STATION-101.filtered_turbidity",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
], "Turbidity Chain (Baseline)")

results["baseline"]["cost_kpis"] = query_signals([
    "ENERGY-MONITORING-STATION-101.specific_energy_consumption",
    "CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3",
    "PLANT-KPI-101.cost_per_m3",
], "Cost KPIs (Baseline)")

results["baseline"]["traceability"] = query_signals([
    "QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score",
    "QUALITY-TRACEABILITY-ENGINE-101.probable_root_cause_code",
], "Traceability (Baseline)")

# ---- Part B: 7 Scenarios ----
results["scenarios"] = {}

# B1: Raw Water Contamination
results["scenarios"]["raw_water_contamination"] = test_scenario(
    "Raw Water Contamination", "raw_water_contamination", [
        "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
        "CLARIFIER-101.settled_turbidity",
        "FILTER-QUALITY-STATION-101.filtered_turbidity",
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
        "QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score",
        "QUALITY-TRACEABILITY-ENGINE-101.probable_root_cause_code",
    ])

# B2: Chemical Overdosing
results["scenarios"]["chemical_overdosing"] = test_scenario(
    "Chemical Overdosing", "chemical_overdosing", [
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine",
        "CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3",
        "PLANT-KPI-101.cost_per_m3",
    ])

# B3: Filter Clogging
results["scenarios"]["filter_clogging_energy_impact"] = test_scenario(
    "Filter Clogging -> Energy Impact", "filter_clogging_energy_impact", [
        "FILTER-101.filter_dp",
        "ENERGY-MONITORING-STATION-101.specific_energy_consumption",
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
        "PLANT-KPI-101.cost_per_m3",
    ])

# B4: Chlorine Underdosing
results["scenarios"]["chlorine_underdosing"] = test_scenario(
    "Chlorine Underdosing", "chlorine_underdosing", [
        "DISINFECTION-QUALITY-STATION-101.free_chlorine",
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine",
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status",
    ])

# B5: Filter Breakthrough
results["scenarios"]["filter_breakthrough"] = test_scenario(
    "Filter Breakthrough", "filter_breakthrough", [
        "FILTER-QUALITY-STATION-101.filtered_turbidity",
        "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
        "QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score",
    ])

# B6: HSP Trip
results["scenarios"]["hsp_trip"] = test_scenario(
    "HSP Trip", "hsp_trip", [
        "HSP-101.flow_rate",
        "OUTLET-MANIFOLD-101.manifold_pressure",
        "OUTLET-MANIFOLD-101.manifold_flow",
        "HSP-102.flow_rate",
    ])

# B7: Algae Bloom
results["scenarios"]["algae_bloom"] = test_scenario(
    "Algae Bloom", "algae_bloom", [
        "RAW-WATER-QUALITY-STATION-101.raw_algae_index",
        "DISINFECTION-QUALITY-STATION-101.free_chlorine",
        "CHEMICAL-CONSUMPTION-STATION-101.chlorine_dose_rate",
    ])

# ---- Part C: Historian ----
print("\n\n")
print("=" * 60)
print("PART C: HISTORIAN VERIFICATION")
print("=" * 60)

results["historian"] = {}
try:
    r = requests.post(
        f"{PLANTOS}/api/v1/historian/query",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "signal_ids": [
                "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
                "CLARIFIER-101.settled_turbidity",
                "FILTER-QUALITY-STATION-101.filtered_turbidity",
                "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
            ],
            "from": "2026-07-02T00:00:00Z",
            "to": "2026-07-02T23:59:59Z",
            "limit": 100,
        },
        timeout=10,
    )
    if r.status_code == 200:
        data = r.json()
        for sig_id, points in data.items():
            if points:
                first = points[0]
                last = points[-1]
                results["historian"][sig_id] = {
                    "points": len(points),
                    "first_value": first["value"],
                    "first_ts": first["timestamp"],
                    "last_value": last["value"],
                    "last_ts": last["timestamp"],
                }
                print(f"  {sig_id}: {len(points)} pts | last={last['value']} @ {last['timestamp']}")
            else:
                results["historian"][sig_id] = {"points": 0}
                print(f"  {sig_id}: NO DATA")
    else:
        print(f"  Historian query failed: HTTP {r.status_code}")
        results["historian"]["error"] = f"HTTP {r.status_code}: {r.text[:200]}"
except Exception as e:
    print(f"  Historian query error: {e}")
    results["historian"]["error"] = str(e)

# ---- Part D: Return to Normal ----
print("\n\nReturning to normal_operation...")
switch_scenario("normal_operation")
results["final_scenario"] = "normal_operation"

# ---- Save all results ----
with open("/tmp/e2e_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print("\n✅ All results saved to /tmp/e2e_results.json")
