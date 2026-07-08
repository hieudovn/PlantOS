"""Event envelope builders — produce contract-compliant MQTT payloads."""

import secrets
from datetime import datetime, timezone

from app.modules.signals.uns import build_uns_topic


def _make_event_id(entity_id: str, timestamp: datetime | None = None) -> str:
    """Generate event_id per contract §5.

    Format: plantos-{entity_id_lower}-{YYYYMMDDTHHMMSSZ}-{random6}
    """
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y%m%dt%H%M%Sz")
    random6 = secrets.token_hex(3)  # 6 hex chars
    return f"plantos-{entity_id.lower()}-{ts}-{random6}"


def _make_correlation_id(entity_type: str, asset_id: str, instance_key: str, timestamp: datetime | None = None) -> str:
    """Generate correlation_id for alarm pairs per contract §7.

    Format: alarm-{asset_id}-{alarm_code}-{ISO8601}
    """
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{entity_type}-{asset_id}-{instance_key}-{ts}"


def build_signal_value_updated(measurement: dict, signal_info: dict, asset_info: dict) -> dict:
    """Build SignalValueUpdated event per contract §4.1."""
    now = datetime.now(timezone.utc)
    signal_id = measurement["signal_id"]
    uns_topic = build_uns_topic(
        plant_id=asset_info["plant_id"],
        area_id=asset_info["area_id"],
        asset_id=asset_info["asset_id"],
        signal_category=signal_info.get("signal_category", "measurement"),
        signal_name=signal_info.get("signal_name", signal_id.split(".")[-1] if "." in signal_id else signal_id),
    )
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(signal_id, now),
        "correlation_id": None,
        "event_type": "SignalValueUpdated",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": {
            "signal_id": signal_id,
            "signal_name": signal_info.get("signal_name", ""),
            "signal_category": signal_info.get("signal_category", "measurement"),
            "data_type": signal_info.get("data_type", "float"),
            "engineering_unit": signal_info.get("engineering_unit", ""),
        },
        "edge": None,
        "alarm": None,
        "uns_topic": uns_topic,
        "payload": {
            "value": measurement["value"],
            "quality": measurement.get("quality", "GOOD"),
        },
    }


def build_signal_quality_changed(signal_id: str, quality: str, previous_quality: str,
                                  signal_info: dict, asset_info: dict, reason: str = "") -> dict:
    """Build SignalQualityChanged event per contract §4.5."""
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"{signal_id}.quality", now),
        "correlation_id": None,
        "event_type": "SignalQualityChanged",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": {
            "signal_id": signal_id,
            "signal_name": signal_info.get("signal_name", ""),
            "signal_category": signal_info.get("signal_category", "measurement"),
        },
        "edge": None,
        "alarm": None,
        "uns_topic": "plantos/events/SignalQualityChanged",
        "payload": {
            "quality": quality,
            "previous_quality": previous_quality,
            "reason": reason,
        },
    }


def build_alarm_raised(alarm_event: dict, rule_info: dict, asset_info: dict, correlation_id: str | None = None) -> dict:
    """Build AlarmRaised event per contract §4.3.

    If correlation_id is provided, it is used as-is for pairing with AlarmCleared.
    Otherwise a new one is generated (fallback for standalone use).
    """
    now = datetime.now(timezone.utc)
    alarm_code = rule_info.get("alarm_code", rule_info.get("name", "UNKNOWN"))
    cid = correlation_id or _make_correlation_id("alarm", asset_info["asset_id"], alarm_code, now)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"alarm.{alarm_event['alarm_id']}", now),
        "correlation_id": cid,
        "event_type": "AlarmRaised",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": None,
        "edge": None,
        "alarm": {
            "alarm_code": alarm_code,
            "severity": rule_info.get("severity", "warning"),
            "description": alarm_event.get("message", ""),
            "state": "raised",
            "threshold_value": rule_info.get("threshold"),
            "actual_value": alarm_event.get("trigger_value"),
        },
        "uns_topic": "plantos/events/AlarmRaised",
        "payload": {},
    }


def build_alarm_cleared(alarm_event: dict, rule_info: dict, asset_info: dict, correlation_id: str) -> dict:
    """Build AlarmCleared event per contract §4.4."""
    now = datetime.now(timezone.utc)
    alarm_code = rule_info.get("alarm_code", rule_info.get("name", "UNKNOWN"))
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"alarm.{alarm_event['alarm_id']}.cleared", now),
        "correlation_id": correlation_id,
        "event_type": "AlarmCleared",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": None,
        "edge": None,
        "alarm": {
            "alarm_code": alarm_code,
            "severity": rule_info.get("severity", "warning"),
            "state": "cleared",
            "cleared_by": "auto",
        },
        "uns_topic": "plantos/events/AlarmCleared",
        "payload": {},
    }


def build_edge_heartbeat(edge_data: dict) -> dict:
    """Build EdgeHeartbeatReceived event per contract §4.6."""
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"edge.{edge_data['edge_node_id']}.heartbeat", now),
        "correlation_id": None,
        "event_type": "EdgeHeartbeatReceived",
        "timestamp": now.isoformat(),
        "asset": None,
        "signal": None,
        "edge": {
            "edge_id": edge_data["edge_node_id"],
            "status": edge_data.get("status", "online"),
            "ip_address": edge_data.get("ip_address", ""),
            "signal_count": edge_data.get("signal_count", 0),
            "version": edge_data.get("version", ""),
        },
        "alarm": None,
        "uns_topic": "plantos/events/EdgeHeartbeatReceived",
        "payload": {},
    }


def build_asset_status_changed(asset_id: str, status: str, previous_status: str,
                                asset_info: dict, reason: str = "") -> dict:
    """Build AssetStatusChanged event per contract §4.2."""
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"asset.{asset_id}.status", now),
        "correlation_id": None,
        "event_type": "AssetStatusChanged",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": None,
        "edge": None,
        "alarm": None,
        "uns_topic": "plantos/events/AssetStatusChanged",
        "payload": {
            "status": status,
            "previous_status": previous_status,
            "reason": reason,
        },
    }
