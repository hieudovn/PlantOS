#!/usr/bin/env python3
"""Check config file."""
import yaml
c = yaml.safe_load(open("/home/plantos/edge-v2/agent/config/config.edge-v2.yaml"))
auth = c.get("auth", {})
print("Keys in auth:", list(auth.keys()))
print("admin_hash present:", "admin_hash" in auth)
print("users type:", type(auth.get("users")).__name__)
print("users count:", len(auth.get("users", {})))
for k, v in auth.get("users", {}).items():
    print(f"  {k}: role={v.get('role')} hash={v.get('password_hash','')[:20]}...")
