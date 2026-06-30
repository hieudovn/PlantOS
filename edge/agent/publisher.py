"""MQTT publisher — sends measurements to EMQX per UNS topic."""

import json
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTPublisher:
    def __init__(self, host: str, port: int, topic_prefix: str, edge_node_id: str):
        self.topic_prefix = topic_prefix
        self.edge_node_id = edge_node_id
        self.client = mqtt.Client(client_id=edge_node_id)
        self.client.on_connect = self._on_connect
        self.connected = False

        try:
            self.client.connect(host, port, keepalive=30)
            self.client.loop_start()
            logger.info(f"MQTT connecting to {host}:{port}")
        except Exception as e:
            logger.warning(f"MQTT connect failed: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = rc == 0
        if self.connected:
            logger.info("MQTT connected")
        else:
            logger.warning(f"MQTT connection failed: rc={rc}")

    def publish_measurements(self, measurements: list[dict]):
        """Publish batch to MQTT. Topic: {prefix}/{signal_id}"""
        if not self.connected:
            return False

        for m in measurements:
            topic = f"{self.topic_prefix}/{m['signal_id'].replace('.', '/')}"
            payload = json.dumps({
                "timestamp": m["timestamp"],
                "value": m["value"],
                "quality": m.get("quality", "GOOD"),
                "source": self.edge_node_id,
            })
            self.client.publish(topic, payload, qos=1)

        return True

    def is_connected(self) -> bool:
        return self.connected

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
