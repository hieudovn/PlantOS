#!/bin/bash
echo "=== VF Log ==="
tail -3 /tmp/vf.log

echo "=== Edge OPC UA ==="
curl -s http://localhost:8001/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
opc = d.get('opcua', {})
print(f\"enabled={opc.get('enabled')}, connected={opc.get('connected')}, signals={opc.get('signal_count')}\")
"

echo "=== Center COMP01-CORE ==="
curl -s 'http://localhost:8000/api/v1/measurements/current?asset_id=COMP01-CORE' | python3 -c "
import sys, json
d = json.load(sys.stdin)
signals = d.get('value', d)
print(f'{len(signals)} signals')
for s in signals[:5]:
    v = s.get('value', '?')
    print(f\"  {s['signal_id']} = {v}\")
"
