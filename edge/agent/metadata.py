"""Edge metadata sync — download asset/signal manifest from Center."""

import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

CACHE_PATH = Path("metadata_cache.json")


class MetadataManager:
    def __init__(self, center_url: str):
        self.center_url = center_url.rstrip("/")
        self.manifest: dict = {"assets": [], "signals": []}
        self._signal_ids: set[str] = set()

    async def sync(self) -> bool:
        """Download manifest from Center and cache locally."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.center_url}/api/v1/edge/sync/manifest")
                if resp.status_code == 200:
                    self.manifest = resp.json()
                    self._signal_ids = {s["signal_id"] for s in self.manifest.get("signals", [])}
                    # Cache to disk
                    CACHE_PATH.write_text(json.dumps(self.manifest, indent=2))
                    logger.info(f"Synced {len(self.manifest.get('assets',[]))} assets, {len(self.manifest.get('signals',[]))} signals")
                    return True
                else:
                    logger.warning(f"Manifest sync failed: HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Manifest sync error: {e}")
        return False

    def load_cache(self) -> bool:
        """Load manifest from local cache file."""
        if CACHE_PATH.exists():
            try:
                self.manifest = json.loads(CACHE_PATH.read_text())
                self._signal_ids = {s["signal_id"] for s in self.manifest.get("signals", [])}
                logger.info(f"Loaded {len(self._signal_ids)} signals from cache")
                return True
            except Exception:
                pass
        return False

    def is_valid_signal(self, signal_id: str) -> bool:
        """Check if a signal_id is in the synced manifest."""
        return signal_id in self._signal_ids

    def get_asset(self, asset_id: str) -> dict | None:
        for a in self.manifest.get("assets", []):
            if a["asset_id"] == asset_id:
                return a
        return None
