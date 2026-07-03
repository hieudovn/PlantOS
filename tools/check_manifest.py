"""Check Edge Agent manifest."""
import json, os, sys

import requests

EDGE_API_KEY = os.environ.get("EDGE_API_KEY", "")
if not EDGE_API_KEY:
    print("ERROR: EDGE_API_KEY environment variable not set.", file=sys.stderr)
    sys.exit(1)

r = requests.get("http://localhost:8000/api/v1/edge/sync/manifest", headers={"X-API-Key": EDGE_API_KEY})
d = r.json()
assets = d.get("assets", [])
signals = d.get("signals", [])
print(f"Manifest: {len(assets)} assets, {len(signals)} signals")
for a in assets[:5]:
    print(f"  Asset: {a.get('asset_id')} ({a.get('name','')})")
