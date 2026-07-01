"""Contract preview — compare against current PostgreSQL state.

Read-only: does NOT write to the database.  Reuses existing
AssetRepository and SignalRepository for cross-reference lookups.
"""

from dataclasses import dataclass, field

from app.db.base import get_session
from app.modules.assets.repository import (
    PlantRepository,
    AreaRepository,
    AssetRepository,
)
from app.modules.signals.repository import SignalRepository


@dataclass
class PreviewChanges:
    creates: list[str] = field(default_factory=list)
    updates: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)


@dataclass
class PreviewResult:
    valid: bool
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    plants: PreviewChanges = field(default_factory=PreviewChanges)
    areas: PreviewChanges = field(default_factory=PreviewChanges)
    assets: PreviewChanges = field(default_factory=PreviewChanges)
    signals: PreviewChanges = field(default_factory=PreviewChanges)


def preview_contract(contract_dict: dict) -> PreviewResult:
    """Compare contract against current DB state. Returns diff without writing."""
    result = PreviewResult(valid=True)

    plant_id = contract_dict["plant"]["plant_id"]

    with get_session() as session:
        plant_repo = PlantRepository(session)
        area_repo = AreaRepository(session)
        asset_repo = AssetRepository(session)
        signal_repo = SignalRepository(session)

        # ---- Plants ----
        existing_plant = plant_repo.get_by_id(plant_id)
        if existing_plant:
            result.plants.conflicts.append(plant_id)
        else:
            result.plants.creates.append(plant_id)

        # ---- Areas ----
        existing_areas = area_repo.list_by_plant(plant_id)
        existing_area_ids = {a.area_id for a in existing_areas}
        contract_area_ids = {a["area_id"] for a in contract_dict["areas"]}

        for area_id in contract_area_ids - existing_area_ids:
            result.areas.creates.append(area_id)
        for area_id in contract_area_ids & existing_area_ids:
            result.areas.conflicts.append(area_id)
        for area_id in existing_area_ids - contract_area_ids:
            result.areas.orphans.append(area_id)

        # ---- Assets ----
        existing_assets = asset_repo.list_all(plant_id=plant_id)
        existing_asset_ids = {a.asset_id for a in existing_assets}
        contract_asset_ids = {a["asset_id"] for a in contract_dict["assets"]}

        for asset_id in contract_asset_ids - existing_asset_ids:
            result.assets.creates.append(asset_id)
        for asset_id in contract_asset_ids & existing_asset_ids:
            result.assets.conflicts.append(asset_id)
        for asset_id in existing_asset_ids - contract_asset_ids:
            result.assets.orphans.append(asset_id)

        # ---- Signals ----
        # Get all signals whose asset belongs to this plant
        plant_asset_ids = {a.asset_id for a in existing_assets}
        all_signals = signal_repo.list_all()
        existing_signal_ids = {
            s.signal_id for s in all_signals
            if s.asset.asset_id in plant_asset_ids
        }
        contract_signal_ids = {s["signal_id"] for s in contract_dict["signals"]}

        for sig_id in contract_signal_ids - existing_signal_ids:
            result.signals.creates.append(sig_id)
        for sig_id in contract_signal_ids & existing_signal_ids:
            result.signals.conflicts.append(sig_id)
        for sig_id in existing_signal_ids - contract_signal_ids:
            result.signals.orphans.append(sig_id)

    return result
