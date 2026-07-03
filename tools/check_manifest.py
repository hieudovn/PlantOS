"""Check Edge Agent manifest."""
import json
import sys

import requests

r = requests.get("http://localhost:8000/api/v1/edge/sync/manifest", headers={"X-API-Key": "plantos-edge-key-2026"})
d = r.json()
assets = d.get("assets", [])
signals = d.get("signals", [])
print(f"Manifest: {len(assets)} assets, {len(signals)} signals")
for a in assets[:5]:
    print(f"  Asset: {a.get('asset_id')} ({a.get('name','')})")
