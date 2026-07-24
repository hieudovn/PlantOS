#!/bin/bash
set -e

echo "=== [1/4] FIXING EDGE V2 CONFIG ==="
cat > /tmp/edge_config.yaml << 'YAMLEOF'
auth:
  users:
    admin:
      display_name: Administrator
      is_active: true
      password_hash: $2b$12$HJXc8NpIHObx5vbmcF2VHubD4aNzWVFunOz8US9rEi9ZUckEGgseG
      role: admin
      synced_at: '2026-07-22T09:54:04.589049+00:00'
    engineer:
      display_name: Engineer
      is_active: true
      password_hash: $2b$12$5ju68S5JJDoYDn1.QmtiS.VzLmVSyJqgnVnuHtR0a9OOQtyp2PGuK
      role: engineer
      synced_at: '2026-07-22T09:54:04.589049+00:00'
    operator:
      display_name: Operator
      is_active: true
      password_hash: $2b$12$DlEKJmrAXfVvGDB5f70V9.8giqvN5zE0AZfIszn0Arq1ScA8dQbu2
      role: operator
      synced_at: '2026-07-22T09:54:04.589049+00:00'
buffer:
  path: /app/data/edge_data.duckdb
  retention_days: 7
center_url: http://plantos-backend:8000
connectors:
  mirror_vf_compressor:
    connection:
      endpoint: opc.tcp://localhost:4840
    enabled: false
    tags: []
    type: opcua
  mirror_wtp_signals:
    connection:
      url: http://localhost:9998/
    enabled: true
    poll_interval_ms: 10000
    tags:
    - data_type: float
      enabled: true
      signal_id: PUMP-101.flow_rate
      source_ref: PUMP-101.flow_rate
      tag_id: PUMP-101_flow_rate
    - data_type: float
      enabled: true
      signal_id: PUMP-101.discharge_pressure
      source_ref: PUMP-101.discharge_pressure
      tag_id: PUMP-101_discharge_pressure
    - data_type: float
      enabled: true
      signal_id: PUMP-101.running_status
      source_ref: PUMP-101.running_status
      tag_id: PUMP-101_running_status
    - data_type: float
      enabled: true
      signal_id: PUMP-101.vibration_rms
      source_ref: PUMP-101.vibration_rms
      tag_id: PUMP-101_vibration_rms
    - data_type: float
      enabled: true
      signal_id: MOTOR-101.motor_current
      source_ref: MOTOR-101.motor_current
      tag_id: MOTOR-101_motor_current
    - data_type: float
      enabled: true
      signal_id: MOTOR-101.motor_temperature
      source_ref: MOTOR-101.motor_temperature
      tag_id: MOTOR-101_motor_temperature
    - data_type: float
      enabled: true
      signal_id: MOTOR-101.running_status
      source_ref: MOTOR-101.running_status
      tag_id: MOTOR-101_running_status
    - data_type: float
      enabled: true
      signal_id: TANK-101.tank_level
      source_ref: TANK-101.tank_level
      tag_id: TANK-101_tank_level
    - data_type: float
      enabled: true
      signal_id: TANK-101.temperature
      source_ref: TANK-101.temperature
      tag_id: TANK-101_temperature
    - data_type: float
      enabled: true
      signal_id: RAW-WATER-QUALITY-STATION-101.raw_turbidity
      source_ref: RAW-WATER-QUALITY-STATION-101.raw_turbidity
      tag_id: RAW-WATER-QUALITY-STATION-101_raw_turbidity
    - data_type: float
      enabled: true
      signal_id: RAW-WATER-QUALITY-STATION-101.raw_ph
      source_ref: RAW-WATER-QUALITY-STATION-101.raw_ph
      tag_id: RAW-WATER-QUALITY-STATION-101_raw_ph
    - data_type: float
      enabled: true
      signal_id: RAW-WATER-QUALITY-STATION-101.raw_temperature
      source_ref: RAW-WATER-QUALITY-STATION-101.raw_temperature
      tag_id: RAW-WATER-QUALITY-STATION-101_raw_temperature
    - data_type: float
      enabled: true
      signal_id: FILTER-101.filter_dp
      source_ref: FILTER-101.filter_dp
      tag_id: FILTER-101_filter_dp
    - data_type: float
      enabled: true
      signal_id: FILTER-101.effluent_flow
      source_ref: FILTER-101.effluent_flow
      tag_id: FILTER-101_effluent_flow
    - data_type: float
      enabled: true
      signal_id: CLEAR-WATER-TANK-101.level
      source_ref: CLEAR-WATER-TANK-101.level
      tag_id: CLEAR-WATER-TANK-101_level
    - data_type: float
      enabled: true
      signal_id: HSP-101.flow_rate
      source_ref: HSP-101.flow_rate
      tag_id: HSP-101_flow_rate
    - data_type: float
      enabled: true
      signal_id: HSP-101-MOTOR.motor_current
      source_ref: HSP-101-MOTOR.motor_current
      tag_id: HSP-101-MOTOR_motor_current
    - data_type: float
      enabled: true
      signal_id: COAG-PUMP-101.flow_rate
      source_ref: COAG-PUMP-101.flow_rate
      tag_id: COAG-PUMP-101_flow_rate
    - data_type: float
      enabled: true
      signal_id: CHLORINE-PUMP-101.flow_rate
      source_ref: CHLORINE-PUMP-101.flow_rate
      tag_id: CHLORINE-PUMP-101_flow_rate
    type: http_poll
