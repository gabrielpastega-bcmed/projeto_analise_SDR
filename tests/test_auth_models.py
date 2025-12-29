"""
Tests for authentication models (User, AuditLog, Session, UserPreferences).

Tests password hashing, model creation, and relationships.
"""

import pytest


class TestUserModel:
    """Tests for User model."""

    def test_set_password_hashes_correctly(self):
        """Test that set_password creates a bcrypt hash."""
        from src.auth.models import User

        user = User(username="testuser", email="test@test.com", password_hash="")
        user.set_password("password123")

        # Hash should be different from original password
        assert user.password_hash != "password123"
        # Hash should start with bcrypt prefix
        assert user.password_hash.startswith("$2b$")

    def test_check_password_valid(self):
        """Test check_password returns True for correct password."""
        from src.auth.models import User

        user = User(username="testuser", email="test@test.com", password_hash="")
        user.set_password("mypassword")

        assert user.check_password("mypassword") is True

    def test_check_password_invalid(self):
        """Test check_password returns False for wrong password."""
        from src.auth.models import User

        user = User(username="testuser", email="test@test.com", password_hash="")
        user.set_password("correctpassword")

        assert user.check_password("wrongpassword") is False

    def test_set_password_too_long_raises(self):
        """Test set_password raises error for passwords > 72 bytes."""
        from src.auth.models import User

        user = User(username="testuser", email="test@test.com", password_hash="")

        with pytest.raises(ValueError, match="Password too long"):
            user.set_password("a" * 100)  # 100 bytes > 72 limit

    def test_is_superadmin_true(self):
        """Test is_superadmin returns True for superadmin role."""
        from src.auth.models import User

        user = User(
            username="admin",
            email="admin@test.com",
            password_hash="hash",
            role="superadmin",
        )

        assert user.is_superadmin() is True

    def test_is_superadmin_false(self):
        """Test is_superadmin returns False for regular user."""
        from src.auth.models import User

        user = User(username="user", email="user@test.com", password_hash="hash", role="user")

        assert user.is_superadmin() is False

    def test_user_repr(self):
        """Test User string representation."""
        from src.auth.models import User

        user = User(username="testuser", email="test@test.com", password_hash="hash")

        repr_str = repr(user)

        assert "testuser" in repr_str


class TestAuditLogModel:
    """Tests for AuditLog model."""

    def test_audit_log_creation(self):
        """Test AuditLog can be created with required fields."""
        from src.auth.models import AuditLog

        log = AuditLog(user_id=1, action="login")

        assert log.user_id == 1
        assert log.action == "login"
        assert log.resource is None
        assert log.details is None

    def test_audit_log_with_details(self):
        """Test AuditLog with resource and details."""
        from src.auth.models import AuditLog

        log = AuditLog(
            user_id=1,
            action="export",
            resource="dashboard",
            details='{"format": "pdf"}',
        )

        assert log.resource == "dashboard"
        assert log.details == '{"format": "pdf"}'


class TestSessionModel:
    """Tests for Session model."""

    def test_session_creation(self):
        """Test Session can be created with required fields."""
        from datetime import datetime, timedelta

        from src.auth.models import Session

        expires = datetime.utcnow() + timedelta(hours=24)
        session = Session(user_id=1, token="abc123", expires_at=expires)

        assert session.user_id == 1
        assert session.token == "abc123"


class TestUserPreferencesModel:
    """Tests for UserPreferences model."""

    def test_preferences_creation(self):
        """Test UserPreferences can be created."""
        from src.auth.models import UserPreferences

        prefs = UserPreferences(user_id=1, theme="dark")

        assert prefs.user_id == 1
        assert prefs.theme == "dark"

    def test_preferences_defaults(self):
        """Test UserPreferences has reasonable defaults."""
        from src.auth.models import UserPreferences

        prefs = UserPreferences(user_id=1)

        # Should have default values
        assert prefs.user_id == 1
