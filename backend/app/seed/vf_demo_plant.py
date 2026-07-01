"""Seed data from Integration Data Contract manifest.

Reads examples/vf-plantos-contract.yaml and creates Plant, Area, Assets, and Signals.
Idempotent — skips entities that already exist.

Usage:
    POST /api/v1/seed/vf-demo
"""

import yaml
from pathlib import Path

MANIFEST_PATH = Path("/app/examples/vf-plantos-contract.yaml")


def load_manifest() -> dict:
    """Load the integration contract manifest."""
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def seed_from_manifest():
    """Seed PlantOS Center from the integration manifest."""
    from app.modules.assets.schemas import PlantCreate, AreaCreate, AssetCreate
    from app.modules.assets.service import PlantService, AreaService, AssetService
    from app.modules.signals.schemas import SignalCreate, SourceInfo
    from app.modules.signals.service import SignalService

    manifest = load_manifest()
    plant_svc = PlantService()
    area_svc = AreaService()
    asset_svc = AssetService()
    signal_svc = SignalService()
    results = {"plants": 0, "areas": 0, "assets": 0, "signals": 0, "skipped": 0}

    # Plant
    p = manifest["plant"]
    try:
        plant_svc.create_plant(PlantCreate(
            plant_id=p["plant_id"], name=p["name"],
            timezone="UTC", status="active",
        ))
        results["plants"] += 1
    except ValueError:
        results["skipped"] += 1

    # Areas
    for a in manifest.get("areas", []):
        try:
            area_svc.create_area(AreaCreate(
                area_id=a["area_id"], plant_id=a["plant_id"],
                name=a["name"], area_type=None, status="active",
            ))
            results["areas"] += 1
        except ValueError:
            results["skipped"] += 1

    # Assets (manifest order — parent trước children)
    for a in manifest.get("assets", []):
        try:
            asset_svc.create_asset(AssetCreate(
                asset_id=a["asset_id"], asset_code=a.get("asset_code", a["asset_id"]),
                name=a["name"], asset_type=a["asset_type"],
                parent_asset_id=a.get("parent_asset_id"),
                plant_id=a.get("plant_id"), area_id=a.get("area_id"),
                criticality=a.get("criticality", "medium"),
            ))
            results["assets"] += 1
        except ValueError:
            results["skipped"] += 1

    # Signals
    for s in manifest.get("signals", []):
        try:
            src = SourceInfo(source_type="opcua", source_ref=s["opcua_node_id"])
            signal_svc.create_signal(SignalCreate(
                signal_id=s["signal_id"], asset_id=s["asset_id"],
                signal_name=s["signal_name"],
                display_name=s.get("display_name"),
                signal_type=s.get("signal_type", "measurement"),
                data_type=s.get("data_type", "float"),
                engineering_unit=s.get("engineering_unit"),
                source=src,
            ))
            results["signals"] += 1
        except ValueError:
            results["skipped"] += 1

    return results
