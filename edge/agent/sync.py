"""Store-and-Forward — sync buffered data to Center when connected."""

import logging
import httpx

logger = logging.getLogger(__name__)


class StoreAndForward:
    def __init__(self, buffer, ingest_url: str, edge_node_id: str):
        self.buffer = buffer
        self.ingest_url = ingest_url
        self.edge_node_id = edge_node_id

    async def flush(self, batch_size: int = 100) -> int:
        """Flush unsynced data to Center. Returns number of synced points."""
        unsynced = self.buffer.get_unsynced(batch_size)
        if not unsynced:
            return 0

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.ingest_url, json={
                    "source": self.edge_node_id,
                    "measurements": unsynced,
                })
                if resp.status_code in (200, 201):
                    data = resp.json()
                    synced = data.get("accepted", 0)
                    if synced > 0:
                        self.buffer.mark_synced(synced)
                    logger.info(f"Flushed {synced}/{len(unsynced)} measurements")
                    return synced
                else:
                    logger.warning(f"Flush failed: HTTP {resp.status_code}")
                    return 0
        except Exception as e:
            logger.warning(f"Flush error: {e}")
            return 0

    def get_backlog(self) -> int:
        return self.buffer.count_unsynced()
