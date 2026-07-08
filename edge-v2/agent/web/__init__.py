"""Web Server — stub for E2V2-0.

Full aiohttp server with Local Console UI added in E2V2-1.
"""

import logging

logger = logging.getLogger(__name__)


class WebServer:
    """Stub web server. No-op until E2V2-1."""

    def __init__(self, config=None, auth=None, buffer=None,
                 connectors=None, processing=None, sync=None):
        self.config = config
        self.auth = auth
        self.buffer = buffer
        self.connectors = connectors
        self.processing = processing
        self.sync = sync

    async def start(self):
        pass

    async def stop(self):
        pass
