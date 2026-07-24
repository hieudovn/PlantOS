#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== Test timezone formats ==="
for fmt in "2026-07-23T15:00:00+07:00 2026-07-23T16:00:00+07:00" \
           "2026-07-23T08:00:00Z 2026-07-23T09:00:00Z" \
           "2026-07-23T15:00 2026-07-23T16:00" \
           "2026-07-23T08:00 2026-07-23T09:00"; do
  from=$(echo $fmt | cut -d' ' -f1)
  to=$(echo $fmt | cut -d' ' -f2)
  count=$(curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=$from&to=$to" \
    -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
  echo "$from -> $to: $count records"
done

echo ""
echo "=== Current TDengine time ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(ts) from d_comp01_motor_current;" 2>&1 | tail -3

echo ""
echo "=== Seeder last log ==="
tail -2 /tmp/live_seeder2.log

echo DONE
