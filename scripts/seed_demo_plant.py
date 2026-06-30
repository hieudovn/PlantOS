#!/usr/bin/env python3
"""Seed DEMO-PLANT data into PlantOS via API."""

import argparse
import sys
import httpx

API = "http://localhost:8000/api/v1"


def post(path, data):
    resp = httpx.post(f"{API}{path}", json=data)
    if resp.status_code not in (200, 201):
        print(f"  FAIL {path}: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json()


def seed(api_url):
    global API
    API = api_url.rstrip("/") + "/api/v1"

    print("Seeding DEMO-PLANT...")

    # 1. Plant
    print("  Creating plant...")
    post("/plants", {"plant_id": "DEMO-PLANT", "name": "Demo Plant", "timezone": "Asia/Ho_Chi_Minh"})

    # 2. Areas
    print("  Creating areas...")
    post("/areas", {"area_id": "PROCESS-AREA", "plant_id": "DEMO-PLANT", "name": "Process Area"})
    post("/areas", {"area_id": "ELECTRICAL-AREA", "plant_id": "DEMO-PLANT", "name": "Electrical Area"})

    # 3. Assets
    print("  Creating assets...")
    # Line hierarchy
    post("/assets", {"asset_id": "LINE-01", "name": "Production Line 01", "asset_type": "line", "area_id": "PROCESS-AREA"})
    # Process assets
    post("/assets", {"asset_id": "PUMP-101", "name": "Feed Pump 101", "asset_type": "pump", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01", "criticality": "high", "location": {"lat": 10.7626, "lng": 106.6602}})
    post("/assets", {"asset_id": "MOTOR-101", "name": "Drive Motor 101", "asset_type": "motor", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01", "criticality": "high"})
    post("/assets", {"asset_id": "TANK-101", "name": "Storage Tank 101", "asset_type": "tank", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01"})
    post("/assets", {"asset_id": "VALVE-101", "name": "Control Valve 101", "asset_type": "valve", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01"})
    # Electrical assets
    post("/assets", {"asset_id": "SUBSTATION-A", "name": "Substation A", "asset_type": "substation", "area_id": "ELECTRICAL-AREA"})
    post("/assets", {"asset_id": "TRANSFORMER-01", "name": "Transformer 01", "asset_type": "transformer", "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A", "criticality": "critical"})
    post("/assets", {"asset_id": "FEEDER-01", "name": "Feeder 01", "asset_type": "feeder", "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A"})
    post("/assets", {"asset_id": "BREAKER-01", "name": "Breaker 01", "asset_type": "breaker", "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A"})

    # 4. Signals
    print("  Creating signals...")
    signals = [
        # PUMP-101
        ("PUMP-101.discharge_pressure", "PUMP-101", "discharge_pressure", "Discharge Pressure", "bar", "float"),
        ("PUMP-101.flow_rate", "PUMP-101", "flow_rate", "Flow Rate", "m³/h", "float"),
        ("PUMP-101.running_status", "PUMP-101", "running_status", "Running Status", None, "bool"),
        ("PUMP-101.vibration_rms", "PUMP-101", "vibration_rms", "Vibration RMS", "mm/s", "float"),
        # MOTOR-101
        ("MOTOR-101.motor_current", "MOTOR-101", "motor_current", "Motor Current", "A", "float"),
        ("MOTOR-101.motor_temperature", "MOTOR-101", "motor_temperature", "Motor Temperature", "°C", "float"),
        ("MOTOR-101.running_status", "MOTOR-101", "running_status", "Running Status", None, "bool"),
        # TANK-101
        ("TANK-101.tank_level", "TANK-101", "tank_level", "Tank Level", "%", "float"),
        ("TANK-101.temperature", "TANK-101", "temperature", "Temperature", "°C", "float"),
        # VALVE-101
        ("VALVE-101.valve_position", "VALVE-101", "valve_position", "Valve Position", "%", "float"),
        # TRANSFORMER-01
        ("TRANSFORMER-01.temperature", "TRANSFORMER-01", "temperature", "Temperature", "°C", "float"),
        # FEEDER-01
        ("FEEDER-01.current", "FEEDER-01", "current", "Current", "A", "float"),
        ("FEEDER-01.power", "FEEDER-01", "power", "Active Power", "kW", "float"),
        # BREAKER-01
        ("BREAKER-01.breaker_status", "BREAKER-01", "breaker_status", "Breaker Status", None, "bool"),
        ("BREAKER-01.voltage", "BREAKER-01", "voltage", "Voltage", "kV", "float"),
    ]
    for sig_id, asset_id, name, display, unit, dtype in signals:
        body = {
            "signal_id": sig_id,
            "asset_id": asset_id,
            "signal_name": name,
            "display_name": display,
            "data_type": dtype,
            "signal_type": "measurement" if dtype == "float" else "status",
        }
        if unit:
            body["engineering_unit"] = unit
        body["source"] = {
            "source_type": "simulator",
            "source_ref": f"sim://{sig_id.replace('.', '/')}",
        }
        body["uns_path"] = f"avenue/demo-plant/{asset_id}/{name}"
        post("/signals", body)

    print(f"  Done! Created 1 plant, 2 areas, 9 assets, {len(signals)} signals.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed DEMO-PLANT data")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    args = parser.parse_args()
    seed(args.api_url)
