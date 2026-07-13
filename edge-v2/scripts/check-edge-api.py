#!/usr/bin/env python3
"""Check edge-nodes API response type."""
import httpx
r = httpx.get("http://localhost:8000/api/v1/edge-nodes", timeout=10)
print(f"Type: {type(r.json()).__name__}, Status: {r.status_code}")
if isinstance(r.json(), list):
    print(f"List length: {len(r.json())}")
