"""Migration: add status to signals, timezone to plants.

Run on startup or as standalone script:
    python -m app.db.migrations.add_status_timezone
"""

import logging

from sqlalchemy import text

from app.db.base import get_session

logger = logging.getLogger(__name__)


def upgrade():
    """Add missing columns. Idempotent — safe to run multiple times."""
    with get_session() as session:
        # signals.status
        try:
            session.execute(text(
                "ALTER TABLE signals ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active'"
            ))
            session.execute(text(
                "UPDATE signals SET status = 'active' WHERE status IS NULL"
            ))
            logger.info("signals.status: OK")
        except Exception as e:
            logger.warning(f"signals.status: {e}")

        # plants.timezone
        try:
            session.execute(text(
                "ALTER TABLE plants ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'UTC'"
            ))
            session.execute(text(
                "UPDATE plants SET timezone = 'UTC' WHERE timezone IS NULL"
            ))
            logger.info("plants.timezone: OK")
        except Exception as e:
            logger.warning(f"plants.timezone: {e}")

        session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
    print("Migration complete.")
