#!/usr/bin/env python3
"""Update only the connectors section of the host config file."""
import yaml, subprocess, time

# Read current host config
with open('/home/plantos/edge-v2/agent/config/config.edge-v2.yaml') as f:
    config = yaml.safe_load(f)

# Build 19-tag connector config
tags = []
signal_ids = [
    'PUMP-101.flow_rate', 'PUMP-101.discharge_pressure', 'PUMP-101.running_status',
    'PUMP-101.vibration_rms', 'MOTOR-101.motor_current', 'MOTOR-101.motor_temperature',
    'MOTOR-101.running_status', 'TANK-101.tank_level', 'TANK-101.temperature',
    'RAW-WATER-QUALITY-STATION-101.raw_turbidity', 'RAW-WATER-QUALITY-STATION-101.raw_ph',
    'RAW-WATER-QUALITY-STATION-101.raw_temperature', 'FILTER-101.filter_dp',
    'FILTER-101.effluent_flow', 'CLEAR-WATER-TANK-101.level', 'HSP-101.flow_rate',
    'HSP-101-MOTOR.motor_current', 'COAG-PUMP-101.flow_rate', 'CHLORINE-PUMP-101.flow_rate',
]

for sig_id in signal_ids:
    tag_id = sig_id.replace('.', '_').replace('-', '-')
    tags.append({
        'tag_id': tag_id,
        'source_ref': sig_id,
        'signal_id': sig_id,
        'data_type': 'float',
        'enabled': True,
    })

# Update connectors
config['connectors'] = {
    'mirror_wtp_signals': {
        'type': 'http_poll',
        'enabled': True,
        'connection': {'url': 'http://localhost:9998/'},
        'poll_interval_ms': 10000,
        'tags': tags,
    },
    'mirror_vf_compressor': {
        'type': 'opcua',
        'enabled': False,
        'connection': {'endpoint': 'opc.tcp://localhost:4840'},
        'tags': [],
    },
}

# Write back
with open('/home/plantos/edge-v2/agent/config/config.edge-v2.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)

# Verify
with open('/home/plantos/edge-v2/agent/config/config.edge-v2.yaml') as f:
    c2 = yaml.safe_load(f)
wtp = c2['connectors']['mirror_wtp_signals']
print(f"tags={len(wtp['tags'])} url={wtp['connection']['url']}")
print(f"buffer path: {c2['buffer']['path']}")

# Restart
subprocess.run(['docker', 'restart', 'plantos-edge-v2'])
time.sleep(15)

# Verify connectors
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f"status={d['status']}")
for c in d['connectors']['list']:
    print(f"  {c['connector_id']}: sig={c['signal_count']} {c['status']}")
