"""Verify SQLAlchemy models import correctly and can create tables."""

from sqlalchemy import create_engine, inspect

from app.db.base import Base


def test_all_models_import():
    """Verify all models can be imported without errors."""
    import app.modules  # noqa: F401
    tables = list(Base.metadata.tables.keys())
    expected = {"plants", "areas", "assets", "signals", "edge_nodes"}
    assert expected.issubset(tables), f"Missing tables: {expected - set(tables)}"


def test_create_all_tables():
    """Verify all tables can be created with SQLite in-memory."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "plants" in table_names
    assert "areas" in table_names
    assert "assets" in table_names
    assert "signals" in table_names
    assert "edge_nodes" in table_names

    engine.dispose()


def test_asset_relationships():
    """Verify Asset's self-referential and FK relationships exist."""
    import app.modules  # noqa: F401
    from app.modules.assets.models import Asset

    # Parent/children self-reference
    assert hasattr(Asset, "parent")
    assert hasattr(Asset, "children")
    # FK to Area
    assert hasattr(Asset, "area")
    # Signals relationship
    assert hasattr(Asset, "signals")


def test_signal_relationships():
    """Verify Signal FK to Asset exists."""
    import app.modules  # noqa: F401
    from app.modules.signals.models import Signal

    assert hasattr(Signal, "asset")
