"""Edge node sync service — builds asset/signal manifest."""

from app.db import get_session
from app.modules.assets.repository import AssetRepository
from app.modules.signals.repository import SignalRepository


def build_sync_manifest() -> dict:
    """Build full asset + signal manifest for edge sync."""
    with get_session() as session:
        asset_repo = AssetRepository(session)
        signal_repo = SignalRepository(session)

        assets = asset_repo.list_all()
        signals = signal_repo.list_all()

        return {
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "name": a.name,
                    "asset_type": a.asset_type,
                    "area_id": a.area.area_id if a.area else None,
                    "parent_asset_id": a.parent.asset_id if a.parent else None,
                    "lifecycle_status": a.lifecycle_status,
                }
                for a in assets
            ],
            "signals": [
                {
                    "signal_id": s.signal_id,
                    "asset_id": s.asset.asset_id,
                    "signal_name": s.signal_name,
                    "display_name": s.display_name,
                    "signal_type": s.signal_type,
                    "data_type": s.data_type,
                    "engineering_unit": s.engineering_unit,
                    "uns_path": s.uns_path,
                }
                for s in signals
            ],
        }

