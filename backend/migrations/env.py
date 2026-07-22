"""Alembic environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.base import Base

# Import all models so Alembic sees them
import app.modules  # noqa: F401

config = context.config

# Build DB URL from env vars (bypass settings singleton to ensure CI env is used)
import os as _os
_db_host = _os.environ.get("POSTGRES_HOST", "localhost")
_db_port = _os.environ.get("POSTGRES_PORT", "5432")
_db_user = _os.environ.get("POSTGRES_USER", "plantos")
_db_pass = _os.environ.get("POSTGRES_PASSWORD", "plantos")
_db_name = _os.environ.get("POSTGRES_DB", "plantos")
_db_url = f"postgresql+psycopg2://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"
config.set_main_option("sqlalchemy.url", _db_url)

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
