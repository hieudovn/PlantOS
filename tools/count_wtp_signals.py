"""Count signals by area for WTP contract."""
import yaml
from collections import Counter

with open("examples/contracts/wtp-demo-01.contract.yaml") as f:
    data = yaml.safe_load(f)

areas = data["areas"]
assets = data["assets"]
signals = data["signals"]

area_counts = Counter()
for s in signals:
    for a in assets:
        if a["asset_id"] == s["asset_id"]:
            area_counts[a["area_id"]] += 1
            break

print("=== Signal Count by Area ===")
for area in areas:
    aid = area["area_id"]
    print(f"  {aid}: {area_counts.get(aid, 0)} signals")

print(f"\n=== Summary ===")
print(f"  Areas:  {len(areas)}")
print(f"  Assets: {len(assets)}")
print(f"  Signals:{len(signals)}")
print(f"  Behaviors: {len(data['simulation']['behaviors'])}")
print(f"  OPC UA bindings: {len(data['bindings']['opcua'])}")
print(f"  Alarm rules: {len(data['extensions']['monitoring']['alarm_recommendations'])}")
