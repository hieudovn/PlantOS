"""Local Auth Manager — stub for E2V2-0.

Full bcrypt hash + signed session cookie implementation added in E2V2-1.
"""

import logging

logger = logging.getLogger(__name__)


class LocalAuthManager:
    """Stub auth manager. No-op until E2V2-1."""

    def __init__(self, config):
        self.config = config

    def is_authenticated(self, request) -> bool:
        """Allow all requests in stub mode."""
        return True

    def login(self, username: str, password: str) -> bool:
        """Accept any credentials in stub mode."""
        return True

    def logout(self):
        pass
