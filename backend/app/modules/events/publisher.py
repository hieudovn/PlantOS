"""MQTT event publisher — singleton client to EMQX."""

import json
import logging
import secrets

import paho.mqtt.publish as mqtt_publish

from app.core.config import settings

logger = logging.getLogger(__name__)

# QoS mapping per contract §6
EVENT_QOS: dict[str, int] = {
    "SignalValueUpdated": 0,
    "AssetStatusChanged": 1,
    "AlarmRaised": 1,
    "AlarmCleared": 1,
    "SignalQualityChanged": 1,
    "EdgeHeartbeatReceived": 0,
}


def get_event_topic(event_type: str, uns_topic: str | None = None) -> str:
    """Return the MQTT topic for an event type.

    SignalValueUpdated uses the signal UNS topic.
    All other types use plantos/events/{event_type}.
    """
    if event_type == "SignalValueUpdated" and uns_topic:
        return uns_topic
    return f"plantos/events/{event_type}"


class MqttPublisher:
    """Singleton MQTT publisher for runtime events."""

    _instance: "MqttPublisher | None" = None

    def __init__(self):
        # One-shot publish mode — no persistent client needed
        self._connected = True
        self._started = False

    @classmethod
    def get_instance(cls) -> "MqttPublisher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def connected(self) -> bool:
        return self._connected

    def start(self):
        """No-op — one-shot publish creates its own connection per publish."""
        if self._started:
            return
        self._started = True
        logger.info("MQTT one-shot publisher ready (EMQX at %s:%s)", settings.EMQX_HOST, settings.EMQX_MQTT_PORT)

    def stop(self):
        """No-op — no persistent connection to clean up."""
        self._started = False
        logger.info("MQTT publisher stopped")

    def publish(self, event_type: str, payload: dict, uns_topic: str | None = None):
        """Publish an event to MQTT.

        Uses one-shot publish (new TCP connection per publish) to avoid
        persistent connection issues with EMQX session management.
        Fire-and-forget: logs errors but does not raise.
        """
        try:
            topic = get_event_topic(event_type, uns_topic)
            qos = EVENT_QOS.get(event_type, 0)
            payload_str = json.dumps(payload, default=str)

            # One-shot publish: connect, send, disconnect
            mqtt_publish.single(
                topic,
                payload_str,
                qos=qos,
                hostname=settings.EMQX_HOST,
                port=settings.EMQX_MQTT_PORT,
                client_id=f"plantos-events-{secrets.token_hex(4)}",
            )
            logger.debug("Published %s to %s (qos=%s)", event_type, topic, qos)
        except Exception:
            logger.exception("MQTT publish error for %s", event_type)
