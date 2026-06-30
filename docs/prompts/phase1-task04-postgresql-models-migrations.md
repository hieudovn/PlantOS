# Phase 1 — Task 4: PostgreSQL Models & Alembic Migrations

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Coder:** DeepSeek V4 Flash | **Reviewer:** DeepSeek V4 Pro
> **Status:** READY FOR IMPLEMENTATION

## Context

Tạo SQLAlchemy models cho PlantOS metadata (Plant, Area, Asset, Signal, EdgeNode) và thiết lập Alembic migrations. Đây là data layer foundation — **chưa implement API, service, router, hay seed data.** Những thứ đó sẽ làm ở Task 6-10.

Tất cả models phải tuân theo UNS/CDM principles:
- Signal ≠ Raw Tag (tách `signal_id` semantic và `source_ref` raw)
- Asset/Signal binding qua FK
- Hierarchy Plant → Area → Asset → Signal khớp UNS path structure

## Plan Reference

- `docs/20-data-model.md` §3 — Core entities (Plant, Area, Asset, Signal, EdgeNode)
- `docs/15-storage-and-historian-design.md` §2-3 — PostgreSQL responsibility split
- `docs/14-api-contract-mvp.md` §4-5 — Asset/Signal field reference
- `docs/13-backend-service-design.md` §5-6 — Architecture rules & folder pattern

## Implementation Checklist

- [ ] MODIFY `backend/app/core/config.py` — thêm DATABASE_URL property
- [ ] CREATE `backend/app/db/base.py` — SQLAlchemy Base, engine, SessionLocal
- [ ] MODIFY `backend/app/db/__init__.py` — re-export symbols
- [ ] CREATE `backend/app/modules/assets/models.py` — Plant, Area, Asset
- [ ] CREATE `backend/app/modules/signals/models.py` — Signal
- [ ] CREATE `backend/app/modules/edge_nodes/models.py` — EdgeNode
- [ ] MODIFY `backend/app/modules/__init__.py` — import all models (cho Alembic)
- [ ] MODIFY `backend/app/modules/assets/__init__.py` — import models
- [ ] MODIFY `backend/app/modules/signals/__init__.py` — import models
- [ ] MODIFY `backend/app/modules/edge_nodes/__init__.py` — import models
- [ ] CREATE `backend/alembic.ini` — Alembic config
- [ ] CREATE `backend/migrations/env.py` — Alembic environment
- [ ] CREATE `backend/migrations/script.py.mako` — Migration template
- [ ] CREATE `backend/migrations/versions/001_initial_metadata_tables.py` — Initial migration
- [ ] MODIFY `backend/app/main.py` — lifespan: init/dispose engine
- [ ] CREATE `backend/tests/test_models.py` — verify model import + table creation (SQLite in-memory)

## Exact Files to Create/Modify

| # | File Path | Action | Content Summary |
|---|-----------|--------|-----------------|
| 1 | `backend/app/core/config.py` | MODIFY | Add `DATABASE_URL` computed property |
| 2 | `backend/app/db/base.py` | CREATE | SQLAlchemy Base, `get_engine()`, `get_session()` |
| 3 | `backend/app/db/__init__.py` | MODIFY | Re-export Base, engine, SessionLocal |
| 4 | `backend/app/modules/assets/models.py` | CREATE | `Plant`, `Area`, `Asset` SQLAlchemy models |
| 5 | `backend/app/modules/signals/models.py` | CREATE | `Signal` SQLAlchemy model |
| 6 | `backend/app/modules/edge_nodes/models.py` | CREATE | `EdgeNode` SQLAlchemy model |
| 7 | `backend/app/modules/__init__.py` | MODIFY | Import all models for Alembic discovery |
| 8 | `backend/app/modules/assets/__init__.py` | MODIFY | `from .models import Plant, Area, Asset` |
| 9 | `backend/app/modules/signals/__init__.py` | MODIFY | `from .models import Signal` |
| 10 | `backend/app/modules/edge_nodes/__init__.py` | MODIFY | `from .models import EdgeNode` |
| 11 | `backend/alembic.ini` | CREATE | Alembic config pointing to `migrations/` |
| 12 | `backend/migrations/env.py` | CREATE | Alembic env with target_metadata = Base.metadata |
| 13 | `backend/migrations/script.py.mako` | CREATE | Standard Alembic migration template |
| 14 | `backend/migrations/versions/001_initial_metadata_tables.py` | CREATE | Generated migration (downgrade possible) |
| 15 | `backend/app/main.py` | MODIFY | Add engine init/dispose in lifespan |
| 16 | `backend/tests/test_models.py` | CREATE | Test model import + create_all with SQLite |

