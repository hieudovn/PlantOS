#!/usr/bin/env python3
"""
Generate Edge V2 config from the PlantOS Integration Contract.
Reads examples/vf-plantos-contract.yaml to extract OPC UA bindings,
merges with existing WTP HTTP Poll config.
"""

import yaml
import sys
from pathlib import Path

CONTRACT_PATH = "/opt/plantos/examples/vf-plantos-contract.yaml"
OUTPUT_PATH = "/tmp/edge_config.yaml"

def main():
    with open(CONTRACT_PATH) as f:
        contract = yaml.safe_load(f)

    signals = contract.get("signals", [])
    print(f"Contract: {len(signals)} signals from {contract['plant']['plant_id']}")

    # Generate OPC UA tags from contract signals
    opcua_tags = []
    for sig in signals:
        node_id = sig.get("opcua_node_id")
        if not node_id:
            continue
        tag = {
            "tag_id": sig["signal_id"].replace(".", "_").replace("-", "_"),
            "source_ref": node_id,
            "signal_id": sig["signal_id"],
            "data_type": sig.get("data_type", "float"),
            "scale": sig.get("scale", 1.0),
            "enabled": True,
        }
        opcua_tags.append(tag)

    print(f"OPC UA tags generated: {len(opcua_tags)}")

    # Build the full config
    config = {
        "auth": {
            "users": {
                "admin": {
                    "display_name": "Administrator",
                    "is_active": True,
                    "password_hash": "$2b$12$HJXc8NpIHObx5vbmcF2VHubD4aNzWVFunOz8US9rEi9ZUckEGgseG",
                    "role": "admin",
                    "synced_at": "2026-07-22T09:54:04.589049+00:00",
                },
                "engineer": {
                    "display_name": "Engineer",
                    "is_active": True,
                    "password_hash": "$2b$12$5ju68S5JJDoYDn1.QmtiS.VzLmVSyJqgnVnuHtR0a9OOQtyp2PGuK",
                    "role": "engineer",
                    "synced_at": "2026-07-22T09:54:04.589049+00:00",
                },
                "operator": {
                    "display_name": "Operator",
                    "is_active": True,
                    "password_hash": "$2b$12$DlEKJmrAXfVvGDB5f70V9.8giqvN5zE0AZfIszn0Arq1ScA8dQbu2",
                    "role": "operator",
                    "synced_at": "2026-07-22T09:54:04.589049+00:00",
                },
            }
        },
        "buffer": {"path": "/app/data/edge_data.duckdb", "retention_days": 7},
        "center_url": "http://plantos-backend:8000",
        "edge_node_id": "EDGEV2-PC-01",
        "heartbeat": {"interval_seconds": 10},
        "http": {"ingest_url": "http://plantos-backend:8000/api/v1/measurements/ingest"},
        "mqtt": {"host": "plantos-emqx", "port": 1883, "topic_prefix": "avenue/demo-plant"},
        "plant_id": "DEMO-PLANT",
        "publish": {"batch_size": 500, "interval_seconds": 5},
        "web": {"port": 8011},
        "connectors": {
            # OPC UA connector for VF Compressor (from contract)
            "mirror_vf_compressor": {
                "type": "opcua",
                "connection": {
                    "endpoint": "opc.tcp://172.19.0.1:4840",
                    "timeout": 5.0,
                },
                "enabled": True,
                "poll_interval_ms": 30000,
                "tags": opcua_tags,
            },
            # HTTP Poll connector for WTP (existing, keep as-is)
            "mirror_wtp_signals": {
                "type": "http_poll",
                "connection": {"url": "http://localhost:9998/"},
                "enabled": True,
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
                ],
            },
        },
    }

    with open(OUTPUT_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Config written to {OUTPUT_PATH}")
    print(f"  OPC UA: {len(opcua_tags)} tags, endpoint=opc.tcp://172.19.0.1:4840")
    print(f"  HTTP Poll: 19 tags, endpoint=http://localhost:9998/")

if __name__ == "__main__":
    main()
