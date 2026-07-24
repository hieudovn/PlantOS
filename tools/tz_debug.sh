#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== SEEDER DATA ==="
cat /tmp/live_seeder2.log | tail -3

echo "=== TDENGINE RAW ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select count(*) from d_comp01_motor_current; select last(*) from d_comp01_motor_current;" 2>&1 | tail -8

echo "=== API QUERY DEBUG ==="
# Try different time formats
for range in "2026-07-23T07:00:00Z 2026-07-23T09:00:00Z" "2026-07-23T07:00 2026-07-23T09:00" "2026-07-23T14:00:00 2026-07-23T16:00:00"; do
  from=$(echo $range | cut -d' ' -f1)
  to=$(echo $range | cut -d' ' -f2)
  count=$(curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=$from&to=$to" \
    -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
  echo "$from -> $count records"
done

echo DONE
