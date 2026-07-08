"""MQTT Subscribe client — connects, subscribes, caches latest values."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False


class MqttSubscribeClient:
    """MQTT subscriber — connects, subscribes to topics, caches latest values.

    Supports JSONPath extraction: configurable $.value, $.ts, $.quality paths.
    Falls back to plain_text mode (entire payload = value).
    """

    def __init__(self, host: str, port: int = 1883, client_id: str = "edge-v2-mqtt",
                 username: str = "", password: str = "",
                 topic_prefix: str = "", on_message_cb: Callable | None = None):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.topic_prefix = topic_prefix
        self.on_message_cb = on_message_cb
        self._client: mqtt.Client | None = None
        self.is_connected = False
        self._latest_values: dict[str, dict[str, Any]] = {}
        self._subscribed_topics: list[str] = []

    def connect(self) -> bool:
        if not HAS_MQTT:
            logger.warning("paho-mqtt not installed — MQTT unavailable")
            return False
        try:
            self._client = mqtt.Client(client_id=self.client_id)
            if self.username:
                self._client.username_pw_set(self.username, self.password)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.connect(self.host, self.port, keepalive=30)
            self._client.loop_start()
            return True
        except Exception as e:
            logger.warning("MQTT connect failed: %s", e)
            return False

    def _on_connect(self, client, userdata, flags, rc):
        self.is_connected = rc == 0
        if self.is_connected:
            logger.info("MQTT connected to %s:%d", self.host, self.port)
            # Re-subscribe on reconnect
            for topic in self._subscribed_topics:
                client.subscribe(topic)
        else:
            logger.warning("MQTT connection failed: rc=%d", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            topic = msg.topic
            self._latest_values[topic] = {
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "topic": topic,
            }
            if self.on_message_cb:
                self.on_message_cb(topic, payload)
        except Exception as e:
            logger.warning("MQTT message parse error: %s", e)

    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        if self._client:
            full_topic = f"{self.topic_prefix}/{topic}" if self.topic_prefix else topic
            self._client.subscribe(full_topic)
            if full_topic not in self._subscribed_topics:
                self._subscribed_topics.append(full_topic)
            logger.info("MQTT subscribed to %s", full_topic)

    def get_latest(self, topic: str) -> dict[str, Any] | None:
        """Get the latest message for a subscribed topic."""
        full_topic = f"{self.topic_prefix}/{topic}" if self.topic_prefix else topic
        return self._latest_values.get(full_topic)

    def get_all_latest(self) -> dict[str, dict[str, Any]]:
        return dict(self._latest_values)

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        self.is_connected = False

    @staticmethod
    def extract_json_value(payload: str, json_path: str) -> Any:
        """Extract a value from JSON using dot-separated path."""
        try:
            data = json.loads(payload)
            parts = json_path.strip("$.").split(".")
            for part in parts:
                if isinstance(data, dict):
                    data = data.get(part)
                elif isinstance(data, list):
                    try:
                        data = data[int(part)]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
            return data
        except (json.JSONDecodeError, Exception):
            return None
