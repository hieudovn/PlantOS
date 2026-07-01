"""Contract apply — safe import into PostgreSQL via existing service layer.

This is the ONLY endpoint in the contracts module that writes to the database.
Default policy is safest possible: on_conflict=fail, no deletes, no silent overwrites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text

from app.db.base import get_session
from app.modules.assets.models import Asset, Plant
from app.modules.assets.repository import AssetRepository, PlantRepository
from app.modules.signals.models import Signal
from app.modules.signals.repository import SignalRepository


@dataclass
class ApplyResult:
    success: bool
    created: dict = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": [],
    })
    updated: dict = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": [],
    })
    skipped: dict = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": [],
    })
    orphaned: dict = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": [],
    })
    deactivated: dict = field(default_factory=lambda: {
        "plants": [], "areas": [], "assets": [], "signals": [],
    })
    errors: list[str] = field(default_factory=list)


def apply_contract(contract_dict: dict, import_policy: dict) -> ApplyResult:
    """Execute contract import. Writes to PostgreSQL via repository layer."""
    result = ApplyResult(success=True)
    mode = import_policy.get("mode", "validate_only")

    if mode != "apply":
        result.errors.append(f"import_policy.mode must be 'apply', got '{mode}'")
        result.success = False
        return result

    on_conflict = import_policy.get("on_conflict", "fail")
    allow_update = import_policy.get("allow_update_existing", False)
    allow_delete = import_policy.get("allow_delete_missing", False)
    orphaned_action = import_policy.get("orphaned_action", "report")

    if orphaned_action == "delete" and not allow_delete:
        result.errors.append("orphaned_action='delete' requires allow_delete_missing=true")
        result.success = False
        return result

    plant_id = contract_dict["plant"]["plant_id"]

    with get_session() as session:
        plant_repo = PlantRepository(session)
        asset_repo = AssetRepository(session)
        signal_repo = SignalRepository(session)

        # =====================================================================
        # 1. Plant
        # =====================================================================
        existing_plant = plant_repo.get_by_id(plant_id)
        if existing_plant:
            if on_conflict == "fail":
                result.errors.append(f"Plant '{plant_id}' already exists (on_conflict=fail)")
                result.success = False
                return result
            elif on_conflict == "skip":
                result.skipped["plants"].append(plant_id)
            elif on_conflict == "update" and allow_update:
                _update_plant_simple(session, existing_plant.id, contract_dict["plant"])
                result.updated["plants"].append(plant_id)
        else:
            new_plant = Plant(
                plant_id=plant_id,
                name=contract_dict["plant"].get("name", plant_id),
            )
            plant_repo.create(new_plant)
            # Re-fetch to get the generated UUID
            existing_plant = plant_repo.get_by_id(plant_id)
            result.created["plants"].append(plant_id)

        session.commit()

        # =====================================================================
        # 2. Areas
        # =====================================================================
        if existing_plant is None:
            existing_plant = plant_repo.get_by_id(plant_id)

        for area in contract_dict["areas"]:
            area_id = area["area_id"]
            existing = _get_area_by_id(session, area_id)
            if existing:
                if on_conflict == "fail" or on_conflict == "skip":
                    result.skipped["areas"].append(area_id)
                    continue
                elif on_conflict == "update" and allow_update:
                    _update_area_simple(session, existing.id, area)
                    result.updated["areas"].append(area_id)
            else:
                _insert_area(session, area, existing_plant.id)
                result.created["areas"].append(area_id)

        session.commit()

        # =====================================================================
        # 3. Assets
        # =====================================================================
        for asset in contract_dict["assets"]:
            asset_id = asset["asset_id"]
            existing = asset_repo.get_by_id(asset_id)
            if existing:
                if on_conflict == "fail" or on_conflict == "skip":
                    result.skipped["assets"].append(asset_id)
                    continue
                elif on_conflict == "update" and allow_update:
                    result.updated["assets"].append(asset_id)
            else:
                _insert_asset(session, asset, contract_dict["areas"])
                result.created["assets"].append(asset_id)

        session.commit()

        # =====================================================================
        # 4. Signals
        # =====================================================================
        for sig in contract_dict["signals"]:
            sig_id = sig["signal_id"]
            existing = signal_repo.get_by_id(sig_id)
            if existing:
                if on_conflict == "fail" or on_conflict == "skip":
                    result.skipped["signals"].append(sig_id)
                    continue
                elif on_conflict == "update" and allow_update:
                    result.updated["signals"].append(sig_id)
            else:
                _insert_signal(session, sig, contract_dict["assets"])
                result.created["signals"].append(sig_id)

        session.commit()

        # =====================================================================
        # 5. Orphan handling
        # =====================================================================
        if orphaned_action != "report":
            existing_asset_ids = _get_asset_ids_for_plant(session, plant_id)
            contract_asset_ids = {a["asset_id"] for a in contract_dict["assets"]}
            orphaned_asset_ids = existing_asset_ids - contract_asset_ids

            for aid in orphaned_asset_ids:
                result.orphaned["assets"].append(aid)
                if orphaned_action == "deactivate":
                    _deactivate_asset(session, aid)
                    result.deactivated["assets"].append(aid)

            existing_signal_ids = _get_signal_ids_for_plant(session, plant_id)
            contract_signal_ids = {s["signal_id"] for s in contract_dict["signals"]}
            orphaned_signal_ids = existing_signal_ids - contract_signal_ids

            for sid in orphaned_signal_ids:
                result.orphaned["signals"].append(sid)
                if orphaned_action == "deactivate":
                    _deactivate_signal(session, sid)
                    result.deactivated["signals"].append(sid)

        session.commit()

    return result


# =========================================================================
# Internal helpers
# =========================================================================


def _get_area_by_id(session, area_id: str):
    """Return area row (with .id UUID) or None."""
    rows = session.execute(
        text("SELECT id, area_id FROM areas WHERE area_id = :aid"),
        {"aid": area_id},
    ).fetchall()
    return rows[0] if rows else None


def _get_asset_id_map(session, areas: list[dict]) -> dict[str, UUID]:
    """Build {area_id_str -> assets.id UUID} lookup utility."""
    area_ids = [a["area_id"] for a in areas]
    rows = session.execute(
        text("SELECT area_id, id FROM areas WHERE area_id = ANY(:aids)"),
        {"aids": area_ids},
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def _update_plant_simple(session, plant_uuid: UUID, plant_data: dict):
    session.execute(
        text("UPDATE plants SET name=:name WHERE id=:pid"),
        {"pid": plant_uuid, "name": plant_data.get("name", "")},
    )


def _insert_area(session, area: dict, plant_uuid: UUID):
    """Insert area using ORM model to handle all column defaults."""
    from app.modules.assets.models import Area
    new_area = Area(
        area_id=area["area_id"],
        name=area["name"],
        plant_id_fk=plant_uuid,
        status=area.get("status", "active"),
    )
    session.add(new_area)
    session.flush()


def _update_area_simple(session, area_uuid: UUID, area: dict):
    session.execute(
        text("UPDATE areas SET name=:name WHERE id=:aid"),
        {"aid": area_uuid, "name": area["name"]},
    )


def _insert_asset(session, asset: dict, contract_areas: list[dict]):
    """Insert asset using ORM model to handle all column defaults."""
    from app.modules.assets.models import Asset

    # Resolve area_id_fk
    rows = session.execute(
        text("SELECT id FROM areas WHERE area_id = :aid"),
        {"aid": asset["area_id"]},
    ).fetchall()
    area_uuid = rows[0][0] if rows else None

    # Resolve parent_asset_id_fk
    parent_uuid = None
    pid = asset.get("parent_asset_id")
    if pid:
        rows = session.execute(
            text("SELECT id FROM assets WHERE asset_id = :aid"),
            {"aid": pid},
        ).fetchall()
        parent_uuid = rows[0][0] if rows else None

    new_asset = Asset(
        asset_id=asset["asset_id"],
        asset_code=asset.get("asset_code", ""),
        name=asset["name"],
        asset_type=asset.get("asset_type", ""),
        area_id_fk=area_uuid,
        parent_asset_id_fk=parent_uuid,
        criticality=asset.get("criticality", "medium"),
        lifecycle_status=asset.get("status", "active"),
    )
    session.add(new_asset)
    session.flush()


def _insert_signal(session, sig: dict, contract_assets: list[dict]):
    """Insert signal using ORM model to handle all column defaults."""
    from app.modules.signals.models import Signal

    rows = session.execute(
        text("SELECT id FROM assets WHERE asset_id = :aid"),
        {"aid": sig["asset_id"]},
    ).fetchall()
    asset_uuid = rows[0][0] if rows else None

    new_signal = Signal(
        signal_id=sig["signal_id"],
        asset_id_fk=asset_uuid,
        signal_name=sig.get("signal_name", ""),
        display_name=sig.get("display_name", ""),
        signal_type=sig.get("signal_type", "measurement"),
        data_type=sig.get("data_type", "float"),
        engineering_unit=sig.get("engineering_unit", ""),
    )
    session.add(new_signal)
    session.flush()


def _get_asset_ids_for_plant(session, plant_id: str) -> set[str]:
    rows = session.execute(
        text("""
            SELECT a.asset_id FROM assets a
            JOIN areas ar ON a.area_id_fk = ar.id
            WHERE ar.plant_id_fk = (
                SELECT id FROM plants WHERE plant_id = :pid
            )
        """),
        {"pid": plant_id},
    ).fetchall()
    return {r[0] for r in rows}


def _get_signal_ids_for_plant(session, plant_id: str) -> set[str]:
    rows = session.execute(
        text("""
            SELECT s.signal_id FROM signals s
            JOIN assets a ON s.asset_id_fk = a.id
            JOIN areas ar ON a.area_id_fk = ar.id
            WHERE ar.plant_id_fk = (
                SELECT id FROM plants WHERE plant_id = :pid
            )
        """),
        {"pid": plant_id},
    ).fetchall()
    return {r[0] for r in rows}


def _deactivate_asset(session, asset_id: str):
    session.execute(
        text("UPDATE assets SET lifecycle_status='deprecated' WHERE asset_id=:aid"),
        {"aid": asset_id},
    )


def _deactivate_signal(session, signal_id: str):
    session.execute(
        text("UPDATE signals SET source_type='deprecated' WHERE signal_id=:sid"),
        {"sid": signal_id},
    )
