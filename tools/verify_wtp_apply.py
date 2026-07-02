"""Verify WTP apply results on PlantOS."""
import json, sys
from collections import Counter

import requests

HOST = "http://localhost:8000"
HEADERS = {"X-API-Key": "plantos-edge-key-2026"}

# 4a. Asset count + types
print("=== 4a. Asset Count & Types ===")
r = requests.get(f"{HOST}/api/v1/assets?plant_id=WTP-DEMO-01", headers=HEADERS)
assets = r.json()
print(f"Total assets: {len(assets)}")
types = Counter()
for a in assets:
    types[a.get("asset_type", "unknown")] += 1
for t, c in sorted(types.items()):
    print(f"  {t}: {c}")

# 4b. Hierarchy
print("\n=== 4b. Asset Hierarchy ===")
roots = [a for a in assets if not a.get("parent_asset_id")]
children = [a for a in assets if a.get("parent_asset_id")]
print(f"Root assets: {len(roots)}")
print(f"Child assets: {len(children)}")

# Verify specific relationships
for a in assets:
    if a.get("asset_id") == "SCREEN-101":
        print(f"SCREEN-101 parent: {a.get('parent_asset_id')} (expected: INTAKE-STRUCTURE-101)")
    if a.get("asset_id") == "RWP-101-MOTOR":
        print(f"RWP-101-MOTOR parent: {a.get('parent_asset_id')} (expected: RWP-101)")
    if a.get("asset_id") == "HSP-101-MOTOR":
        print(f"HSP-101-MOTOR parent: {a.get('parent_asset_id')} (expected: HSP-101)")

# 4c. Signal count
print("\n=== 4c. Signal Count ===")
r2 = requests.get(f"{HOST}/api/v1/signals?plant_id=WTP-DEMO-01", headers=HEADERS)
signals = r2.json()
print(f"Total signals: {len(signals)}")

# 4d. VF-DEMO intact
print("\n=== 4d. VF-DEMO Intact ===")
r3 = requests.get(f"{HOST}/api/v1/assets?plant_id=VF-DEMO", headers=HEADERS)
vfdemo = r3.json()
print(f"VF-DEMO assets: {len(vfdemo)}")

# 5. Key signals verification
print("\n=== 5. Key Signals (Quality Chain) ===")
key_signals = [
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "CLARIFIER-101.settled_turbidity",
    "FILTER-QUALITY-STATION-101.filtered_turbidity",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
    "DISINFECTION-QUALITY-STATION-101.free_chlorine",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine",
    "ENERGY-MONITORING-STATION-101.specific_energy_consumption",
    "PLANT-KPI-101.cost_per_m3",
    "QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score",
]
signal_ids = {s["signal_id"] for s in signals}
for ks in key_signals:
    status = "✅" if ks in signal_ids else "❌ MISSING"
    print(f"{status} {ks}")

print("\n✅ ALL VERIFICATIONS COMPLETE")
