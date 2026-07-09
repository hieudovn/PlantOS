#!/bin/bash
echo "=== Check host config ==="
ls -la /home/plantos/edge-v2/agent/config/config.edge-v2.yaml
echo "=== Host config contents ==="
python3 -c "
import yaml
with open('/home/plantos/edge-v2/agent/config/config.edge-v2.yaml') as f:
    c = yaml.safe_load(f)
wtp = c['connectors']['mirror_wtp_signals']
print('tags=' + str(len(wtp['tags'])))
print('url=' + wtp['connection']['url'])
"
