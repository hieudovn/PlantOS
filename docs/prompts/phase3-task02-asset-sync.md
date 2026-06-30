# Phase 3 — Task 3-02: Bi-directional Asset Sync (Center→Edge)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Center là source of truth cho Asset/Signal registry. Edge tải metadata từ Center khi khởi động, cache local, dùng để validate measurement trước khi publish.

## Architecture

```
Center                                    Edge
──────────────────────                    ──────────────────────
GET /api/v1/edge/sync/manifest            metadata.py
→ Trả về toàn bộ:                        ├── download_manifest()
  {                                       ├── cache local JSON
    "assets": [...],                      ├── validate(signal_id)
    "signals": [...],                     └── auto-refresh mỗi 5 phút
    "generated_at": "..."
  }                                       main.py
                                          └── gọi sync khi startup
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/edge_nodes/service.py` — build manifest
- [ ] MODIFY `backend/app/modules/edge_nodes/router.py` — add sync endpoint
- [ ] CREATE `edge/agent/metadata.py` — download, cache, validate
- [ ] MODIFY `edge/agent/main.py` — call sync on startup + periodic
- [ ] MODIFY `edge/agent/config.yaml` — add center_url

## Detailed Instructions

### 1. `backend/app/modules/edge_nodes/service.py`

```python
"""Edge node sync service — builds asset/signal manifest."""

from app.db import get_session
from app.modules.assets.repository import AssetRepository
from app.modules.signals.repository import SignalRepository


def build_sync_manifest() -> dict:
    """Build full asset + signal manifest for edge sync."""
    with get_session() as session:
        asset_repo = AssetRepository(session)
        signal_repo = SignalRepository(session)

        assets = asset_repo.list_all()
        signals = signal_repo.list_all()

    return {
        "assets": [
            {
                "asset_id": a.asset_id,
                "name": a.name,
                "asset_type": a.asset_type,
                "area_id": a.area.area_id if a.area else None,
                "parent_asset_id": a.parent.asset_id if a.parent else None,
                "lifecycle_status": a.lifecycle_status,
            }
            for a in assets
        ],
        "signals": [
            {
                "signal_id": s.signal_id,
                "asset_id": s.asset.asset_id,
                "signal_name": s.signal_name,
                "display_name": s.display_name,
                "signal_type": s.signal_type,
                "data_type": s.data_type,
                "engineering_unit": s.engineering_unit,
                "uns_path": s.uns_path,
            }
            for s in signals
        ],
    }
```

### 2. `backend/app/modules/edge_nodes/router.py` — Add endpoint

```python
from app.modules.edge_nodes.service import build_sync_manifest
from datetime import datetime, timezone

@router.get("/edge/sync/manifest")
def get_sync_manifest():
    """Return full asset + signal manifest for edge nodes to sync."""
    manifest = build_sync_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["version"] = "1.0"
    return manifest
```

### 3. `edge/agent/metadata.py`

```python
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
```

### 4. `edge/agent/main.py` — Integrate

```python
from metadata import MetadataManager

class EdgeAgent:
    def __init__(self, config_path: str):
        # ... existing init ...

        # Metadata sync
        self.metadata = MetadataManager(self.cfg.get("center_url", "http://localhost:8000"))

    async def run(self):
        # Sync metadata on startup (try Center first, fallback to cache)
        ok = await self.metadata.sync()
        if not ok:
            logger.warning("Center unreachable, loading cached metadata")
            self.metadata.load_cache()

        # Start periodic tasks
        asyncio.create_task(self.health.run(lambda: self.sync.get_backlog()))
        asyncio.create_task(self._periodic_metadata_sync())

        # ... existing main loop ...

    async def _periodic_metadata_sync(self):
        """Refresh metadata from Center every 5 minutes."""
        while True:
            await asyncio.sleep(300)
            await self.metadata.sync()
```

### 5. `edge/agent/config.yaml` — Add

```yaml
center_url: http://localhost:8000
```

## Constraints

- [x] Center = source of truth — Edge chỉ download, không push metadata lên
- [x] Edge cache local JSON — hoạt động offline khi Center unavailable
- [x] Validate signal_id trước khi publish (chỉ publish signals đã biết)
- [x] Periodic refresh mỗi 5 phút

## Validation

```bash
# 1. Start backend + seed data
# 2. Start edge agent → verify "Synced X assets, Y signals"
# 3. Check manifest endpoint
curl http://localhost:8000/api/v1/edge/sync/manifest | python -m json.tool | head -20
# 4. Check cache file
cat edge/agent/metadata_cache.json | python -m json.tool | head -10
```
