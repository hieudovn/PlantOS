"""LocalUserStore — local cache of users synced from Center.

Stores user credentials locally so Edge can authenticate offline.
Format (YAML in config file):
  auth:
    users:
      admin:
        password_hash: $2b$12$...
        display_name: Administrator
        role: admin
        synced_at: "2026-07-13T00:00:00Z"
      engineer:
        password_hash: $2b$12$...
        display_name: Engineer
        role: engineer
        synced_at: "2026-07-13T00:00:00Z"
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class UserInfo:
    """Represents a cached user."""
    def __init__(self, username: str, password_hash: str, display_name: str,
                 role: str, is_active: bool = True,
                 synced_at: datetime | None = None):
        self.username = username
        self.password_hash = password_hash
        self.display_name = display_name
        self.role = role
        self.is_active = is_active
        self.synced_at = synced_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "password_hash": self.password_hash,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "synced_at": self.synced_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, username: str, data: dict) -> "UserInfo":
        synced = data.get("synced_at")
        if synced:
            synced = datetime.fromisoformat(synced)
        return cls(
            username=username,
            password_hash=data["password_hash"],
            display_name=data.get("display_name", username),
            role=data.get("role", "operator"),
            is_active=data.get("is_active", True),
            synced_at=synced,
        )


class LocalUserStore:
    """Local cache of authorized users, synced from Center."""

    def __init__(self, config):
        self.config = config
        self._users: dict[str, UserInfo] = {}
        self._load()

    def _load(self):
        """Load users from config."""
        auth_section = self.config.get("auth", {})
        if not isinstance(auth_section, dict):
            auth_section = {}
        users_dict = auth_section.get("users", {})
        if not isinstance(users_dict, dict):
            users_dict = {}
        self._users = {}
        for username, data in users_dict.items():
            try:
                self._users[username] = UserInfo.from_dict(username, data)
            except Exception as e:
                logger.warning("Failed to load user %s: %s", username, e)

    def _save(self):
        """Save users to config."""
        data = {}
        for username, user in self._users.items():
            data[username] = user.to_dict()
        self.config._data.setdefault("auth", {})["users"] = data
        self.config._save()
        logger.info("Saved %d users to local config", len(self._users))

    # ---- Migration: convert legacy admin_hash to users dict ----

    def migrate_legacy_admin(self) -> bool:
        """If legacy admin_hash exists, migrate to users dict. Returns True if migrated."""
        legacy_hash = self.config.get("auth", {}).get("admin_hash")
        if not legacy_hash:
            return False
        if self._users:
            return False  # already migrated

        self._users["admin"] = UserInfo(
            username="admin",
            password_hash=legacy_hash,
            display_name="Administrator",
            role="admin",
        )
        # Remove legacy key
        if "admin_hash" in self.config._data.get("auth", {}):
            del self.config._data["auth"]["admin_hash"]
        self._save()
        logger.info("Migrated legacy admin_hash to users dict")
        return True

    # ---- CRUD ----

    def get_user(self, username: str) -> UserInfo | None:
        return self._users.get(username)

    def list_users(self) -> list[UserInfo]:
        return list(self._users.values())

    def upsert_user(self, user: UserInfo):
        self._users[user.username] = user
        self._save()

    def delete_user(self, username: str) -> bool:
        if username not in self._users:
            return False
        del self._users[username]
        self._save()
        return True

    # ---- Sync ----

    def sync_from_center(self, center_users: list[dict]):
        """Replace local user list with Center data. Called on push or pull."""
        now = datetime.now(timezone.utc)
        new_users: dict[str, UserInfo] = {}
        for u in center_users:
            username = u["username"]
            new_users[username] = UserInfo(
                username=username,
                password_hash=u["password_hash"],
                display_name=u.get("display_name", username),
                role=u.get("role", "operator"),
                is_active=u.get("is_active", True),
                synced_at=now,
            )
        self._users = new_users
        self._save()
        logger.info("Synced %d users from Center", len(self._users))

    def get_sync_timestamp(self) -> str | None:
        """Get timestamp of last sync for incremental pull."""
        if not self._users:
            return None
        latest = max((u.synced_at for u in self._users.values()),
                     default=None)
        return latest.isoformat() if latest else None

    def __len__(self):
        return len(self._users)
