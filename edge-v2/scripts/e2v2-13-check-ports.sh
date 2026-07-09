#!/bin/bash
echo "=== Port 9999 ==="
curl -s http://localhost:9999/ 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Signals: {len(d)}')
for k in list(d.keys())[:5]:
    print(f'  {k}')
" 2>/dev/null || echo "No response"

echo "=== Port 9998 ==="
curl -s http://localhost:9998/ 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Signals: {len(d)}')
for k in list(d.keys())[:5]:
    print(f'  {k}')
" 2>/dev/null || echo "No response"
