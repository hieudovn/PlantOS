#!/usr/bin/env python3
"""Fix Edge v2 connector config — point HTTP Poll to simulator port 9998."""
path = '/home/plantos/edge-v2/agent/config/config.edge-v2.yaml'
with open(path) as f:
    content = f.read()

# Fix url: change ingest endpoint to simulator
content = content.replace(
    'url: http://172.17.0.1:8000/api/v1/measurements/ingest',
    'url: http://172.17.0.1:9998/')
# Also fix old localhost:8000 version if present
content = content.replace(
    'url: http://localhost:8000/api/v1/measurements/ingest',
    'url: http://172.17.0.1:9998/')

with open(path, 'w') as f:
    f.write(content)

# Verify
import yaml
with open(path) as f:
    cfg = yaml.safe_load(f)
url = cfg['connectors']['mirror_wtp_signals']['connection']['url']
print(f'Connector URL: {url}')
print('Config fixed — restart Edge v2 to apply.')
