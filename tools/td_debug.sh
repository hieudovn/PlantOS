#!/bin/bash
echo "=== TEST SAFE NAME ==="
docker exec plantos-backend python3 -c "
import sys; sys.path.insert(0,'/app')
from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
adapter = TDengineHistorianAdapter()
tests = ['COMP-01.motor_current', 'motor_101.motor_current', 'PUMP-101.flow_rate']
for t in tests:
    sn = adapter._safe_name(t)
    print(f'{t} -> d_{sn}')
" 2>&1

echo ""
echo "=== ACTUAL TD TABLES ==="
docker exec plantos-tdengine taos -s "use plantos_ts; show tables;" 2>&1 | grep -E 'd_comp01_motor_current|d_motor_101|d_pump_101' | head -5

echo ""
echo "=== TRY DIRECT QUERY FROM BACKEND ==="
docker exec plantos-backend python3 -c "
from taosws import connect
conn = connect(host='tdengine', port=6041, user='root', password='taosdata', database='plantos_ts')
for table in ['d_comp01_motor_current', 'd_comp_01_motor_current']:
    try:
        result = conn.query(f'SELECT COUNT(*) FROM {table}')
        for row in result:
            print(f'{table}: {row} rows')
    except Exception as e:
        print(f'{table}: ERROR - {str(e)[:80]}')
" 2>&1

echo DONE
