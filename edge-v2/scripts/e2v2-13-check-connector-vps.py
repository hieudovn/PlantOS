#!/usr/bin/env python3
"""Check v2 connector details - runs on VPS."""
import httpx, json

r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f"status={d['status']}")
print(f"bl={d['sync']['backlog']} buf={d['buffer']['row_count']}")
for c in d['connectors']['list']:
    print(f"connector: {c['connector_id']} sig={c['signal_count']} {c['status']} conn={c['connected']}")
