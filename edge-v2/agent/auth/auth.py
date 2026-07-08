"""LocalAuthManager — bcrypt hashing, signed sessions, CSRF tokens.

No plaintext passwords stored. Session cookies are signed with itsdangerous.
CSRF tokens are generated per-session and stored in session data.

SECURITY: Fail fast if bcrypt or itsdangerous are missing (unless EDGE_DEV_INSECURE_AUTH=true).
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

try:
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    HAS_ITSDAENGEROUS = True
except ImportError:
    HAS_ITSDAENGEROUS = False

logger = logging.getLogger(__name__)

SESSION_TTL = timedelta(hours=24)
CSRF_BYTES = 32


# ---- Production safety check --------------------------------------------

def _check_crypto():
    """Fail fast if production crypto libs are missing, unless dev mode set."""
    dev_mode = os.environ.get("EDGE_DEV_INSECURE_AUTH", "").lower() in ("true", "1", "yes")
    if not HAS_BCRYPT:
        msg = "bcrypt required for production. Install: pip install bcrypt"
        if dev_mode:
            logger.warning("%s — running with INSECURE SHA-256 fallback", msg)
        else:
            raise RuntimeError(msg)
    if not HAS_ITSDAENGEROUS:
        msg = "itsdangerous required for production. Install: pip install itsdangerous"
        if dev_mode:
            logger.warning("%s — running with INSECURE HMAC fallback", msg)
        else:
            raise RuntimeError(msg)


# ---- Password helpers (with bcrypt) -------------------------------------

def _hash_password(password: str) -> str:
    if HAS_BCRYPT:
        pw = password.encode("utf-8")
        return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")
    logger.warning("Using INSECURE SHA-256 password hashing (EDGE_DEV_INSECURE_AUTH mode)")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _check_password(password: str, hashed: str) -> bool:
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed


# ---- Session helpers (itsdangerous) -------------------------------------

def _make_serializer(secret: str) -> URLSafeTimedSerializer | str:
    if HAS_ITSDAENGEROUS:
        return URLSafeTimedSerializer(secret, salt="plantos-edge-session")
    return secret


def _sign_session(serializer: URLSafeTimedSerializer | str, data: dict) -> str:
    if HAS_ITSDAENGEROUS:
        return serializer.dumps(data)
    import hmac, json
    payload = json.dumps(data)
    sig = hmac.new(serializer.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{sig}:{payload}"


def _unsign_session(serializer: URLSafeTimedSerializer | str, cookie: str) -> dict | None:
    if HAS_ITSDAENGEROUS:
        try:
            return serializer.loads(cookie, max_age=int(SESSION_TTL.total_seconds()))
        except (BadSignature, SignatureExpired):
            return None
    import hmac, json
    try:
        sig, payload = cookie.split(":", 1)
        expected = hmac.new(serializer.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return None
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
        # Fail fast if production crypto libs are missing
        _check_crypto()
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
