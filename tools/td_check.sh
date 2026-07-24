#!/bin/bash
echo "=== TDENGINE CONFIG IN BACKEND ==="
docker exec plantos-backend python3 -c "
import os
for k in ['TDENGINE_HOST','TDENGINE_PORT','TDENGINE_DATABASE','TDENGINE_USER','TDENGINE_PASSWORD']:
    print(f'{k}={os.environ.get(k,\"NOT_SET\")}')
" 2>&1

echo ""
echo "=== TEST TDENGINE FROM BACKEND ==="
docker exec plantos-backend python3 -c "
from taosws import connect
try:
    conn = connect(host='tdengine', port=6041, user='root', password='taosdata', database='plantos_ts')
    result = conn.query('show databases')
    for row in result:
        print(row)
    print('TDENGINE_CONNECT_OK')
except Exception as e:
    print(f'TDENGINE_ERROR: {e}')
" 2>&1

echo ""
echo "=== BACKEND HISTORIAN LOG ==="
docker logs plantos-backend 2>&1 | grep -iE 'tdengine|historian|stub|adapter' | head -10

echo ""
echo "=== FIX: RESTART WITH FULL LOGS ==="
docker restart plantos-backend
sleep 6
docker logs plantos-backend 2>&1 | grep -iE 'tdengine|historian|stub|adapter|connect' | head -15

echo DONE
