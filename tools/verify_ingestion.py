"""Verify WTP ingestion current values via PlantOS API."""
import json, os, sys

import requests

EDGE_API_KEY = os.environ.get("EDGE_API_KEY", "")
if not EDGE_API_KEY:
    print("ERROR: EDGE_API_KEY environment variable not set.", file=sys.stderr)
    sys.exit(1)

HOST = "http://localhost:8000"
HEADERS = {"X-API-Key": EDGE_API_KEY}

# A2: Test specific endpoints
test_signals = [
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "CLARIFIER-101.settled_turbidity",
    "FILTER-QUALITY-STATION-101.filtered_turbidity",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
    "PLANT-KPI-101.cost_per_m3",
]

print("=== A2: Current Values (Key Signals) ===")
for sid in test_signals:
    try:
        r = requests.get(
            f"{HOST}/api/v1/signals/{sid}/current",
            headers=HEADERS,
            timeout=5,
        )
        if r.status_code == 200:
            d = r.json()
            print(f"✅ {sid}: {d.get('value')} @ {d.get('timestamp', '?')}")
        else:
            print(f"❌ {sid}: HTTP {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"❌ {sid}: {e}")

# A3: Turbidity chain via historian
print("\n=== A3: Turbidity Chain (Historian) ===")
try:
    r = requests.post(
        f"{HOST}/api/v1/historian/query",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "signal_ids": [
                "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
                "CLARIFIER-101.settled_turbidity",
                "FILTER-QUALITY-STATION-101.filtered_turbidity",
                "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
            ],
            "limit": 3,
        },
        timeout=10,
    )
    if r.status_code == 200:
        data = r.json()
        for sid, points in data.items():
            if points:
                latest = points[-1]
                print(f"✅ {sid}: value={latest.get('value')} @ {latest.get('timestamp', '?')}")
            else:
                print(f"⚠️  {sid}: no data points")
    else:
        print(f"❌ Historian query: HTTP {r.status_code} {r.text[:300]}")
except Exception as e:
    print(f"❌ Historian query error: {e}")

# A4: Sample 10 random signals
print("\n=== A4: Random Signal Sample ===")
sample_signals = [
    "RWP-101.flow_rate",
    "RWP-101-MOTOR.motor_current",
    "COAG-PUMP-101.flow_rate",
    "CHLORINE-PUMP-101.flow_rate",
    "FILTER-101.filter_dp",
    "FILTER-102.filter_dp",
    "DISINFECTION-QUALITY-STATION-101.free_chlorine",
    "ENERGY-MONITORING-STATION-101.total_active_power",
    "PLANT-KPI-101.water_production_today",
    "QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score",
]
success = 0
for sid in sample_signals:
    try:
        r = requests.get(
            f"{HOST}/api/v1/signals/{sid}/current",
            headers=HEADERS,
            timeout=5,
        )
        if r.status_code == 200:
            d = r.json()
            print(f"✅ {sid}: {d.get('value')} ({d.get('timestamp', '?')})")
            success += 1
        else:
            print(f"❌ {sid}: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ {sid}: {e}")

print(f"\n✅ {success}/10 signals returned valid data")