edge_node_id: EDGEV2-PC-01
heartbeat:
  interval_seconds: 10
http:
  ingest_url: http://plantos-backend:8000/api/v1/measurements/ingest
mqtt:
  host: plantos-emqx
  port: 1883
  topic_prefix: avenue/demo-plant
plant_id: DEMO-PLANT
publish:
  batch_size: 500
  interval_seconds: 5
web:
  port: 8011
YAMLEOF

echo "Config written. Checking for BOM:"
head -1 /tmp/edge_config.yaml | xxd | head -1

echo ""
echo "=== [2/4] UPDATING .ENV ==="
ENV_FILE="/opt/plantos/deployment/.env"

if ! grep -q '^EDGE_SESSION_SECRET=' "$ENV_FILE"; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "EDGE_SESSION_SECRET=$SECRET" >> "$ENV_FILE"
    echo "Added EDGE_SESSION_SECRET"
fi

if ! grep -q '^EDGE_API_KEY=' "$ENV_FILE"; then
    API_KEY=$(grep '^API_KEYS=' "$ENV_FILE" | cut -d= -f2 | cut -d, -f1)
    echo "EDGE_API_KEY=$API_KEY" >> "$ENV_FILE"
    echo "Added EDGE_API_KEY=$API_KEY"
fi

if ! grep -q '^CENTER_URL=' "$ENV_FILE"; then
    echo "CENTER_URL=http://plantos-backend:8000" >> "$ENV_FILE"
    echo "Added CENTER_URL"
fi

echo "Final .env:"
cat "$ENV_FILE"

echo ""
echo "=== [3/4] RESTARTING EDGE V2 ==="
cd /opt/plantos/deployment
set -a; source "$ENV_FILE" 2>/dev/null; set +a

docker stop plantos-edge-v2 2>/dev/null || true
docker rm plantos-edge-v2 2>/dev/null || true

docker run -d \
  --name plantos-edge-v2 \
  --network deployment_plantos-net \
  -p 127.0.0.1:8011:8011 \
  -e EDGE_CONFIG_PATH=/app/agent/config/config.edge-v2.yaml \
  -e EDGE_SESSION_SECRET="$EDGE_SESSION_SECRET" \
  -e EDGE_CENTER_PASSWORD="$EDGE_CENTER_PASSWORD" \
  -e EDGE_API_KEY="$EDGE_API_KEY" \
  -e CENTER_URL="$CENTER_URL" \
  -v /tmp/edge_config.yaml:/app/agent/config/config.edge-v2.yaml:ro \
  --restart unless-stopped \
  plantos-edge-v2:patched

echo ""
echo "Waiting 8 seconds for startup..."
sleep 8

echo "=== [4/4] VERIFICATION ==="
echo "Container:"
docker ps --filter name=plantos-edge-v2 --format '{{.Names}} {{.Status}}'

echo ""
echo "Recent logs:"
docker logs plantos-edge-v2 --tail 25 2>&1

echo ""
echo "Local API status:"
curl -s http://localhost:8011/api/status 2>&1 | python3 -m json.tool 2>&1 | head -30

echo ""
echo "DONE"
