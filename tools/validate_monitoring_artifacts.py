"""Validate monitoring artifact files."""
import yaml, json

# 1. Binding YAML
y = yaml.safe_load(open("examples/diagrams/wtp-demo-01-process.binding.yaml"))
bindings = y.get("bindings", [])
print(f"Binding YAML: {len(bindings)} bindings")

# Check all bindings have required fields
for b in bindings:
    assert "binding_id" in b, f"Missing binding_id in {b}"
    assert "selector" in b, f"Missing selector in {b}"
    assert "asset_id" in b, f"Missing asset_id in {b}"
    assert "signal_name" in b, f"Missing signal_name in {b}"
print("  All bindings have required fields ✓")

# 2. GIS JSON
j = json.load(open("examples/gis/wtp-demo-01-site-layout.json"))
print(f"\nGIS JSON: {len(j['areas'])} areas, {len(j['assets'])} assets")
area_ids = {a["area_id"] for a in j["areas"]}
for a in j["assets"]:
    assert a["area_id"] in area_ids, f"Asset {a['asset_id']} references unknown area {a['area_id']}"
print("  All assets reference valid areas ✓")

# 3. Trends YAML
y2 = yaml.safe_load(open("examples/diagrams/wtp-demo-01-trends.yaml"))
bundles = y2.get("bundles", {})
print(f"\nTrends YAML: {len(bundles)} bundles")
for name, cfg in bundles.items():
    signals = cfg.get("signals", [])
    print(f"  {name}: {len(signals)} signals")

# 4. SVG
svg = open("examples/diagrams/wtp-demo-01-process.svg").read()
lines = svg.split("\n")
# Count elements with id attributes (excluding arrow marker)
id_count = svg.count("id=\"")
print(f"\nSVG: {len(lines)} lines")
print(f"  Elements with IDs: {id_count}")
print("\n✅ All files valid")
