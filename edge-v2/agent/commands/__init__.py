"""Command Poller — stub for E2V2-0.

Full pull-based command execution added in E2V2-4.
"""

import logging

logger = logging.getLogger(__name__)


class CommandPoller:
    """Stub command poller. No-op until E2V2-4."""

    def __init__(self, config):
        self.config = config

    async def poll(self):
        pass
