#!/usr/bin/env python3
"""Seed EDGEV2-TEST workspace for dry-run migration tests.

Creates:
  - Plant: EDGEV2-TEST
  - 3 test assets
  - 5 test signals

Usage:
    python scripts/seed_edgev2_test.py [--api-url http://localhost:8000]
"""

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

    print("Seeding EDGEV2-TEST workspace for dry-run migration test...")

    # 1. Plant
    print("  Creating plant...")
    post("/plants", {
        "plant_id": "EDGEV2-TEST",
        "name": "Edge v2 Test Workspace (Dry-Run)",
        "timezone": "Asia/Ho_Chi_Minh",
    })

    # 2. Area
    print("  Creating area...")
    post("/areas", {
        "area_id": "EDGEV2-TEST-AREA",
        "plant_id": "EDGEV2-TEST",
        "name": "Test Area",
    })

    # 3. Assets (3 test assets)
    print("  Creating assets...")
    assets = [
        {"asset_id": "TEST-PUMP-001", "name": "Test Pump 001", "asset_type": "pump",
         "area_id": "EDGEV2-TEST-AREA", "criticality": "low"},
        {"asset_id": "TEST-TANK-001", "name": "Test Tank 001", "asset_type": "tank",
         "area_id": "EDGEV2-TEST-AREA"},
        {"asset_id": "TEST-MOTOR-001", "name": "Test Motor 001", "asset_type": "motor",
         "area_id": "EDGEV2-TEST-AREA", "criticality": "low"},
    ]
    for a in assets:
        post("/assets", a)

    # 4. Signals (5 signals)
    print("  Creating signals...")
    signals = [
        ("TEST-PUMP-001.flow_rate", "TEST-PUMP-001", "flow_rate",
         "Flow Rate", "m³/h", "float", "measurement"),
        ("TEST-PUMP-001.pressure", "TEST-PUMP-001", "pressure",
         "Discharge Pressure", "bar", "float", "measurement"),
        ("TEST-TANK-001.level", "TEST-TANK-001", "level",
         "Tank Level", "%", "float", "measurement"),
        ("TEST-TANK-001.temperature", "TEST-TANK-001", "temperature",
         "Temperature", "°C", "float", "measurement"),
        ("TEST-MOTOR-001.running_status", "TEST-MOTOR-001", "running_status",
         "Running Status", None, "bool", "status"),
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
            "uns_path": f"avenue/edgev2-test/{asset_id}/{name}",
        }
        if unit:
            body["engineering_unit"] = unit
        post("/signals", body)

    print("  Done! Created 1 plant, 1 area, 3 assets, 5 signals.")
    print()
    print("Now run the dry-run migration test:")
    print("  1. python tools/migrate_v1_config_to_v2.py --dry-run")
    print("  2. python tools/compare_v1_v2_data.py --v1-workspace EDGEV2-TEST --v2-workspace EDGEV2-TEST --hours 1")
    print("  3. Follow docs/runbooks/edge-v1-to-v2-migration.md (Phase 1-3 only)")
    print("  4. Follow docs/runbooks/edge-v1-to-v2-rollback.md (verify v1 resume)")

    print()
    print("🔴 Edge v1 NOT modified, stopped, or deprecation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed EDGEV2-TEST workspace")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    args = parser.parse_args()
    seed(args.api_url)
