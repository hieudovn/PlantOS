import urllib.request, json

r = urllib.request.urlopen('http://localhost:8000/api/v1/assets?plant_id=VF-DEMO')
data = json.loads(r.read())
print(f'VF-DEMO assets: {len(data)}')
for a in data:
    print(f'  {a["asset_id"]}: {a["name"]} ({a["asset_type"]})')
