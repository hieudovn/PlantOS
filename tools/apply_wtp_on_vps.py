"""Apply WTP contract to PlantOS database via API."""
import json, sys

import requests

HOST = "http://localhost:8000"
HEADERS = {"X-API-Key": "plantos-edge-key-2026"}

with open("/tmp/wtp_contract.json") as f:
    contract = json.load(f)

payload = {
    "contract": contract,
    "import_policy": {
        "mode": "apply",
        "on_conflict": "fail",
        "allow_delete_missing": False,
        "orphaned_action": "report",
    },
}

print("=" * 60)
print("APPLY /api/v1/contracts/apply")
print("=" * 60)

resp = requests.post(f"{HOST}/api/v1/contracts/apply", json=payload, headers=HEADERS)
data = resp.json()

print(f"HTTP Status: {resp.status_code}")
print(json.dumps(data, indent=2))

with open("/tmp/wtp_apply_response.json", "w") as f:
    json.dump(data, f, indent=2)
print("\n✅ Response saved to /tmp/wtp_apply_response.json")
