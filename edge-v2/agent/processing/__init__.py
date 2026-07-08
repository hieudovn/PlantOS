"""Processing Engine — stub for E2V2-0.

Full pipeline with 7 MVP steps added in E2V2-3.
"""

import logging

logger = logging.getLogger(__name__)


class ProcessingEngine:
    """Stub processing engine. No-op until E2V2-3."""

    def __init__(self):
        self._profiles: dict[str, dict] = {}
