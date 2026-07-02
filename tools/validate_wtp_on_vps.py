"""Validate and preview WTP contract on server."""
import json, sys

import requests

HOST = "http://localhost:8000"
HEADERS = {"X-API-Key": "plantos-edge-key-2026"}

with open("/tmp/wtp_contract.json") as f:
    contract = json.load(f)

# ---- Validate ----
print("=" * 60)
print("VALIDATE /api/v1/contracts/validate")
print("=" * 60)

resp = requests.post(f"{HOST}/api/v1/contracts/validate", json=contract, headers=HEADERS)
data = resp.json()

print(f"valid: {data.get('valid')}")
print(f"errors: {len(data.get('errors', []))}")
print(f"warnings: {len(data.get('warnings', []))}")
s = data.get("summary", {})
print(f"summary: areas={s.get('areas')}, assets={s.get('assets')}, signals={s.get('signals')}")

# Print first few warnings by type
unit_warnings = 0
binding_warnings = 0
other_warnings = 0
for w in data.get("warnings", []):
    msg = w.get("message", "")
    if "unit" in msg.lower():
        unit_warnings += 1
    elif "binding" in msg.lower() or "unbound" in msg.lower():
        binding_warnings += 1
    else:
        other_warnings += 1

print(f"\n  Warnings breakdown:")
print(f"    Unrecognized units: {unit_warnings}")
print(f"    No OPC UA binding:  {binding_warnings}")
print(f"    Other warnings:     {other_warnings}")

# Show sample of each type
if data.get("errors"):
    print("\n  First 3 errors:")
    for e in data["errors"][:3]:
        print(f"    ❌ {e['path']}: {e['message']}")

if unit_warnings > 0:
    print("\n  Sample unit warnings:")
    count = 0
    for w in data.get("warnings", []):
        if "unit" in w["message"].lower() and count < 3:
            print(f"    ⚠️  {w['message']}")
            count += 1

# ---- Preview ----
print("\n" + "=" * 60)
print("PREVIEW /api/v1/contracts/preview")
print("=" * 60)

resp2 = requests.post(f"{HOST}/api/v1/contracts/preview", json=contract, headers=HEADERS)
preview = resp2.json()

print(f"valid: {preview.get('valid')}")
changes = preview.get("changes", {})
for entity_type in ["plants", "areas", "assets", "signals"]:
    c = changes.get(entity_type, {})
    print(f"  {entity_type}: creates={len(c.get('create',[]))} conflicts={len(c.get('conflict',[]))} orphans={len(c.get('orphan',[]))}")

summary = preview.get("summary", {})
print(f"\n  Totals: creates={summary.get('total_creates')} conflicts={summary.get('total_conflicts')} orphans={summary.get('total_orphans')}")

if preview.get("changes"):
    print("\n✅ Preview completed successfully")
else:
    print("\n⚠️  Preview returned no changes data")

# ---- Save full response for report ----
with open("/tmp/wtp_validate_response.json", "w") as f:
    json.dump(data, f, indent=2)
with open("/tmp/wtp_preview_response.json", "w") as f:
    json.dump(preview, f, indent=2)
print("\n✅ Full responses saved to /tmp/wtp_validate_response.json and /tmp/wtp_preview_response.json")
