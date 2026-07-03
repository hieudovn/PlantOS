#!/bin/bash
echo "=== COUNT(*) full scan ==="
sudo docker exec plantos-tdengine taos -s "SELECT COUNT(*) FROM plantos_ts.measurements;" 2>&1 | grep 'Query OK'

echo ""
echo "=== AVG/MAX/MIN/STDDEV with INTERVAL(10m) ==="
sudo docker exec plantos-tdengine taos -s "SELECT AVG(value), MAX(value), MIN(value), STDDEV(value) FROM plantos_ts.measurements WHERE signal_id='RAW-WATER-QUALITY-STATION-101.raw_turbidity' INTERVAL(10m) LIMIT 20;" 2>&1 | tail -25

echo ""
echo "=== Last 10 rows for a signal ==="
sudo docker exec plantos-tdengine taos -s "SELECT ts, value FROM plantos_ts.measurements WHERE signal_id='HSP-101.flow_rate' ORDER BY ts DESC LIMIT 10;" 2>&1 | tail -15

echo ""
echo "=== Data duration ==="
sudo docker exec plantos-tdengine taos -s "SELECT FIRST(ts), LAST(ts) FROM plantos_ts.measurements;" 2>&1 | tail -10

echo ""
echo "=== Disk usage ==="
sudo du -sh /var/lib/docker/volumes/deployment_tdengine_data/_data 2>/dev/null
