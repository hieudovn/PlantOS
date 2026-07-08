"""OPC UA client wrapper — handles connection, reads, browse."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from asyncua import Client as OpcUaAsyncClient, ua
    HAS_OPCUA = True
except ImportError:
    HAS_OPCUA = False


class OpcUaClient:
    """Wraps asyncua Client with reconnection, timeout, and browse support."""

    def __init__(self, endpoint: str, timeout: float = 5.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self._client: OpcUaAsyncClient | None = None
        self.is_connected = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0

    async def connect(self) -> bool:
        if not HAS_OPCUA:
            logger.warning("asyncua not installed — OPC UA unavailable")
            return False
        try:
            self._client = OpcUaAsyncClient(self.endpoint, timeout=self.timeout)
            await self._client.connect()
            self.is_connected = True
            self._reconnect_delay = 1.0
            logger.info("OPC UA connected to %s", self.endpoint)
            return True
        except Exception as e:
            self.is_connected = False
            logger.warning("OPC UA connect failed: %s", e)
            return False

    async def disconnect(self):
        if self._client and self.is_connected:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self.is_connected = False
            self._client = None

    async def read_values(self, node_ids: list[str]) -> list[dict[str, Any]]:
        """Read values for a list of NodeIds. Returns [{node_id, value, quality}]."""
        if not self.is_connected or not self._client:
            return []
        results = []
        for node_id in node_ids:
            try:
                node = self._client.get_node(node_id)
                val = await node.read_value()
                dv = await node.read_data_value()
                quality = "GOOD"
                if dv.StatusCode and dv.StatusCode.is_bad:
                    quality = "BAD"
                elif dv.StatusCode and dv.StatusCode.is_uncertain:
                    quality = "UNCERTAIN"
                results.append({
                    "node_id": node_id,
                    "value": float(val) if val is not None else 0.0,
                    "quality": quality,
                })
            except Exception as e:
                logger.debug("OPC UA read %s failed: %s", node_id, e)
                results.append({"node_id": node_id, "value": 0.0, "quality": "BAD"})
        return results

    async def browse(self, node_id: str = "i=84", namespace_filter: int = -1,
                     max_depth: int = 3) -> list[dict[str, Any]]:
        """Browse OPC UA address space. Returns [{node_id, name, type, has_children}]."""
        if not self.is_connected or not self._client:
            return []
        results = []

        async def _browse(current_id: str, depth: int = 0):
            if depth > max_depth:
                return
            try:
                node = self._client.get_node(current_id)
                children = await node.get_children()
                for child in children:
                    try:
                        browse_name = await child.read_browse_name()
                        node_id_str = child.nodeid.to_string()
                        name = browse_name.Name
                        if namespace_filter >= 0 and child.nodeid.NamespaceIndex != namespace_filter:
                            continue
                        child_children = await child.get_children()
                        has_children = len(child_children) > 0
                        results.append({
                            "node_id": node_id_str,
                            "name": name,
                            "has_children": has_children,
                            "depth": depth,
                        })
                        if has_children:
                            await _browse(node_id_str, depth + 1)
                    except Exception:
                        continue
            except Exception:
                pass

        await _browse(node_id)
        return results

    async def reconnect(self):
        """Attempt reconnection with exponential backoff."""
        while not self.is_connected:
            logger.info("OPC UA reconnecting in %.0fs...", self._reconnect_delay)
            await asyncio.sleep(self._reconnect_delay)
            if await self.connect():
                return
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