## Detailed Instructions

### 1. `backend/app/core/config.py` — Add DATABASE_URL

Add a `DATABASE_URL` property to Settings:

```python
@property
def DATABASE_URL(self) -> str:
    """Construct PostgreSQL connection URL from settings."""
    return (
        f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    )

@property
def DATABASE_URL_SYNC(self) -> str:
    """Synchronous URL for Alembic (migrations run sync)."""
    return self.DATABASE_URL
```

> Lưu ý: property không cần khai báo type annotation riêng. Đặt trong class Settings, dưới các field hiện có.

### 2. `backend/app/db/base.py` — SQLAlchemy Foundation

```python
"""SQLAlchemy base, engine, and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all PlantOS SQLAlchemy models."""
    pass


# Engine is created lazily to avoid import-time DB connection
_engine = None
_SessionLocal = None


def get_engine():
    """Return (or create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session():
    """Return a new SQLAlchemy session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def dispose_engine():
    """Dispose the engine (for graceful shutdown)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
```

### 3. `backend/app/db/__init__.py` — Re-export

```python
from app.db.base import Base, get_engine, get_session, dispose_engine

__all__ = ["Base", "get_engine", "get_session", "dispose_engine"]
```

### 4. `backend/app/modules/assets/models.py` — Plant, Area, Asset

```python
"""Asset Registry — SQLAlchemy models for Plant, Area, Asset."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    plant_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    areas: Mapped[list["Area"]] = relationship("Area", back_populates="plant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Plant {self.plant_id}>"


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    area_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    plant_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    plant: Mapped["Plant"] = relationship("Plant", back_populates="areas")
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="area", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Area {self.area_id}>"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    asset_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    asset_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    area_id_fk: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    parent_asset_id_fk: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    criticality: Mapped[str] = mapped_column(String(32), default="medium")
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="active")
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    area: Mapped["Area | None"] = relationship("Area", back_populates="assets")
    parent: Mapped["Asset | None"] = relationship("Asset", remote_side="Asset.id", back_populates="children")
    children: Mapped[list["Asset"]] = relationship("Asset", back_populates="parent", cascade="all, delete-orphan")
    signals: Mapped[list["Signal"]] = relationship("Signal", back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Asset {self.asset_id}>"
```

### 5. `backend/app/modules/signals/models.py` — Signal

```python
"""Signal Registry — SQLAlchemy model for Signal."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    signal_id: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    asset_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    signal_name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(32), default="measurement")
    data_type: Mapped[str] = mapped_column(String(32), default="float")
    engineering_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    uns_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), default="simulator")
    source_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    quality_policy: Mapped[str] = mapped_column(String(32), default="GOOD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="signals")

    def __repr__(self):
        return f"<Signal {self.signal_id}>"
```

> Lưu ý: `Asset` type được import từ `app.modules.assets.models`. Sử dụng TYPE_CHECKING nếu cần tránh circular import:
> ```python
> from __future__ import annotations
> ```

### 6. `backend/app/modules/edge_nodes/models.py` — EdgeNode

```python
"""Edge Node Registry — SQLAlchemy model for EdgeNode."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class EdgeNode(Base):
    __tablename__ = "edge_nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    edge_node_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), default="simulator")
    status: Mapped[str] = mapped_column(String(32), default="offline")
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f"<EdgeNode {self.edge_node_id}>"
```

### 7-10. Module `__init__.py` Updates

`backend/app/modules/__init__.py`:

```python
# Import all models so Alembic can discover them
from app.modules.assets.models import Plant, Area, Asset  # noqa: F401
from app.modules.signals.models import Signal  # noqa: F401
from app.modules.edge_nodes.models import EdgeNode  # noqa: F401
```

`backend/app/modules/assets/__init__.py`:

```python
from app.modules.assets.models import Plant, Area, Asset  # noqa: F401
```

`backend/app/modules/signals/__init__.py`:

```python
from app.modules.signals.models import Signal  # noqa: F401
```

`backend/app/modules/edge_nodes/__init__.py`:

```python
from app.modules.edge_nodes.models import EdgeNode  # noqa: F401
```

### 11. `backend/alembic.ini`

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg2://plantos:plantos@localhost:5432/plantos

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 12. `backend/migrations/env.py`

