#!/usr/bin/env python3
"""Seed EDGEV2-DEMO workspace + assets into PlantOS Center via API.

Creates:
  - Workspace/Plant: EDGEV2-DEMO
  - 5 assets: PUMP-101, TANK-101, MOTOR-101, QUALITY-STATION-101, ENERGY-METER-101
  - 7 signals (all prefixed with EDGEV2-)

Usage:
    python scripts/seed_edgev2_demo.py [--api-url http://localhost:8000]
"""

import argparse
import sys
import httpx

API = "http://localhost:8000/api/v1"


def post(path, data, api_key=None):
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    resp = httpx.post(f"{API}{path}", json=data, headers=headers)
    if resp.status_code not in (200, 201):
        print(f"  FAIL {path}: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json()


def seed(api_url, api_key=None):
    global API
    API = api_url.rstrip("/") + "/api/v1"

    print("Seeding EDGEV2-DEMO workspace...")

    # 1. Plant (acts as workspace)
    print("  Creating plant...")
    post("/plants", {
        "plant_id": "EDGEV2-DEMO",
        "name": "Edge v2 Demo Plant",
        "timezone": "Asia/Ho_Chi_Minh",
    }, api_key)

    # 2. Area
    print("  Creating area...")
    post("/areas", {
        "area_id": "EDGEV2-DEMO-AREA",
        "plant_id": "EDGEV2-DEMO",
        "name": "Edge v2 Demo Area",
    }, api_key)

    # 3. Assets (5 assets, all prefixed EDGEV2-)
    print("  Creating assets...")
    assets = [
        {"asset_id": "EDGEV2-PUMP-101", "name": "Edge v2 Feed Pump 101", "asset_type": "pump",
         "area_id": "EDGEV2-DEMO-AREA", "criticality": "high"},
        {"asset_id": "EDGEV2-TANK-101", "name": "Edge v2 Storage Tank 101", "asset_type": "tank",
         "area_id": "EDGEV2-DEMO-AREA"},
        {"asset_id": "EDGEV2-MOTOR-101", "name": "Edge v2 Drive Motor 101", "asset_type": "motor",
         "area_id": "EDGEV2-DEMO-AREA", "criticality": "high"},
        {"asset_id": "EDGEV2-QUALITY-STATION-101", "name": "Edge v2 Quality Station 101",
         "asset_type": "quality_station", "area_id": "EDGEV2-DEMO-AREA"},
        {"asset_id": "EDGEV2-ENERGY-METER-101", "name": "Edge v2 Energy Meter 101",
         "asset_type": "energy_meter", "area_id": "EDGEV2-DEMO-AREA"},
    ]
    for a in assets:
        post("/assets", a, api_key)

    # 4. Signals (7 signals)
    print("  Creating signals...")
    signals = [
        # PUMP-101: 3 signals
        ("EDGEV2-PUMP-101.flow_rate", "EDGEV2-PUMP-101", "flow_rate",
         "Flow Rate", "m³/h", "float", "measurement"),
        ("EDGEV2-PUMP-101.discharge_pressure", "EDGEV2-PUMP-101", "discharge_pressure",
         "Discharge Pressure", "bar", "float", "measurement"),
        ("EDGEV2-PUMP-101.vibration", "EDGEV2-PUMP-101", "vibration",
         "Vibration", "mm/s", "float", "measurement"),
        # TANK-101: 1 signal
        ("EDGEV2-TANK-101.level", "EDGEV2-TANK-101", "level",
         "Tank Level", "%", "float", "measurement"),
        # MOTOR-101: 1 signal
        ("EDGEV2-MOTOR-101.running_status", "EDGEV2-MOTOR-101", "running_status",
         "Running Status", None, "bool", "status"),
        # QUALITY-STATION-101: 1 signal
        ("EDGEV2-QUALITY-STATION-101.turbidity", "EDGEV2-QUALITY-STATION-101", "turbidity",
         "Turbidity", "NTU", "float", "measurement"),
        # ENERGY-METER-101: 1 signal
        ("EDGEV2-ENERGY-METER-101.active_power", "EDGEV2-ENERGY-METER-101", "active_power",
         "Active Power", "kW", "float", "measurement"),
    ]
    for sig_id, asset_id, name, display, unit, dtype, sig_type in signals:
        body = {
            "signal_id": sig_id,
            "asset_id": asset_id,
            "signal_name": name,
            "display_name": display,
            "data_type": dtype,
            "signal_type": sig_type,
            "source": {
                "source_type": "simulator",
                "source_ref": f"sim://{sig_id.replace('.', '/')}",
            },
            "uns_path": f"avenue/edgev2-demo/{asset_id}/{name}",
        }
        if unit:
            body["engineering_unit"] = unit
        post("/signals", body, api_key)

    print("  Done! Created 1 plant, 1 area, 5 assets, 7 signals.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed EDGEV2-DEMO workspace")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    parser.add_argument("--api-key", default=None, help="API key for authentication")
    args = parser.parse_args()
    seed(args.api_url, args.api_key)
