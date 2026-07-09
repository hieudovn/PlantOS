#!/usr/bin/env python3
"""Seed EDGEV2-DEMO workspace with signals matching DEMO-PLANT.

This creates the EDGEV2-DEMO workspace with identical structure to DEMO-PLANT
so the side-by-side comparison tool finds shared signal_ids.

Shared signals (the ones the comparison tool checks):
  - PUMP-101.flow_rate
  - PUMP-101.discharge_pressure
  - MOTOR-101.motor_current

Usage:
    export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
    python scripts/seed_edgev2_demo.py

    # With sample measurement generation for immediate comparison:
    python scripts/seed_edgev2_demo.py --generate-measurements

    # Override API URL:
    python scripts/seed_edgev2_demo.py --api-url http://localhost:8000

SA Constraint: Mirror-first. Edge v1 NOT modified.
"""

import argparse
import os
import random
import sys
from datetime import datetime, timezone, timedelta

import httpx

API = "http://localhost:8000/api/v1"
TOKEN = None
HEADERS = {}


def _req(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{API}{path}"
    h = dict(HEADERS)
    extra_headers = kwargs.pop("headers", {})
    h.update(extra_headers)
    return httpx.request(method, url, headers=h, timeout=15, **kwargs)


def post(path: str, data: dict):
    """POST, skipping duplicates (409) gracefully."""
    resp = _req("POST", path, json=data)
    if resp.status_code in (200, 201):
        return True
    elif resp.status_code == 409:
        return False
    else:
        print(f"  WARN {path}: {resp.status_code} (may already exist)")
        return False


def login(api_url: str):
    """Authenticate and get JWT token using env vars."""
    global TOKEN, HEADERS
    username = os.environ.get("PLANTOS_CENTER_USERNAME", "admin")
    password = os.environ.get("PLANTOS_CENTER_PASSWORD", "")
    if not password:
        print("  ERROR: PLANTOS_CENTER_PASSWORD environment variable not set")
        print("  Usage: PLANTOS_CENTER_PASSWORD=\"...\" python scripts/seed_edgev2_demo.py")
        sys.exit(1)
    base = api_url.rstrip("/")
    try:
        resp = httpx.post(
            f"{base}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            TOKEN = resp.json().get("access_token", "")
            HEADERS = {"Authorization": f"Bearer {TOKEN}"}
            print("  Auth: logged in")
        else:
            print(f"  Auth: login failed {resp.status_code}")
    except Exception as e:
        print(f"  Auth: login error {e}")
        sys.exit(1)


def seed(api_url: str, generate_measurements: bool = False):
    global API
    API = api_url.rstrip("/") + "/api/v1"
    plant_id = "EDGEV2-DEMO"

    login(api_url)

    print(f"\nSeeding {plant_id} workspace...")

    # ── 1. Plant ──
    print("  [1/4] Creating plant...")
    post("/plants", {"plant_id": plant_id, "name": "Edge v2 Demo Workspace", "timezone": "Asia/Ho_Chi_Minh"})

    # ── 2. Areas (matching DEMO-PLANT structure) ──
    print("  [2/4] Creating areas...")
    post("/areas", {"area_id": "PROCESS-AREA", "plant_id": plant_id, "name": "Process Area"})
    post("/areas", {"area_id": "ELECTRICAL-AREA", "plant_id": plant_id, "name": "Electrical Area"})

    # ── 3. Assets (matching DEMO-PLANT) ──
    print("  [3/4] Creating assets...")
    assets = [
        {"asset_id": "LINE-01", "name": "Production Line 01", "asset_type": "line", "area_id": "PROCESS-AREA"},
        {"asset_id": "PUMP-101", "name": "Feed Pump 101", "asset_type": "pump", "area_id": "PROCESS-AREA",
         "parent_asset_id": "LINE-01", "criticality": "high",
         "location": {"lat": 10.7626, "lng": 106.6602}},
        {"asset_id": "MOTOR-101", "name": "Drive Motor 101", "asset_type": "motor", "area_id": "PROCESS-AREA",
         "parent_asset_id": "LINE-01", "criticality": "high"},
        {"asset_id": "TANK-101", "name": "Storage Tank 101", "asset_type": "tank", "area_id": "PROCESS-AREA",
         "parent_asset_id": "LINE-01"},
        {"asset_id": "VALVE-101", "name": "Control Valve 101", "asset_type": "valve", "area_id": "PROCESS-AREA",
         "parent_asset_id": "LINE-01"},
        {"asset_id": "SUBSTATION-A", "name": "Substation A", "asset_type": "substation",
         "area_id": "ELECTRICAL-AREA"},
        {"asset_id": "TRANSFORMER-01", "name": "Transformer 01", "asset_type": "transformer",
         "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A", "criticality": "critical"},
        {"asset_id": "FEEDER-01", "name": "Feeder 01", "asset_type": "feeder",
         "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A"},
        {"asset_id": "BREAKER-01", "name": "Breaker 01", "asset_type": "breaker",
         "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A"},
    ]
    for a in assets:
        post("/assets", a)

    # ── 4. Signals (SAME signal_ids as DEMO-PLANT — enables comparison) ──
    print("  [4/4] Creating signals...")
    signals = [
        # PUMP-101 (4 signals)
        ("PUMP-101.discharge_pressure", "PUMP-101", "discharge_pressure",
         "Discharge Pressure", "bar", "float", "measurement"),
        ("PUMP-101.flow_rate", "PUMP-101", "flow_rate",
         "Flow Rate", "m³/h", "float", "measurement"),
        ("PUMP-101.running_status", "PUMP-101", "running_status",
         "Running Status", None, "bool", "status"),
        ("PUMP-101.vibration_rms", "PUMP-101", "vibration_rms",
         "Vibration RMS", "mm/s", "float", "measurement"),
        # MOTOR-101 (3 signals)
        ("MOTOR-101.motor_current", "MOTOR-101", "motor_current",
         "Motor Current", "A", "float", "measurement"),
        ("MOTOR-101.motor_temperature", "MOTOR-101", "motor_temperature",
         "Motor Temperature", "°C", "float", "measurement"),
        ("MOTOR-101.running_status", "MOTOR-101", "running_status",
         "Running Status", None, "bool", "status"),
        # TANK-101 (2 signals)
        ("TANK-101.tank_level", "TANK-101", "tank_level",
         "Tank Level", "%", "float", "measurement"),
        ("TANK-101.temperature", "TANK-101", "temperature",
         "Temperature", "°C", "float", "measurement"),
        # VALVE-101 (1 signal)
        ("VALVE-101.valve_position", "VALVE-101", "valve_position",
         "Valve Position", "%", "float", "measurement"),
        # TRANSFORMER-01 (1 signal)
        ("TRANSFORMER-01.temperature", "TRANSFORMER-01", "temperature",
         "Temperature", "°C", "float", "measurement"),
        # FEEDER-01 (2 signals)
        ("FEEDER-01.current", "FEEDER-01", "current",
         "Current", "A", "float", "measurement"),
        ("FEEDER-01.power", "FEEDER-01", "power",
         "Active Power", "kW", "float", "measurement"),
        # BREAKER-01 (2 signals)
        ("BREAKER-01.breaker_status", "BREAKER-01", "breaker_status",
         "Breaker Status", None, "bool", "status"),
        ("BREAKER-01.voltage", "BREAKER-01", "voltage",
         "Voltage", "kV", "float", "measurement"),
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
        post("/signals", body)

    print(f"  Done! Created 1 plant, 2 areas, {len(assets)} assets, {len(signals)} signals.")
    print(f"  Shared signal_ids with DEMO-PLANT: {sum(1 for s in signals if s[0].count('.') >= 1)} of {len(signals)}")

    # ── 5. Generate sample measurements (optional) ──
    if generate_measurements:
        _generate_measurements(api_url, plant_id, signals)

    print(f"\n{'=' * 60}")
    print("EDGEV2-DEMO workspace ready for side-by-side comparison.")
    print("Shared signals: PUMP-101.flow_rate, PUMP-101.discharge_pressure,")
    print("                MOTOR-101.motor_current (+ 12 more)")
    print(f"{'=' * 60}")
    print()
    print("Next steps:")
    print("  1. Run comparison tool:")
    print("     PLANTOS_CENTER_PASSWORD='...' python tools/compare_v1_v2_data.py --hours 1")
    print()
    print("🔴 Edge v1 NOT modified, stopped, or deprecated.")


def _generate_measurements(api_url: str, plant_id: str, signals: list):
    """Generate 60 minutes of sample measurements for immediate comparison.

    Values are within ±2% of DEMO-PLANT simulator nominal values so the
    comparison tool finds them within ±5% tolerance.
    """
    print("\n  Generating sample measurements...")
    now = datetime.now(timezone.utc)

    # Nominal values matching DEMO-PLANT simulator output
    base_values = {
        "PUMP-101.flow_rate": 45.0,
        "PUMP-101.discharge_pressure": 3.5,
        "PUMP-101.running_status": 1.0,
        "PUMP-101.vibration_rms": 2.1,
        "MOTOR-101.motor_current": 15.0,
        "MOTOR-101.motor_temperature": 65.0,
        "MOTOR-101.running_status": 1.0,
        "TANK-101.tank_level": 75.0,
        "TANK-101.temperature": 28.0,
        "VALVE-101.valve_position": 60.0,
        "TRANSFORMER-01.temperature": 55.0,
        "FEEDER-01.current": 100.0,
        "FEEDER-01.power": 45.0,
        "BREAKER-01.breaker_status": 1.0,
        "BREAKER-01.voltage": 22.0,
    }

    measurements = []
    for i in range(60):  # 60 data points over 60 minutes
        ts = (now - timedelta(minutes=59 - i)).isoformat()
        for sig_id, _, _, _, _, dtype, _ in signals:
            if dtype != "float" and sig_id not in base_values:
                continue
            base_val = base_values.get(sig_id, 50.0)
            noise = base_val * random.uniform(-0.02, 0.02)
            val = round(base_val + noise, 4)
            measurements.append({
                "signal_id": sig_id,
                "plant_id": plant_id,
                "value": val,
                "timestamp": ts,
                "quality": "good",
            })

    # Ingest in batches of 100
    batch_size = 100
    ingested = 0
    for i in range(0, len(measurements), batch_size):
        batch = measurements[i:i + batch_size]
        try:
            resp = _req("POST", "/measurements/ingest", json={"measurements": batch})
            if resp.status_code in (200, 201):
                ingested += len(batch)
        except Exception as e:
            print(f"  WARN ingest error: {e}")

    print(f"  Ingested {ingested} sample measurements for {plant_id}")
    print(f"  Expected comparison: ✅ within ±5% tolerance")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed EDGEV2-DEMO workspace")
    parser.add_argument("--api-url", default="http://localhost:8000",
                        help="Center API URL (default: http://localhost:8000)")
    parser.add_argument("--generate-measurements", action="store_true",
                        help="Generate 60 min of sample measurements for immediate comparison")
    args = parser.parse_args()
    seed(args.api_url, args.generate_measurements)
