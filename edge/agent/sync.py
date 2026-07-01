"""Store-and-Forward — sync buffered data to Center when connected."""

import logging
import httpx

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class StoreAndForward:
    def __init__(self, buffer, ingest_url: str, edge_node_id: str, api_key: str = ""):
        self.buffer = buffer
        self.ingest_url = ingest_url
        self.edge_node_id = edge_node_id
        self.api_key = api_key

    async def flush(self, batch_size: int = 100) -> int:
        """Flush unsynced data to Center. Returns number of synced points.

        Rows rejected by backend (e.g. unknown signal_id) are retried up to
        MAX_RETRIES times, then skipped as dead letters.
        """
        # 1. Skip dead letters (rows that already exceeded max retries)
        skipped = self.buffer.skip_dead_letters(MAX_RETRIES)
        if skipped > 0:
            logger.warning(f"Dead letter: skipped {skipped} rows after {MAX_RETRIES} retries")

        # 2. Get fresh unsynced rows (excluding dead letters)
        unsynced = self.buffer.get_unsynced(batch_size, MAX_RETRIES)
        if not unsynced:
            return 0

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                resp = await client.post(self.ingest_url, json={
                    "source": self.edge_node_id,
                    "measurements": unsynced,
                }, headers=headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    synced = data.get("accepted", 0)
                    rejected = len(unsynced) - synced

                    if synced > 0:
                        self.buffer.mark_synced(synced)

                    if rejected > 0:
                        self.buffer.increment_retry_count(rejected)
                        logger.warning(
                            f"Flushed {synced}/{len(unsynced)} — "
                            f"{rejected} rejected (will retry up to {MAX_RETRIES}x)"
                        )
                    else:
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
