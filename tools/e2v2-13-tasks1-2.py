#!/usr/bin/env python3
"""E2V2-13 Task 1+2: Update simulator to 19 signals and reconfigure v2 connector."""
import subprocess, json, yaml, sys, time

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd: str) -> str:
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"  WARN: {r.stderr[:200]}")
    return r.stdout.strip()

def scp(local: str, remote: str):
    subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", local, f"{USER}@{VPS}:{remote}"],
                   capture_output=True, timeout=30)

print("=== E2V2-13 Task 1: Expand HTTP Simulator to 19 Signals ===")

# Step 1: Backup old simulator
print("\n1. Backing up old simulator...")
ssh("cp /tmp/http_simulator.py /tmp/http_simulator.py.bak 2>/dev/null; echo done")

# Step 2: Kill old simulator
print("2. Killing old simulator...")
ssh("kill 865751 2>/dev/null; sleep 2; echo done")

# Step 3: SCP and start 19-signal simulator
print("3. Starting 19-signal simulator...")
scp("d:/Project/Github/PlantOS/edge-v2/scripts/http_simulator_19.py",
    "/tmp/http_simulator_19.py")
ssh("cp /tmp/http_simulator_19.py /tmp/http_simulator.py")
pid = ssh("nohup python3 /tmp/http_simulator.py > /tmp/http_simulator.log 2>&1 & echo $!")
print(f"   Simulator PID: {pid}")
time.sleep(3)

# Step 4: Verify 19 signals
print("4. Verifying 19 signals...")
sig_out = ssh("curl -s http://localhost:9998/ | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))'")
print(f"   Signals: {sig_out}")

# Step 5: Build new connector config
print("\n=== Task 2: Update v2 Connector Config ===")

new_connectors = {
    "mirror_wtp_signals": {
        "type": "http_poll", "enabled": True,
        "connection": {"url": "http://localhost:9998/"},
        "poll_interval_ms": 10000,
        "tags": [
            {"tag_id": "PUMP-101_flow_rate", "source_ref": "PUMP-101.flow_rate", "signal_id": "PUMP-101.flow_rate", "data_type": "float", "enabled": True},
            {"tag_id": "PUMP-101_discharge_pressure", "source_ref": "PUMP-101.discharge_pressure", "signal_id": "PUMP-101.discharge_pressure", "data_type": "float", "enabled": True},
            {"tag_id": "PUMP-101_running_status", "source_ref": "PUMP-101.running_status", "signal_id": "PUMP-101.running_status", "data_type": "float", "enabled": True},
            {"tag_id": "PUMP-101_vibration_rms", "source_ref": "PUMP-101.vibration_rms", "signal_id": "PUMP-101.vibration_rms", "data_type": "float", "enabled": True},
            {"tag_id": "MOTOR-101_motor_current", "source_ref": "MOTOR-101.motor_current", "signal_id": "MOTOR-101.motor_current", "data_type": "float", "enabled": True},
            {"tag_id": "MOTOR-101_motor_temperature", "source_ref": "MOTOR-101.motor_temperature", "signal_id": "MOTOR-101.motor_temperature", "data_type": "float", "enabled": True},
            {"tag_id": "MOTOR-101_running_status", "source_ref": "MOTOR-101.running_status", "signal_id": "MOTOR-101.running_status", "data_type": "float", "enabled": True},
            {"tag_id": "TANK-101_tank_level", "source_ref": "TANK-101.tank_level", "signal_id": "TANK-101.tank_level", "data_type": "float", "enabled": True},
            {"tag_id": "TANK-101_temperature", "source_ref": "TANK-101.temperature", "signal_id": "TANK-101.temperature", "data_type": "float", "enabled": True},
            {"tag_id": "RAW-WATER-QUALITY-STATION-101_raw_turbidity", "source_ref": "RAW-WATER-QUALITY-STATION-101.raw_turbidity", "signal_id": "RAW-WATER-QUALITY-STATION-101.raw_turbidity", "data_type": "float", "enabled": True},
            {"tag_id": "RAW-WATER-QUALITY-STATION-101_raw_ph", "source_ref": "RAW-WATER-QUALITY-STATION-101.raw_ph", "signal_id": "RAW-WATER-QUALITY-STATION-101.raw_ph", "data_type": "float", "enabled": True},
            {"tag_id": "RAW-WATER-QUALITY-STATION-101_raw_temperature", "source_ref": "RAW-WATER-QUALITY-STATION-101.raw_temperature", "signal_id": "RAW-WATER-QUALITY-STATION-101.raw_temperature", "data_type": "float", "enabled": True},
            {"tag_id": "FILTER-101_filter_dp", "source_ref": "FILTER-101.filter_dp", "signal_id": "FILTER-101.filter_dp", "data_type": "float", "enabled": True},
            {"tag_id": "FILTER-101_effluent_flow", "source_ref": "FILTER-101.effluent_flow", "signal_id": "FILTER-101.effluent_flow", "data_type": "float", "enabled": True},
            {"tag_id": "CLEAR-WATER-TANK-101_level", "source_ref": "CLEAR-WATER-TANK-101.level", "signal_id": "CLEAR-WATER-TANK-101.level", "data_type": "float", "enabled": True},
            {"tag_id": "HSP-101_flow_rate", "source_ref": "HSP-101.flow_rate", "signal_id": "HSP-101.flow_rate", "data_type": "float", "enabled": True},
            {"tag_id": "HSP-101-MOTOR_motor_current", "source_ref": "HSP-101-MOTOR.motor_current", "signal_id": "HSP-101-MOTOR.motor_current", "data_type": "float", "enabled": True},
            {"tag_id": "COAG-PUMP-101_flow_rate", "source_ref": "COAG-PUMP-101.flow_rate", "signal_id": "COAG-PUMP-101.flow_rate", "data_type": "float", "enabled": True},
            {"tag_id": "CHLORINE-PUMP-101_flow_rate", "source_ref": "CHLORINE-PUMP-101.flow_rate", "signal_id": "CHLORINE-PUMP-101.flow_rate", "data_type": "float", "enabled": True},
        ]
    },
    "mirror_vf_compressor": {
        "type": "opcua", "enabled": False,
        "connection": {"endpoint": "opc.tcp://localhost:4840"},
        "tags": []
    }
}

# Read existing config from container
out = ssh("docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml")
cfg = yaml.safe_load(out)
cfg["connectors"] = new_connectors

# Write updated config back
new_yaml = yaml.dump(cfg, default_flow_style=False, indent=2)
# Escape for shell
escaped = new_yaml.replace("'", "'\\''")
ssh(f"""docker exec -i plantos-edge-v2 bash -c 'cat > /app/agent/config/config.edge-v2.yaml' << 'EOF'
{new_yaml}
EOF""")
print("5. Config updated successfully")

# Verify
print("6. Verifying config...")
v = ssh("docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml | grep -A3 'mirror_wtp_signals' | head -6")
print(f"   {v[:200]}")

# Restart v2
print("7. Restarting v2...")
ssh("docker restart plantos-edge-v2")
time.sleep(10)

# Verify v2
print("8. Verifying v2...")
v2 = ssh("""python3 -c "
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f'status={d[\"status\"]}')
for c in d['connectors']['list']:
    print(f'  {c[\"connector_id\"]}: sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
" """)
print(f"   {v2}")

print("\n=== Tasks 1+2 Complete ===")
