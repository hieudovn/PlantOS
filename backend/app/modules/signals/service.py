"""Signal Registry — Service layer."""

from app.db import get_session
from app.modules.assets.repository import AssetRepository
from app.modules.signals.models import Signal
from app.modules.signals.repository import SignalRepository
from app.modules.signals.schemas import (
    SignalCreate,
    SignalUpdate,
    SignalResponse,
    SourceInfo,
)


def _signal_to_response(signal: Signal) -> SignalResponse:
    source = None
    if signal.source_type or signal.source_ref:
        source = SourceInfo(
            source_type=signal.source_type,
            source_ref=signal.source_ref,
        )

    return SignalResponse(
        signal_id=signal.signal_id,
        asset_id=signal.asset.asset_id,
        signal_name=signal.signal_name,
        display_name=signal.display_name,
        signal_type=signal.signal_type,
        data_type=signal.data_type,
        engineering_unit=signal.engineering_unit,
        min_value=signal.min_value,
        max_value=signal.max_value,
        uns_path=signal.uns_path,
        source=source,
        quality_policy=signal.quality_policy,
        created_at=signal.created_at,
        updated_at=signal.updated_at,
    )


class SignalService:
    def create_signal(self, data: SignalCreate) -> SignalResponse:
        with get_session() as session:
            signal_repo = SignalRepository(session)
            if signal_repo.get_by_id(data.signal_id):
                raise ValueError(f"Signal '{data.signal_id}' already exists")

            # Resolve asset
            asset_repo = AssetRepository(session)
            asset = asset_repo.get_by_id(data.asset_id)
            if not asset:
                raise ValueError(f"Asset '{data.asset_id}' not found")

            source_type = data.source.source_type if data.source else "simulator"
            source_ref = data.source.source_ref if data.source else None

            signal = Signal(
                signal_id=data.signal_id,
                asset_id_fk=asset.id,
                signal_name=data.signal_name,
                display_name=data.display_name,
                signal_type=data.signal_type,
                data_type=data.data_type,
                engineering_unit=data.engineering_unit,
                min_value=data.min_value,
                max_value=data.max_value,
                uns_path=data.uns_path,
                source_type=source_type,
                source_ref=source_ref,
                quality_policy=data.quality_policy,
            )
            signal = signal_repo.create(signal)
            return _signal_to_response(signal)

    def get_signal(self, signal_id: str) -> SignalResponse:
        with get_session() as session:
            repo = SignalRepository(session)
            signal = repo.get_by_id(signal_id)
            if not signal:
                raise ValueError(f"Signal '{signal_id}' not found")
            return _signal_to_response(signal)

    def list_signals(
        self,
        asset_id: str | None = None,
        signal_type: str | None = None,
        data_type: str | None = None,
        plant_id: str | None = None,
    ) -> list[SignalResponse]:
        with get_session() as session:
            repo = SignalRepository(session)
            signals = repo.list_all(asset_id, signal_type, data_type, plant_id)
            return [_signal_to_response(s) for s in signals]

    def update_signal(self, signal_id: str, data: SignalUpdate) -> SignalResponse:
        with get_session() as session:
            repo = SignalRepository(session)
            signal = repo.get_by_id(signal_id)
            if not signal:
                raise ValueError(f"Signal '{signal_id}' not found")

            update_data = data.model_dump(exclude_unset=True)

            # Flatten source object
            if "source" in update_data:
                src = update_data.pop("source")
                if src:
                    update_data["source_type"] = src.source_type
                    update_data["source_ref"] = src.source_ref
                else:
                    update_data["source_type"] = "simulator"
                    update_data["source_ref"] = None

            signal = repo.update(signal, update_data)
            return _signal_to_response(signal)
