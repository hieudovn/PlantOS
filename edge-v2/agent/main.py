#!/usr/bin/env python3
"""PlantOS Edge v2 — EdgeAgentV2 clean skeleton.

Clean-skeleton Edge Agent. Selectively reuses Edge v1 libraries (DuckDB buffer,
store-and-forward sync, health reporter, MQTT publisher) via `from edge.agent.*`.
All new code (config, auth, connectors, processing, commands, web) is built from
scratch in `edge-v2/agent/`.

IMPORTANT: This file uses sys.path manipulation to resolve imports.
Run from repo root with:
    PYTHONPATH=$(pwd) python edge-v2/agent/main.py
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# -- Path setup ------------------------------------------------------------
# Add repo root and edge-v2/ to sys.path so that both
# `from edge.agent.*` (v1 reuse) and `from agent.*` (v2) resolve.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_EDGE_V2_ROOT = _REPO_ROOT / "edge-v2"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_EDGE_V2_ROOT) not in sys.path:
    sys.path.insert(0, str(_EDGE_V2_ROOT))

# -- Selective reuse of Edge v1 libraries ---------------------------------
# These import from edge/agent/ (v1 stable baseline).
try:
    from edge.agent.buffer import DuckDBBuffer
    from edge.agent.sync import StoreAndForward
    from edge.agent.health import HealthReporter
    from edge.agent.publisher import MQTTPublisher
except ImportError as e:
    print(f"ERROR: Cannot import Edge v1 library: {e}", file=sys.stderr)
    print("Ensure repo root is on PYTHONPATH, e.g.:", file=sys.stderr)
    print("  PYTHONPATH=$(pwd) python edge-v2/agent/main.py", file=sys.stderr)
    sys.exit(1)

# -- Edge v2 modules (clean skeleton, built from scratch) -----------------
from agent.config import ConfigManager
from agent.auth import LocalAuthManager
from agent.connectors import ConnectorRegistry
from agent.processing import ProcessingEngine
from agent.commands import CommandPoller
from agent.web import WebServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
logger = logging.getLogger("edge-v2-agent")


class EdgeAgentV2:
    """Clean-skeleton Edge Agent.

    Selectively reuses Edge v1 libraries where appropriate. Builds new
    Productization Layer (auth, config ownership, connectors, processing,
    commands, web) from scratch. No global module variables.
    All dependencies injected via constructor.
    """

    def __init__(self, config_path: str):
        # Config — new, ownership model added in later phases
        self.config = ConfigManager(config_path)

        # Auth — bcrypt hashing, signed sessions, CSRF protection
        self.auth = LocalAuthManager(self.config)

        # Buffer — reused from edge.agent.buffer
        self.buffer = DuckDBBuffer(
            path=self.config.db_path,
            retention_days=self.config.buffer_retention_days,
        )

        # MQTT publisher — reused from edge.agent.publisher
        self.mqtt = MQTTPublisher(
            host=self.config.mqtt_host,
            port=self.config.mqtt_port,
            topic_prefix=self.config.mqtt_topic_prefix,
            edge_node_id=self.config.edge_node_id,
        )

        # Store-and-forward sync — reused from edge.agent.sync
        self.sync = StoreAndForward(
            buffer=self.buffer,
            ingest_url=self.config.center_ingest_url,
            edge_node_id=self.config.edge_node_id,
            api_key=self.config.api_key,
        )

        # Health reporter — reused from edge.agent.health
        self.health = HealthReporter(
            heartbeat_url=self.config.heartbeat_url,
            edge_node_id=self.config.edge_node_id,
            interval=self.config.heartbeat_interval,
            api_key=self.config.api_key,
        )

        # Connectors — OPC UA, Modbus TCP, MQTT Subscribe via safe apply
        self.connectors = ConnectorRegistry(self.config)

        # Processing engine — new, stub for now, full implementation in E2V2-3
        self.processing = ProcessingEngine()

        # Command poller — new, stub for now, full implementation in E2V2-4
        self.commands = CommandPoller(self.config)

        # Web server — aiohttp, auth middleware, static files
        self.web = WebServer(
            config=self.config,
            auth=self.auth,
            buffer=self.buffer,
            connectors=self.connectors,
            processing=self.processing,
            sync=self.sync,
            health=self.health,
        )

        self._running = False

    async def run(self):
        """Start the Edge v2 agent main loop."""
        logger.info("EdgeAgentV2 starting — node=%s plant=%s",
                     self.config.edge_node_id, self.config.plant_id)
        self._running = True

        # Start web server
        await self.web.start()

        # Start connectors
        await self.connectors.start_all()

        # Periodic tasks: heartbeat, sync, command poll
        async def heartbeat_loop():
            while self._running:
                backlog = self.sync.get_backlog()
                await self.health.send_heartbeat("online", backlog)
                await asyncio.sleep(self.config.heartbeat_interval)

        async def sync_loop():
            while self._running:
                await self.sync.flush(batch_size=self.config.batch_size)
                await asyncio.sleep(self.config.publish_interval)

        async def command_poll_loop():
            while self._running:
                await self.commands.poll()
                await asyncio.sleep(30)

        await asyncio.gather(
            heartbeat_loop(),
            sync_loop(),
            command_poll_loop(),
        )

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("EdgeAgentV2 shutting down")
        self._running = False
        await self.connectors.stop_all()
        await self.web.stop()


def main():
    parser = argparse.ArgumentParser(description="PlantOS Edge v2 Agent")
    parser.add_argument(
        "--config",
        default=os.environ.get("EDGE_CONFIG_PATH", "edge-v2/agent/config/config.edge-v2.yaml"),
        help="Path to config YAML (default from EDGE_CONFIG_PATH env or edge-v2/agent/config/config.edge-v2.yaml)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        # Also try relative to repo root
        alt = Path(__file__).resolve().parent.parent.parent / args.config
        if alt.exists():
            config_path = alt
        else:
            print(f"Config not found: {args.config}", file=sys.stderr)
            sys.exit(1)

    agent = EdgeAgentV2(str(config_path))

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        asyncio.run(agent.shutdown())


if __name__ == "__main__":
    main()
