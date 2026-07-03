"""Check Edge Agent cache for WTP assets."""
import json

with open("/opt/plantos/edge/agent/metadata_cache.json") as f:
    d = json.load(f)

assets = d.get("assets", [])
signals = d.get("signals", [])
print(f"Cache: {len(assets)} assets, {len(signals)} signals")

# Show asset_id list (first and last few)
ids = [a["asset_id"] for a in assets]
print(f"Asset IDs: {ids[:3]} ... {ids[-3:]}")
has_vfdemo = any("COMP01" in a["asset_id"] for a in assets)
has_wtp = any("WTP" in a["asset_id"] or "RWP" in a["asset_id"] for a in assets)
print(f"VF-DEMO assets: {has_vfdemo}")
print(f"WTP assets: {has_wtp}")
print(f"Asset count: VF={sum(1 for a in assets if 'COMP' in a['asset_id'])}, WTP={sum(1 for a in assets if 'COMP' not in a['asset_id'])}")
