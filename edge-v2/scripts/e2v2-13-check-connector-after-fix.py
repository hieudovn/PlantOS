#!/usr/bin/env python3
"""Check v2 connector status."""
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f"status={d['status']}")
for c in d['connectors']['list']:
    print(f"  {c['connector_id']}: sig={c['signal_count']} {c['status']} conn={c['connected']}")
