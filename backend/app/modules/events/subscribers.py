"""Event publishing subscribers — bridge internal EventDispatcher to MQTT."""

import logging

from app.modules.events.publisher import MqttPublisher
from app.modules.events.builders import (
    build_signal_value_updated,
    build_signal_quality_changed,
    build_alarm_raised,
    build_alarm_cleared,
    build_edge_heartbeat,
)
from app.modules.events.resolver import resolve_signal_info, resolve_asset_info

logger = logging.getLogger(__name__)

# Track previous quality per signal for change detection
_previous_quality: dict[str, str] = {}


async def on_measurements_ingested(data: dict):
    """Publish SignalValueUpdated events for each ingested measurement."""
    measurements = data.get("measurements", [])
    if not measurements:
        return

    publisher = MqttPublisher.get_instance()

    for m in measurements:
        try:
            signal_id = m.get("signal_id", "")
            if not signal_id:
                continue

            signal_info = resolve_signal_info(signal_id)
            if not signal_info:
                continue

            asset_info = resolve_asset_info(signal_info["asset_id"])
            if not asset_info:
                continue

            # Build and publish SignalValueUpdated
            event = build_signal_value_updated(m, signal_info, asset_info)
            publisher.publish("SignalValueUpdated", event, uns_topic=event["uns_topic"])

            # Check for quality change
            quality = m.get("quality", "GOOD")
            prev = _previous_quality.get(signal_id)
            if prev and prev != quality:
                q_event = build_signal_quality_changed(
                    signal_id, quality, prev, signal_info, asset_info,
                    reason=f"Quality changed from {prev} to {quality}",
                )
                publisher.publish("SignalQualityChanged", q_event)
            _previous_quality[signal_id] = quality

        except Exception:
            logger.exception("Failed to publish event for measurement %s", m.get("signal_id", "?"))


async def on_alarm_raised(data: dict):
    """Publish AlarmRaised event."""
    publisher = MqttPublisher.get_instance()
    try:
        alarm_event = data.get("alarm", {})
        rule_info = data.get("rule", {})
        correlation_id = data.get("correlation_id", "")
        asset_id = alarm_event.get("asset_id") or rule_info.get("asset_id", "")

        asset_info = resolve_asset_info(asset_id)
        if not asset_info:
            logger.warning("Cannot publish AlarmRaised: asset %s not found", asset_id)
            return

        event = build_alarm_raised(alarm_event, rule_info, asset_info, correlation_id or None)
        publisher.publish("AlarmRaised", event)
    except Exception:
        logger.exception("Failed to publish AlarmRaised event")


async def on_alarm_cleared(data: dict):
    """Publish AlarmCleared event."""
    publisher = MqttPublisher.get_instance()
    try:
        alarm_event = data.get("alarm", {})
        rule_info = data.get("rule", {})
        correlation_id = data.get("correlation_id", "")
        asset_id = alarm_event.get("asset_id") or rule_info.get("asset_id", "")

        asset_info = resolve_asset_info(asset_id)
        if not asset_info:
            logger.warning("Cannot publish AlarmCleared: asset %s not found", asset_id)
            return

        event = build_alarm_cleared(alarm_event, rule_info, asset_info, correlation_id)
        publisher.publish("AlarmCleared", event)
    except Exception:
        logger.exception("Failed to publish AlarmCleared event")


async def on_edge_heartbeat(data: dict):
    """Publish EdgeHeartbeatReceived event."""
    publisher = MqttPublisher.get_instance()
    try:
        edge_data = data.get("edge", {})
        event = build_edge_heartbeat(edge_data)
        publisher.publish("EdgeHeartbeatReceived", event)
    except Exception:
        logger.exception("Failed to publish EdgeHeartbeatReceived event")
