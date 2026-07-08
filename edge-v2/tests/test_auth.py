"""Tests for LocalAuthManager — password hashing, sessions, CSRF."""

import pytest
from unittest.mock import MagicMock


class TestPasswordHashing:
    """Verify bcrypt password hashing and verification."""

    @pytest.fixture
    def config(self):
        cfg = MagicMock()
        cfg.get.return_value = None
        cfg._data = {}
        cfg._save = MagicMock()
        return cfg

    @pytest.fixture
    def auth(self, config):
        from agent.auth.auth import LocalAuthManager
        return LocalAuthManager(config)

    def test_create_admin(self, auth):
        """First-run admin creation should succeed."""
        result = auth.create_admin("test-password-123")
        assert result is True
        assert auth.has_admin() is True

    def test_create_admin_twice_fails(self, auth):
        """Creating admin twice should return False."""
        auth.create_admin("test-password-123")
        result = auth.create_admin("another-password")
        assert result is False

    def test_verify_correct_password(self, auth):
        """Correct password should verify."""
        auth.create_admin("test-password-123")
        assert auth.verify_password("admin", "test-password-123") is True

    def test_verify_wrong_password(self, auth):
        """Wrong password should not verify."""
        auth.create_admin("test-password-123")
        assert auth.verify_password("admin", "wrong-password") is False

    def test_verify_wrong_username(self, auth):
        """Wrong username should not verify."""
        auth.create_admin("test-password-123")
        assert auth.verify_password("not-admin", "test-password-123") is False

    def test_verify_no_admin_set(self, auth):
        """Should return False if no admin password set."""
        assert auth.verify_password("admin", "anything") is False

    def test_is_first_run_true(self, auth):
        """Should return True when no admin set."""
        assert auth.is_first_run() is True

    def test_is_first_run_false(self, auth):
        """Should return False after admin created."""
        auth.create_admin("test-password-123")
        assert auth.is_first_run() is False

    def test_change_password(self, auth):
        """Should change password and invalidate sessions."""
        auth.create_admin("old-password")
        result = auth.change_password("old-password", "new-password")
        assert result is True
        assert auth.verify_password("admin", "new-password") is True
        assert auth.verify_password("admin", "old-password") is False

    def test_change_password_wrong_old(self, auth):
        """Should return False if old password is wrong."""
        auth.create_admin("correct-password")
        result = auth.change_password("wrong-password", "new-password")
        assert result is False


class TestSessionManagement:
    """Verify session creation, validation, and destruction."""

    @pytest.fixture
    def auth(self):
        from agent.auth.auth import LocalAuthManager
        cfg = MagicMock()
        cfg.get.return_value = "test-secret-key-for-sessions"
        cfg._data = {}
        cfg._save = MagicMock()
        mgr = LocalAuthManager(cfg)
        mgr.create_admin("test-password")
        return mgr

    def test_create_session(self, auth):
        """Creating a session should return cookie and session object."""
        cookie, session = auth.create_session("admin", role="admin")
        assert cookie is not None
        assert len(cookie) > 0
        assert session.username == "admin"
        assert session.role == "admin"
        assert session.session_id is not None

    def test_validate_valid_session(self, auth):
        """A valid session should validate successfully."""
        cookie, _ = auth.create_session("admin", role="admin")
        session = auth.validate_session(cookie)
        assert session is not None
        assert session.username == "admin"
        assert session.role == "admin"

    def test_validate_invalid_session(self, auth):
        """An invalid cookie should return None."""
        session = auth.validate_session("invalid-cookie-value")
        assert session is None

    def test_validate_empty_session(self, auth):
        """An empty cookie should return None."""
        session = auth.validate_session("")
        assert session is None

    def test_destroy_session(self, auth):
        """After destroying a session, it should no longer validate."""
        cookie, _ = auth.create_session("admin", role="admin")
        auth.destroy_session(cookie)
        session = auth.validate_session(cookie)
        assert session is None

    def test_logout_invalidates(self, auth):
        """Logout should invalidate the session."""
        cookie, _ = auth.create_session("admin", role="admin")
        auth.destroy_session(cookie)
        assert auth.validate_session(cookie) is None

    def test_password_change_invalidates_sessions(self, auth):
        """Password change should invalidate all sessions."""
        cookie1, _ = auth.create_session("admin", role="admin")
        cookie2, _ = auth.create_session("admin", role="admin")
        auth.change_password("test-password", "new-password")
        assert auth.validate_session(cookie1) is None
        assert auth.validate_session(cookie2) is None

    def test_csrf_token_in_session(self, auth):
        """Session should have a CSRF token."""
        _, session = auth.create_session("admin", role="admin")
        assert session.csrf_token is not None
        assert len(session.csrf_token) > 0


class TestCSRFProtection:
    """Verify CSRF token validation."""

    @pytest.fixture
    def auth(self):
        from agent.auth.auth import LocalAuthManager
        cfg = MagicMock()
        cfg.get.return_value = "test-secret-key"
        cfg._data = {}
        cfg._save = MagicMock()
        mgr = LocalAuthManager(cfg)
        mgr.create_admin("test-password")
        return mgr

    def test_valid_csrf_token(self, auth):
        """A valid CSRF token should validate."""
        cookie, session = auth.create_session("admin", role="admin")
        assert auth.validate_csrf(cookie, session.csrf_token) is True

    def test_invalid_csrf_token(self, auth):
        """An invalid CSRF token should not validate."""
        cookie, _ = auth.create_session("admin", role="admin")
        assert auth.validate_csrf(cookie, "wrong-token") is False

    def test_empty_csrf_token(self, auth):
        """An empty CSRF token should not validate."""
        cookie, _ = auth.create_session("admin", role="admin")
        assert auth.validate_csrf(cookie, "") is False

    def test_csrf_without_session(self, auth):
        """CSRF check without valid session should fail."""
        assert auth.validate_csrf("invalid-cookie", "some-token") is False
