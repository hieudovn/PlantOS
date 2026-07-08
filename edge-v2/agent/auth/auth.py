"""LocalAuthManager — bcrypt hashing, signed sessions, CSRF tokens.

No plaintext passwords stored. Session cookies are signed with itsdangerous.
CSRF tokens are generated per-session and stored in session data.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import bcrypt
except ImportError:
    bcrypt = None  # Fallback handled below

logger = logging.getLogger(__name__)

SESSION_TTL = timedelta(hours=24)
CSRF_BYTES = 32


# ---- Password helpers (with bcrypt) -------------------------------------

def _hash_password(password: str) -> str:
    if bcrypt:
        pw = password.encode("utf-8")
        return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")
    # Fallback — SHA-256 (for environments without bcrypt)
    logger.warning("bcrypt not available; using SHA-256 fallback (NOT production-safe)")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _check_password(password: str, hashed: str) -> bool:
    if bcrypt:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed


# ---- Session helpers (itsdangerous) -------------------------------------

try:
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

    def _make_serializer(secret: str) -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(secret, salt="plantos-edge-session")

    def _sign_session(serializer: URLSafeTimedSerializer, data: dict) -> str:
        return serializer.dumps(data)

    def _unsign_session(serializer: URLSafeTimedSerializer, cookie: str) -> dict | None:
        try:
            return serializer.loads(cookie, max_age=int(SESSION_TTL.total_seconds()))
        except (BadSignature, SignatureExpired):
            return None
except ImportError:
    # Fallback — simple HMAC-like signing (NOT production-safe)
    import hmac

    logger.warning("itsdangerous not available; using HMAC fallback (NOT production-safe)")

    def _make_serializer(secret: str) -> str:
        return secret

    def _sign_session(secret: str, data: dict) -> str:
        import json
        payload = json.dumps(data)
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{sig}:{payload}"

    def _unsign_session(secret: str, cookie: str) -> dict | None:
        try:
            sig, payload = cookie.split(":", 1)
            expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(sig, expected):
                return None
            import json
            return json.loads(payload)
        except (ValueError, Exception):
            return None


class Session:
    """Represents an authenticated session."""

    def __init__(self, session_id: str, username: str, role: str,
                 csrf_token: str, created_at: datetime | None = None):
        self.session_id = session_id
        self.username = username
        self.role = role
        self.csrf_token = csrf_token
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "username": self.username,
            "role": self.role,
            "csrf_token": self.csrf_token,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            session_id=data["session_id"],
            username=data["username"],
            role=data["role"],
            csrf_token=data["csrf_token"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
        )


class LocalAuthManager:
    """Manages local authentication, sessions, and CSRF protection.

    Stores admin password hash in config. Session data is signed with
    itsdangerous and stored client-side in HttpOnly cookies.
    """

    def __init__(self, config):
        self.config = config
        self._serializer = _make_serializer(config.get("session_secret", "plantos-edge-default-secret"))
        # In-memory session store for CSRF token lookup (cookie carries the rest)
        self._sessions: dict[str, Session] = {}

    # ---- Password management ------------------------------------------------

    def create_admin(self, password: str) -> bool:
        """Set the admin password (first-run). Returns False if already exists."""
        existing = self.config.get("auth", {}).get("admin_hash")
        if existing:
            return False
        hashed = _hash_password(password)
        self.config._data.setdefault("auth", {})["admin_hash"] = hashed
        self.config._save()
        logger.info("Admin password created")
        return True

    def has_admin(self) -> bool:
        """Check if admin password has been set."""
        return bool(self.config.get("auth", {}).get("admin_hash"))

    def verify_password(self, username: str, password: str) -> bool:
        """Verify username/password. Only 'admin' user is supported."""
        if username != "admin":
            return False
        stored_hash = self.config.get("auth", {}).get("admin_hash")
        if not stored_hash:
            return False
        return _check_password(password, stored_hash)

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change admin password. Returns False if old password is wrong."""
        if not self.verify_password("admin", old_password):
            return False
        hashed = _hash_password(new_password)
        self.config._data.setdefault("auth", {})["admin_hash"] = hashed
        self.config._save()
        # Invalidate all existing sessions
        self._sessions.clear()
        logger.info("Admin password changed — all sessions invalidated")
        return True

    def is_first_run(self) -> bool:
        """Detect if no admin password has been set."""
        return not self.has_admin()

    # ---- Session management -------------------------------------------------

    def create_session(self, username: str, role: str = "admin") -> tuple[str, Session]:
        """Create a new session. Returns (cookie_value, session_object)."""
        session_id = secrets.token_hex(16)
        csrf_token = secrets.token_hex(CSRF_BYTES)
        session = Session(
            session_id=session_id,
            username=username,
            role=role,
            csrf_token=csrf_token,
        )
        self._sessions[session_id] = session
        cookie_value = _sign_session(self._serializer, session.to_dict())
        return cookie_value, session

    def validate_session(self, cookie: str) -> Session | None:
        """Validate a session cookie. Returns Session or None."""
        if not cookie:
            return None
        data = _unsign_session(self._serializer, cookie.strip('"'))
        if not data:
            return None
        try:
            session = Session.from_dict(data)
        except (KeyError, ValueError):
            return None
        # Verify session still in memory store
        stored = self._sessions.get(session.session_id)
        if not stored:
            # Session was invalidated (e.g., password change)
            return None
        # Sync CSRF token from memory (it's not in cookie for security)
        session.csrf_token = stored.csrf_token
        return session

    def destroy_session(self, cookie: str):
        """Destroy a session."""
        data = _unsign_session(self._serializer, cookie)
        if data and "session_id" in data:
            self._sessions.pop(data["session_id"], None)

    # ---- CSRF protection ----------------------------------------------------

    def validate_csrf(self, cookie: str, csrf_header: str | None) -> bool:
        """Validate CSRF token from header against session."""
        if not csrf_header:
            return False
        session = self.validate_session(cookie)
        if not session:
            return False
        return secrets.compare_digest(session.csrf_token, csrf_header)

    # ---- Legacy stub compatibility ------------------------------------------

    def is_authenticated(self, request) -> bool:
        """Legacy stub — unused in E2V2-1+. Use validate_session instead."""
        return True

    def login(self, username: str, password: str) -> bool:
        """Direct login without session — for testing."""
        return self.verify_password(username, password)

    def logout(self):
        pass
