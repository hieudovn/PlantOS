import urllib.request, json

API = "http://localhost:8000"
KEY = "plantos-edge-8db46bd13a6a1e50b75f854b"

def api(path):
    req = urllib.request.Request(f"{API}{path}", headers={"X-API-Key": KEY})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

plants = api("/api/v1/plants")
areas = api("/api/v1/areas")
assets = api("/api/v1/assets")
signals = api("/api/v1/signals")

# Pick WTP-DEMO-01
wtp_areas = [a for a in areas if a.get("plant_id") == "WTP-DEMO-01"]
wtp_assets = [a for a in assets if a.get("plant_id") == "WTP-DEMO-01"][:3]
wtp_ids = {a["asset_id"] for a in wtp_assets}
wtp_signals = [s for s in signals if s.get("asset_id") in wtp_ids][:5]

# Add UNS topic derivation
def uns_topic(s):
    return f"plantos/wtp-demo-01/{s['asset_id'].lower()}/measurement/{s['signal_name']}"

for s in wtp_signals:
    s["uns_topic"] = uns_topic(s)

export = {
    "export_info": {
        "source": "PlantOS Center API",
        "generated_at": "2026-07-06T00:00:00Z",
        "plantos_version": "0.1.0",
        "schema_version": "2.0"
    },
    "sample_plant": plants[0] if plants else {},
    "sample_areas": wtp_areas[:1],
    "sample_assets": wtp_assets,
    "sample_signals": wtp_signals
}

with open("/tmp/export_sample.json", "w") as f:
    json.dump(export, f, indent=2, default=str)
print("OK: exported", len(wtp_assets), "assets,", len(wtp_signals), "signals")
