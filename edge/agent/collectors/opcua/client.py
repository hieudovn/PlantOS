"""OPC UA async client for reading industrial signals from Virtual Factory."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OpcUaClient:
    """Async OPC UA client that connects to a server and reads variable values."""

    def __init__(self, endpoint: str, timeout: float = 5.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self._client: Any = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    async def connect(self, retries: int = 10, delay_s: float = 2.0) -> bool:
        """Connect to OPC UA server with retry logic."""
        try:
            from asyncua import Client
        except ImportError:
            logger.error("asyncua not installed. Run: pip install asyncua")
            return False

        for attempt in range(1, retries + 1):
            try:
                self._client = Client(url=self.endpoint, timeout=self.timeout)
                await self._client.connect()
                self._connected = True
                logger.info(f"Connected to OPC UA server at {self.endpoint}")
                return True
            except Exception as e:
                logger.warning(f"OPC UA connect attempt {attempt}/{retries}: {e}")
                if self._client:
                    try:
                        await self._client.disconnect()
                    except Exception:
                        pass
                    self._client = None
                if attempt < retries:
                    await asyncio.sleep(delay_s)

        logger.error(f"Failed to connect to OPC UA server after {retries} attempts")
        return False

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
        self._connected = False

    async def read_value(self, node_id: str) -> Any | None:
        if not self.is_connected:
            return None
        try:
            node = self._client.get_node(node_id)
            return await node.read_value()
        except Exception as e:
            logger.error(f"Failed to read {node_id}: {e}")
            return None

    async def read_values(self, node_ids: list[str]) -> dict[str, Any]:
        if not self.is_connected:
            return {}
        results = {}
        for nid in node_ids:
            value = await self.read_value(nid)
            if value is not None:
                results[nid] = value
        return results
