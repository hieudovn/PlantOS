"""Verify WTP ingestion via measurements/current endpoint."""
import json

import requests

HOST = "http://localhost:8000"
HEADERS = {"X-API-Key": "plantos-edge-key-2026"}

# Turbidity chain
print("=== Turbidity Chain ===")
turbidity_signals = [
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "CLARIFIER-101.settled_turbidity",
    "FILTER-QUALITY-STATION-101.filtered_turbidity",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
]
for sid in turbidity_signals:
    r = requests.get(f"{HOST}/api/v1/measurements/current", headers=HEADERS, params={"signal_id": sid})
    if r.status_code == 200 and r.json():
        d = r.json()[0]
        print(f"✅ {sid}: {d['value']} @ {d['timestamp']}")
    else:
        print(f"❌ {sid}: HTTP {r.status_code} {r.text[:100]}")

# Key signals
print("\n=== Key Signals ===")
key_signals = [
    "DISINFECTION-QUALITY-STATION-101.free_chlorine",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine",
    "ENERGY-MONITORING-STATION-101.specific_energy_consumption",
    "PLANT-KPI-101.cost_per_m3",
    "QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score",
    "RWP-101.flow_rate",
    "RWP-101-MOTOR.motor_current",
    "COAG-PUMP-101.flow_rate",
    "FILTER-101.filter_dp",
    "PLANT-KPI-101.water_production_today",
]
success = 0
for sid in key_signals:
    r = requests.get(f"{HOST}/api/v1/measurements/current", headers=HEADERS, params={"signal_id": sid})
    if r.status_code == 200 and r.json():
        d = r.json()[0]
        print(f"✅ {sid}: {d['value']} @ {d['timestamp']}")
        success += 1
    else:
        print(f"❌ {sid}: HTTP {r.status_code}")

print(f"\n✅ {success}/10 signals returned valid data")
