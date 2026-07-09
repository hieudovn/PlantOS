#!/usr/bin/env python3
"""Quick check v2 status fields and connector structure."""
import httpx, json

r = httpx.get('http://localhost:8011/api/status', timeout=10)
s = json.loads(r.text)

print("Status keys:", list(s.keys()))
print(f"Status: {s.get('status')}")
print(f"Edge node: {s.get('edge_node_id')}")

# Check connectors in various possible locations
for key in s.keys():
    val = s[key]
    if isinstance(val, dict):
        print(f"\n'{key}' is dict with keys: {list(val.keys())[:5]}")
        # Check if this looks like connectors
        for k2, v2 in val.items():
            if isinstance(v2, dict) and 'status' in v2:
                print(f"  -> Found connector-like entry: {k2}")
    elif isinstance(val, list):
        print(f"\n'{key}' is list with {len(val)} items")
        if val:
            print(f"  First item type: {type(val[0]).__name__}")

# Print connectors specifically  
conns = s.get('connectors', {})
print(f"\nconnectors type: {type(conns).__name__}")
if isinstance(conns, dict):
    for k, v in conns.items():
        print(f"  {k}: {type(v).__name__} = {v}")
elif isinstance(conns, list):
    for i, c in enumerate(conns):
        print(f"  [{i}]: {type(c).__name__} = {c}")
