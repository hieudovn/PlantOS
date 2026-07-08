"""Resolve signal and asset metadata for event building."""

import logging
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db import get_session
from app.modules.assets.models import Asset, Area
from app.modules.signals.models import Signal

logger = logging.getLogger(__name__)


def resolve_signal_info(signal_id: str) -> dict | None:
    """Get signal metadata needed for event envelopes."""
    try:
        with get_session() as session:
            signal = session.scalar(
                select(Signal)
                .options(joinedload(Signal.asset))
                .where(Signal.signal_id == signal_id)
            )
            if not signal:
                logger.warning("Signal not found for event: %s", signal_id)
                return None
            asset = signal.asset
            return {
                "signal_id": signal.signal_id,
                "signal_name": signal.signal_name,
                "signal_category": signal.signal_category,
                "data_type": signal.data_type,
                "engineering_unit": signal.engineering_unit or "",
                "asset_id": asset.asset_id if asset else "",
            }
    except Exception:
        logger.exception("Failed to resolve signal info for %s", signal_id)
        return None


def resolve_asset_info(asset_id: str) -> dict | None:
    """Get asset metadata needed for event envelopes."""
    try:
        with get_session() as session:
            asset = session.scalar(
                select(Asset)
                .options(joinedload(Asset.area).joinedload(Area.plant))
                .where(Asset.asset_id == asset_id)
            )
            if not asset:
                logger.warning("Asset not found for event: %s", asset_id)
                return None
            area = asset.area
            plant = area.plant if area else None
            return {
                "asset_id": asset.asset_id,
                "asset_code": asset.asset_code or "",
                "asset_type": asset.asset_type,
                "asset_role": asset.asset_role,
                "plant_id": plant.plant_id if plant else "",
                "area_id": area.area_id if area else "",
            }
    except Exception:
        logger.exception("Failed to resolve asset info for %s", asset_id)
        return None