```python
"""Alembic environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.base import Base
from app.core.config import settings

# Import all models so Alembic sees them
import app.modules  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 13. `backend/migrations/script.py.mako`

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

### 14. `backend/migrations/versions/001_initial_metadata_tables.py`

Generate migration tự động bằng lệnh:
```bash
cd backend
alembic revision --autogenerate -m "initial_metadata_tables"
```

**Sau khi generate**, đọc file và kiểm tra:
- Có đủ 5 bảng: `plants`, `areas`, `assets`, `signals`, `edge_nodes`
- Mỗi bảng có `upgrade()` và `downgrade()`
- UUID PK, unique constraints, foreign keys đúng

> Nếu không chạy được `alembic revision --autogenerate` (cần PostgreSQL running), tạo migration thủ công với đầy đủ `op.create_table()` cho 5 bảng.

### 15. `backend/app/main.py` — Lifespan Update

Thêm engine init/dispose vào lifespan:

```python
"""PlantOS Center Backend — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db import get_engine, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup — initialize DB engine
    get_engine()
    yield
    # Shutdown — dispose DB engine
    dispose_engine()


app = FastAPI(
    title="PlantOS API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
```

### 16. `backend/tests/test_models.py` — Model Tests

```python
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
```

## Constraints

- [x] Không bypass UNS/CDM — Signal có `uns_path`, tách `signal_id` và `source_ref`
- [x] Không UI-to-DB coupling — models là internal, không expose ra API trực tiếp
- [x] Không hardcode raw tag/signal names — mọi ID là parameter
- [x] Edge/Center tách biệt — EdgeNode là metadata registry trong Center
- [x] Không business logic ngoài scope — chỉ models + migrations, không service/router
- [x] Chỉ tạo file trong bảng trên — không tạo thư mục mới
- [x] Không implement API routes — Task 6-7 mới làm
- [x] Không tạo Pydantic schemas — Task 6-7 mới làm
- [x] Không seed data — Task 10 mới làm

## Validation

1. **Import check:**
   ```bash
   cd backend
   python -c "import app.modules; print('Models imported OK')"
   ```

2. **Model tests (SQLite in-memory, không cần PostgreSQL):**
   ```bash
   cd backend
   python -m pytest tests/test_models.py -v
   ```
   Expected: 4 tests passed

3. **Health endpoint still works:**
   ```bash
   cd backend
   python -m pytest tests/test_health.py -v
   ```
   Expected: 1 test passed (health endpoint không bị break)

4. **Alembic migration can be generated:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "initial_metadata_tables"
   ```
   Expected: Tạo file trong `migrations/versions/` với đủ 5 bảng

5. **Verify migration file:**
   - Đọc file migration vừa tạo
   - Xác nhận `upgrade()` có `op.create_table()` cho plants, areas, assets, signals, edge_nodes
   - Xác nhận `downgrade()` có `op.drop_table()` cho tất cả

## Expected Output Format

```
1. Files created/modified:
   - backend/app/core/config.py — MODIFY — added DATABASE_URL property
   - backend/app/db/base.py — CREATE — SQLAlchemy Base + engine
   - backend/app/db/__init__.py — MODIFY — re-export
   - backend/app/modules/assets/models.py — CREATE — Plant, Area, Asset
   - backend/app/modules/signals/models.py — CREATE — Signal
   - backend/app/modules/edge_nodes/models.py — CREATE — EdgeNode
   - backend/app/modules/__init__.py — MODIFY — import all models
   - backend/app/modules/assets/__init__.py — MODIFY — import models
   - backend/app/modules/signals/__init__.py — MODIFY — import models
   - backend/app/modules/edge_nodes/__init__.py — MODIFY — import models
   - backend/alembic.ini — CREATE
   - backend/migrations/env.py — CREATE
   - backend/migrations/script.py.mako — CREATE
   - backend/migrations/versions/001_initial_metadata_tables.py — CREATE
   - backend/app/main.py — MODIFY — engine init/dispose in lifespan
   - backend/tests/test_models.py — CREATE

2. Test results:
   - test_health.py: PASSED
   - test_models.py::test_all_models_import: PASSED
   - test_models.py::test_create_all_tables: PASSED
   - test_models.py::test_asset_relationships: PASSED
   - test_models.py::test_signal_relationships: PASSED

3. Issues / Deviations:
   - [none hoặc liệt kê]

4. Confirmation:
   - [x] No constitution rule violated
   - [x] No UNS/CDM bypass
   - [x] No UI-to-DB coupling
   - [x] Edge/Center separation maintained
   - [x] All models follow data model spec
```
