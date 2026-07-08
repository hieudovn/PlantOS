import pytest
from app.modules.assets.schemas import AssetResponse, AssetCreate
from app.modules.signals.schemas import SignalResponse, SignalCreate


def test_asset_create_schema_has_asset_role():
    """AssetCreate must include asset_role field."""
    schema = AssetCreate.model_json_schema()
    assert "asset_role" in schema["properties"]
    assert schema["properties"]["asset_role"]["default"] == "equipment"


def test_asset_response_schema_has_asset_role():
    """AssetResponse must include asset_role field."""
    schema = AssetResponse.model_json_schema()
    assert "asset_role" in schema["properties"]


def test_signal_create_schema_has_signal_category():
    """SignalCreate must include signal_category field."""
    schema = SignalCreate.model_json_schema()
    assert "signal_category" in schema["properties"]


def test_signal_response_schema_has_signal_category():
    """SignalResponse must include signal_category and external_refs."""
    schema = SignalResponse.model_json_schema()
    assert "signal_category" in schema["properties"]
    assert "external_refs" in schema["properties"]


@pytest.mark.skip(reason="Requires PostgreSQL connection (set POSTGRES_PASSWORD)")
def test_frontend_operations_asset_role_not_broken():
    """Quick check that resolve_asset_info returns asset_role."""
    from app.modules.events.resolver import resolve_asset_info
    info = resolve_asset_info("FILTER-101")
    assert info is not None
    assert "asset_role" in info
    assert info["asset_role"] in (
        "equipment", "functional_location", "subsystem", "component", "logical_group",
    )
