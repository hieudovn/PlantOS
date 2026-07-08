"""CommandPoller — polls Center for pending commands, executes allowed ones.

Pull-based: Edge polls Center every N seconds. No inbound connectivity needed.
Executes ONLY commands in ALLOWED_COMMANDS list.
Reports result back to Center after execution.
"""

import asyncio
import logging
import os
import sys
from typing import Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger(__name__)

# Commands allowed in E2V2-5 (restart_agent requires supervisor)
ALLOWED_COMMANDS = {
    "sync_now",
    "reload_config",
    "restart_connector",
    "enable_connector",
    "disable_connector",
    "restart_agent",
}

POLL_INTERVAL = 15  # seconds between polls


def _running_under_supervisor() -> bool:
    """Detect if running under Docker or systemd supervisor.

    Returns True if supervisor can restart the process after exit.
    """
    # Docker detection: check for /.dockerenv or /proc/1/cgroup
    if os.path.exists("/.dockerenv"):
        return True
    try:
        with open("/proc/1/cgroup") as f:
            content = f.read()
        if "docker" in content or "containerd" in content:
            return True
    except Exception:
        pass
    # systemd detection: check if our parent is systemd
    try:
        with open("/proc/1/comm") as f:
            parent_comm = f.read().strip()
        if parent_comm == "systemd":
            return True
    except Exception:
        pass
    return False

POLL_INTERVAL = 15  # seconds between polls


