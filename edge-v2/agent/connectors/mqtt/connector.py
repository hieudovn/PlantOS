"""MQTT Subscribe Connector — implements BaseConnector for MQTT subscription.

NEW — no Edge v1 equivalent. Listens to MQTT topics and caches latest values.
Not poll-based: read_tags() returns latest cached values from subscribed topics.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import (
    BaseConnector, ConnectorStatus, RawReading, TagConfig, TestResult,
)
from agent.connectors.mqtt.client import MqttSubscribeClient

logger = logging.getLogger(__name__)


class MqttSubscribeConnector(BaseConnector):
    """MQTT Subscribe connector — subscribes to topics, caches latest values.

    JSONPath mode: extract $.value, $.ts, $.quality from JSON payload.
    Plain text mode: entire payload = value, current time = timestamp.
    """

    def __init__(self, connector_id: str, config: dict):
        super().__init__(connector_id, config)
        self.connector_type = "mqtt"
        conn = config.get("connection", {})
        self.client = MqttSubscribeClient(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 1883),
            client_id=conn.get("client_id", f"edge-v2-{connector_id}"),
            username=conn.get("username", ""),
            password=conn.get("password", ""),
            topic_prefix=conn.get("topic_prefix", ""),
            on_message_cb=self._on_message,
        )
        tags_raw = config.get("tags", [])
        self.tags = [TagConfig(**t) if isinstance(t, dict) else t for t in tags_raw]
        self._json_value_path = config.get("json_value_path", "$.value")
        self._json_ts_path = config.get("json_ts_path", "$.ts")
        self._json_quality_path = config.get("json_quality_path", "$.quality")
        self._parse_mode = config.get("parse_mode", "jsonpath")  # jsonpath or plain_text
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._last_error_at: datetime | None = None

    def _on_message(self, topic: str, payload: str):
        """Callback for incoming MQTT messages. Parse and cache."""
        try:
            for tag in self.tags:
                if not tag.enabled:
                    continue
                match_topic = f"{self.client.topic_prefix}/{tag.source_ref}" if self.client.topic_prefix else tag.source_ref
                if topic == match_topic:
                    if self._parse_mode == "jsonpath":
                        value = MqttSubscribeClient.extract_json_value(payload, self._json_value_path)
                        if value is None:
                            continue
                        value = float(value)
                    else:
                        value = float(payload.strip())

                    self._last_success = datetime.now(timezone.utc)
                    break
        except Exception as e:
            logger.warning("MQTT message parse error: %s", e)

    async def validate_config(self, config: dict) -> list[str]:
        errors = []
        conn = config.get("connection", {})
        if not conn.get("host"):
            errors.append("Missing 'connection.host'")
        tags = config.get("tags", [])
        if not tags:
            errors.append("At least one tag mapping required")
        return errors

    async def test_connection(self) -> TestResult:
        import time
        conn = self.config.get("connection", {})
        test_client = MqttSubscribeClient(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 1883),
            client_id="edge-v2-test",
            username=conn.get("username", ""),
            password=conn.get("password", ""),
        )
        start = time.monotonic()
        ok = test_client.connect()
        elapsed = (time.monotonic() - start) * 1000
        if ok:
            test_client.disconnect()
            return TestResult(success=True, message="MQTT broker reachable",
                              latency_ms=round(elapsed, 1))
        return TestResult(success=False, message="MQTT connection failed",
                          latency_ms=round(elapsed, 1))

    async def start(self):
        ok = self.client.connect()
        if ok:
            # Subscribe to configured topics
            for tag in self.tags:
                if tag.enabled:
                    self.client.subscribe(tag.source_ref)
            self._running = True
            logger.info("MQTT Subscribe connector '%s' started with %d tags",
                        self.connector_id, len([t for t in self.tags if t.enabled]))
        else:
            logger.warning("MQTT Subscribe connector '%s' failed to connect", self.connector_id)

    async def stop(self):
        self.client.disconnect()
        self._running = False

    async def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_id=self.connector_id,
            type=self.connector_type,
            status="running" if self._running else "stopped",
            connected=self.client.is_connected,
            signal_count=len(self.tags),
            last_success_at=self._last_success,
            last_error=self._last_error,
            last_error_at=self._last_error_at,
        )

    async def read_tags(self, tag_configs: list[TagConfig]) -> list[RawReading]:
        """Return latest cached values from subscribed topics."""
        now = datetime.now(timezone.utc)
        readings = []
        latest = self.client.get_all_latest() if self.client else {}

        for tag in tag_configs:
            if not tag.enabled:
                continue
            full_topic = f"{self.client.topic_prefix}/{tag.source_ref}" if self.client.topic_prefix else tag.source_ref
            cached = latest.get(full_topic)
            if not cached:
                continue

            try:
                payload = cached["payload"]
                if self._parse_mode == "jsonpath":
                    value = MqttSubscribeClient.extract_json_value(payload, self._json_value_path)
                    if value is None:
                        continue
                    value = float(value)
                else:
                    value = float(payload.strip())

                readings.append(RawReading(
                    source_ref=tag.source_ref,
                    signal_id=tag.signal_id,
                    raw_value=value,
                    timestamp=now,
                ))
            except (ValueError, TypeError) as e:
                logger.debug("MQTT value parse error for %s: %s", tag.source_ref, e)

        return readings

    async def browse(self, path: str = "") -> list[dict[str, Any]]:
        # MQTT has no browse — return configured topics
        return [
            {"node_id": t.source_ref, "name": t.source_ref,
             "has_children": False, "depth": 0, "type": "topic"}
            for t in self.tags
        ]
