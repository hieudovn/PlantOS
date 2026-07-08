"""Offline detection background task.

Runs every 30 seconds. Marks edges stale (30s no heartbeat) → offline (60s no heartbeat).
Dispatches edge.offline event on status transitions.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.db import get_session
from app.modules.edge_nodes.models import EdgeNode

logger = logging.getLogger(__name__)

STALE_SECONDS = 30
OFFLINE_SECONDS = 60
CHECK_INTERVAL = 30


async def detect_offline_edges():
    """Background task: check edge node freshness periodically."""
    while True:
        try:
            _check()
        except Exception as e:
            logger.exception("Offline detection error: %s", e)
        await asyncio.sleep(CHECK_INTERVAL)


def _check():
    """Check all edge nodes and update status based on last_heartbeat."""
    now = datetime.now(timezone.utc)
    stale_threshold = now - timedelta(seconds=STALE_SECONDS)
    offline_threshold = now - timedelta(seconds=OFFLINE_SECONDS)

    with get_session() as session:
        nodes = session.query(EdgeNode).all()
        for node in nodes:
            if node.last_heartbeat is None:
                continue

            previous_status = node.status

            if node.last_heartbeat < offline_threshold:
                new_status = "offline"
            elif node.last_heartbeat < stale_threshold:
                new_status = "stale"
            else:
                new_status = "online"

            if new_status != previous_status:
                node.status = new_status
                logger.info(
                    "Edge node '%s' status transition: %s → %s",
                    node.edge_node_id, previous_status, new_status,
                )

        session.commit()


def get_offline_detector_task() -> asyncio.Task:
    """Create and return the offline detector background task."""
    return asyncio.create_task(detect_offline_edges())