class CommandPoller:
    """Polls Center for pending commands and executes them locally.

    Constructor receives the EdgeAgentV2 instance to access its components.
    NO global module variables. All dependencies injected.
    """

    def __init__(self, config, edge_agent=None):
        self.config = config
        self.agent = edge_agent  # EdgeAgentV2 instance
        self._running = False

    async def poll(self):
        """Single poll cycle. Called periodically by main loop."""
        if not HAS_HTTPX:
            return

        center_url = self.config.center_url.rstrip("/")
        node_id = self.config.edge_node_id
        poll_url = f"{center_url}/api/v1/edge-nodes/{node_id}/commands/pending"
        headers = {}
        api_key = self.config.api_key
        if api_key:
            headers["X-API-Key"] = api_key

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(poll_url, headers=headers)
                if resp.status_code != 200:
                    return

                commands = resp.json()
                if not commands:
                    return

                logger.info("Received %d pending command(s)", len(commands))

                for cmd in commands:
                    await self._execute(cmd, client, headers)

        except Exception as e:
            logger.debug("Command poll error: %s", e)

    async def _execute(self, cmd: dict, client: httpx.AsyncClient, headers: dict):
        """Execute a single command and report result."""
        cmd_id = cmd.get("command_id", "")
        cmd_type = cmd.get("command_type", "")
        target = cmd.get("target")
        params = cmd.get("params", {})

        if cmd_type not in ALLOWED_COMMANDS:
            logger.warning("Command '%s' not in allowed list — skipping", cmd_type)
            await self._report(cmd_id, "failed", "Command not allowed", client, headers)
            return

        logger.info("Executing command: %s (target=%s)", cmd_type, target)

        try:
            if cmd_type == "sync_now":
                await self._handle_sync_now()
            elif cmd_type == "reload_config":
                await self._handle_reload_config()
            elif cmd_type == "restart_connector":
                await self._handle_restart_connector(target)
            elif cmd_type == "enable_connector":
                await self._handle_enable_connector(target)
            elif cmd_type == "disable_connector":
                await self._handle_disable_connector(target)
            elif cmd_type == "restart_agent":
                await self._handle_restart_agent(cmd_id, client, headers)
                return  # _handle_restart_agent reports + exits

            await self._report(cmd_id, "success", f"Command '{cmd_type}' executed", client, headers)

        except Exception as e:
            logger.exception("Command '%s' failed: %s", cmd_type, e)
            await self._report(cmd_id, "failed", str(e), client, headers)

    async def _report(self, cmd_id: str, status: str, message: str,
                       client: httpx.AsyncClient, headers: dict):
        """Report command execution result to Center."""
        center_url = self.config.center_url.rstrip("/")
        node_id = self.config.edge_node_id
        url = f"{center_url}/api/v1/edge-nodes/{node_id}/commands/{cmd_id}/result"
        try:
            await client.post(url, json={
                "status": status,
                "result_message": message,
            }, headers=headers)
        except Exception as e:
            logger.warning("Failed to report command result: %s", e)

    # ---- Command Handlers ---------------------------------------------------

    async def _handle_sync_now(self):
        """Trigger immediate sync flush."""
        if self.agent and hasattr(self.agent, "sync"):
            logger.info("Executing sync_now...")
            synced = await self.agent.sync.flush(batch_size=1000)
            logger.info("sync_now completed: %d measurements synced", synced)
        else:
            logger.warning("sync_now: no sync component available")

    async def _handle_reload_config(self):
        """Reload config from YAML, re-validate connectors."""
        if self.agent and hasattr(self.agent, "config"):
            logger.info("Executing reload_config...")
            self.agent.config._load()
            logger.info("Config reloaded successfully")
        else:
            logger.warning("reload_config: no config component available")

    async def _handle_restart_connector(self, connector_id: str | None):
        """Restart a specific connector."""
        if not connector_id:
            raise ValueError("restart_connector requires a connector_id target")
        if self.agent and hasattr(self.agent, "connectors"):
            connector = self.agent.connectors.get(connector_id)
            if not connector:
                raise ValueError(f"Connector '{connector_id}' not found")
            await connector.restart()
            logger.info("Connector '%s' restarted", connector_id)
        else:
            logger.warning("restart_connector: no connectors component available")

    async def _handle_enable_connector(self, connector_id: str | None):
        """Enable a disabled connector."""
        if not connector_id:
            raise ValueError("enable_connector requires a connector_id target")
        if self.agent and hasattr(self.agent, "connectors"):
            connector = self.agent.connectors.get(connector_id)
            if not connector:
                raise ValueError(f"Connector '{connector_id}' not found")
            connector.config["enabled"] = True
            await connector.start()
            logger.info("Connector '%s' enabled", connector_id)
        else:
            logger.warning("enable_connector: no connectors component available")

    async def _handle_disable_connector(self, connector_id: str | None):
        """Disable a running connector."""
        if not connector_id:
            raise ValueError("disable_connector requires a connector_id target")
        if self.agent and hasattr(self.agent, "connectors"):
            connector = self.agent.connectors.get(connector_id)
            if not connector:
                raise ValueError(f"Connector '{connector_id}' not found")
            connector.config["enabled"] = False
            await connector.stop()
            logger.info("Connector '%s' disabled", connector_id)
        else:
            logger.warning("disable_connector: no connectors component available")

    # ---- restart_agent (E2V2-5 — requires supervisor) -----------------------

    async def _handle_restart_agent(self, cmd_id: str,
                                     client: httpx.AsyncClient,
                                     headers: dict):
        """Restart the agent process via supervisor exit.

        1. Check supervisor is available
        2. Flush buffer (sync pending measurements)
        3. Stop all connectors gracefully
        4. Report success to Center
        5. Exit with code 0 → supervisor (Docker/systemd) brings process back
        """
        logger.info("Executing restart_agent...")

        if not _running_under_supervisor():
            await self._report(
                cmd_id, "failed",
                "restart_agent requires Docker or systemd supervisor. "
                "Start the agent with: docker compose up -d or systemctl start plantos-edge-v2",
                client, headers,
            )
            return

        # 1. Flush buffer
        if self.agent and hasattr(self.agent, "sync"):
            try:
                await self.agent.sync.flush(batch_size=1000)
                logger.info("restart_agent: buffer flushed")
            except Exception as e:
                logger.warning("restart_agent: flush error: %s", e)

        # 2. Stop connectors
        if self.agent and hasattr(self.agent, "connectors"):
            try:
                await self.agent.connectors.stop_all()
                logger.info("restart_agent: connectors stopped")
            except Exception as e:
                logger.warning("restart_agent: connector stop error: %s", e)

        # 3. Report success
        await self._report(
            cmd_id, "success",
            "Agent restarting — supervisor will bring process back",
            client, headers,
        )

        logger.info("restart_agent: exiting for supervisor restart")

        # 4. Exit — supervisor (Docker restart policy / systemd Restart=) brings back
        sys.exit(0)
