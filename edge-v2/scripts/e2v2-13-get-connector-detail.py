#!/usr/bin/env python3
"""Get full connector status from v2 API."""
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print("Full connector info:")
print(json.dumps(d['connectors'], indent=2))
print("\nSignal count from list_status_sync:")
# Check what list_status_sync returns
for c_id, inst in d.items():
    pass  # not accessible this way
