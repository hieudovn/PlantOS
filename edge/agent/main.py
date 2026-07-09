#!/usr/bin/env python3
"""PlantOS Edge Agent — collector -> DuckDB buffer -> MQTT publish -> sync."""

import argparse
import asyncio
import logging
import math
import random
import yaml
from datetime import datetime, timezone
from pathlib import Path

from buffer import DuckDBBuffer
from publisher import MQTTPublisher
from sync import StoreAndForward
from health import HealthReporter
from metadata import MetadataManager
from web import setup as web_setup, run_server, set_modbus_collector, set_opcua_collector, set_metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("edge-agent")


class SignalGenerator:
    """Simple signal generator (same pattern as simulator)."""

    def __init__(self, cfg: dict):
        self.signal_id = cfg["signal_id"]
        self.v_min = cfg.get("min", 0)
        self.v_max = cfg.get("max", 100)
        self.noise = cfg.get("noise", 0.1)
        self.pattern = cfg.get("pattern", "sine")
        self._phase = random.uniform(0, 2 * math.pi)
        self._value = random.uniform(self.v_min, self.v_max)

    def update(self, dt: float) -> float:
        mid = (self.v_min + self.v_max) / 2
        amp = (self.v_max - self.v_min) / 2
        if self.pattern == "sine":
            self._phase += dt * 0.1
            self._value = mid + amp * math.sin(self._phase)
        elif self.pattern == "random_walk":
            self._value += random.gauss(0, self.noise * dt)
            self._value = max(self.v_min, min(self.v_max, self._value))
        self._value += random.gauss(0, self.noise)
        return round(self._value, 3)


class EdgeAgent:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)

        self.node_id = self.cfg["edge_node_id"]
        self.interval = self.cfg["publish"]["interval_seconds"]
        self.batch_size = self.cfg["publish"]["batch_size"]

        # DuckDB buffer
        self.buffer = DuckDBBuffer(
            path=self.cfg["buffer"]["path"],
            retention_days=self.cfg["buffer"]["retention_days"],
        )

        # MQTT publisher
        mqtt_cfg = self.cfg["mqtt"]
        self.mqtt = MQTTPublisher(mqtt_cfg["host"], mqtt_cfg["port"], mqtt_cfg["topic_prefix"], self.node_id)

        # Store-and-forward
        self.sync = StoreAndForward(
            self.buffer, self.cfg["http"]["ingest_url"], self.node_id,
            api_key=self.cfg.get("api_key", ""),
        )

        # Health reporter
        self.health = HealthReporter(
            self.cfg["heartbeat"]["url"], self.node_id, self.cfg["heartbeat"]["interval_seconds"],
            api_key=self.cfg.get("api_key", ""),
        )

        # Signal generators
        self.generators = [SignalGenerator(s) for s in self.cfg["signals"]]

        # Setup web server
        web_setup(self.buffer, self.mqtt, self.sync, self.cfg)

        # Metadata sync
        self.metadata = MetadataManager(self.cfg.get("center_url", "http://localhost:8000"))
        set_metadata(self.metadata)

        # Modbus collector
        from collectors.modbus.collector import ModbusCollector
        modbus_cfg = self.cfg.get("modbus", {})
        self.modbus = ModbusCollector(modbus_cfg, self.buffer)
        set_modbus_collector(self.modbus)

        # OPC UA collector (for Virtual Factory integration)
        from collectors.opcua import OpcUaCollector
        opcua_cfg = self.cfg.get("opcua", {})
        self.opcua_collector = OpcUaCollector(opcua_cfg, self.buffer)
        set_opcua_collector(self.opcua_collector)

        logger.info(f"Agent {self.node_id} started with {len(self.generators)} signals")

    async def run(self):
        # Sync metadata on startup (try Center first, fallback to cache)
        ok = await self.metadata.sync()
        if not ok:
            logger.warning("Center unreachable, loading cached metadata")
            self.metadata.load_cache()

        # Start web server as background task
        asyncio.create_task(run_server(port=8001))

        asyncio.create_task(self.health.run(lambda: self.sync.get_backlog()))
        asyncio.create_task(self._periodic_metadata_sync())
        asyncio.create_task(self.modbus.start())
        asyncio.create_task(self.opcua_collector.start())

        while True:
            # Generate measurements
            now = datetime.now(timezone.utc)
            measurements = []
            for gen in self.generators:
                val = gen.update(self.interval)
                measurements.append({
                    "timestamp": now.isoformat(),
                    "signal_id": gen.signal_id,
                    "value": val,
                    "quality": "SIMULATED",
                    "source": self.node_id,
                })

            # Write to DuckDB
            self.buffer.write(measurements)

            # Publish via MQTT
            self.mqtt.publish_measurements(measurements)

            # Sync backlog to Center via HTTP
            await self.sync.flush(self.batch_size)

            # Periodic retention cleanup (every 100 cycles ~ 100s)
            if random.randint(0, 99) == 0:
                self.buffer.cleanup_retention()

            await asyncio.sleep(self.interval)

    async def _periodic_metadata_sync(self):
        """Refresh metadata from Center every 5 minutes."""
        while True:
            await asyncio.sleep(300)
            await self.metadata.sync()


    def get_opcua_status(self) -> dict:
        if not hasattr(self, 'opcua_collector'):
            return {"enabled": False}
        return {
            "enabled": self.opcua_collector._enabled,
            "connected": self.opcua_collector.connected,
            "endpoint": self.opcua_collector.config.get("endpoint", ""),
            "signal_count": len(self.opcua_collector.mapper.node_ids),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PlantOS Edge Agent")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    agent = EdgeAgent(args.config)
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Agent stopped")
