#!/usr/bin/env python3
"""Seed EDGEV2-DEMO workspace with mirror signals for comparison."""
import httpx, sys

API = "http://localhost:8000/api/v1"

# Login
resp = httpx.post(f"http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"})
if resp.status_code != 200:
    print(f"Login failed: {resp.status_code}")
    sys.exit(1)
token = resp.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}
print(f"Logged in, token={token[:15]}...")

def post(path, data):
    r = httpx.post(f"{API}{path}", json=data, headers=h)
    if r.status_code in (200, 201):
        print(f"  OK {path}")
    else:
        print(f"  FAIL {path}: {r.status_code} {r.text[:80]}")
        # Don't exit on duplicate - continue

# 1. Plant
print("Creating EDGEV2-DEMO plant...")
post("/plants", {"plant_id": "EDGEV2-DEMO", "name": "Edge v2 Demo Workspace", "timezone": "Asia/Ho_Chi_Minh"})

# 2. Area
print("Creating area...")
post("/areas", {"area_id": "EDGEV2-PROCESS", "plant_id": "EDGEV2-DEMO", "name": "Process Area"})

# 3. Assets (3)
print("Creating assets...")
assets = [
    {"asset_id": "PUMP-101", "name": "Feed Pump 101", "asset_type": "pump", "area_id": "EDGEV2-PROCESS"},
    {"asset_id": "MOTOR-101", "name": "Drive Motor 101", "asset_type": "motor", "area_id": "EDGEV2-PROCESS"},
]
for a in assets:
    post("/assets", a)

# 4. Signals (3 - mirror of v1)
print("Creating signals...")
signals = [
    {"signal_id": "PUMP-101.flow_rate", "asset_id": "PUMP-101", "signal_name": "flow_rate",
     "display_name": "Flow Rate", "engineering_unit": "m3/h", "data_type": "float", "signal_type": "measurement",
     "source": {"source_type": "simulator", "source_ref": "sim://PUMP-101/flow_rate"},
     "uns_path": "avenue/edgev2-demo/PUMP-101/flow_rate"},
    {"signal_id": "PUMP-101.discharge_pressure", "asset_id": "PUMP-101", "signal_name": "discharge_pressure",
     "display_name": "Discharge Pressure", "engineering_unit": "bar", "data_type": "float", "signal_type": "measurement",
     "source": {"source_type": "simulator", "source_ref": "sim://PUMP-101/discharge_pressure"},
     "uns_path": "avenue/edgev2-demo/PUMP-101/discharge_pressure"},
    {"signal_id": "MOTOR-101.motor_current", "asset_id": "MOTOR-101", "signal_name": "motor_current",
     "display_name": "Motor Current", "engineering_unit": "A", "data_type": "float", "signal_type": "measurement",
     "source": {"source_type": "simulator", "source_ref": "sim://MOTOR-101/motor_current"},
     "uns_path": "avenue/edgev2-demo/MOTOR-101/motor_current"},
]
for s in signals:
    post("/signals", s)

print("\nDone! EDGEV2-DEMO seeded.")
