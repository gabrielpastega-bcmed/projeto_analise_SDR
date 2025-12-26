"""
Tests for AuthManager class and authentication functions.

Uses mocking to avoid database dependencies and Streamlit session state.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestLogAction:
    """Tests for log_action function."""

    @patch("src.auth.auth_manager.SessionLocal")
    def test_log_action_creates_entry(self, mock_session_local):
        """Test that log_action creates an AuditLog entry."""
        from src.auth.auth_manager import log_action

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        log_action(1, "test_action", "resource", {"key": "value"})

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.auth.auth_manager.SessionLocal")
    def test_log_action_without_details(self, mock_session_local):
        """Test log_action with no details."""
        from src.auth.auth_manager import log_action

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        log_action(1, "test_action")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestAuthManagerLogin:
    """Tests for AuthManager.login method."""

    @patch("src.auth.auth_manager.log_action")
    @patch("src.auth.auth_manager.SessionLocal")
    def test_login_valid_credentials(self, mock_session_local, mock_log_action):
        """Test login with valid username and password."""
        from src.auth.auth_manager import AuthManager

        # Setup mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.check_password.return_value = True

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_session_local.return_value = mock_db

        result = AuthManager.login("testuser", "password123")

        assert result == mock_user
        mock_user.check_password.assert_called_once_with("password123")
        mock_log_action.assert_called()

    @patch("src.auth.auth_manager.log_action")
    @patch("src.auth.auth_manager.SessionLocal")
    def test_login_invalid_password(self, mock_session_local, mock_log_action):
        """Test login with invalid password."""
        from src.auth.auth_manager import AuthManager

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.check_password.return_value = False

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_session_local.return_value = mock_db

        result = AuthManager.login("testuser", "wrongpassword")

        assert result is None

    @patch("src.auth.auth_manager.SessionLocal")
    def test_login_user_not_found(self, mock_session_local):
        """Test login with non-existent user."""
        from src.auth.auth_manager import AuthManager

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = AuthManager.login("nonexistent", "password")

        assert result is None


class TestAuthManagerLogout:
    """Tests for AuthManager.logout method."""

    @patch("src.auth.auth_manager.st")
    @patch("src.auth.auth_manager.log_action")
    def test_logout_clears_session(self, mock_log_action, mock_st):
        """Test that logout clears session state."""
        from src.auth.auth_manager import AuthManager

        # Setup mock session state as MagicMock
        mock_session = MagicMock()
        mock_session.user_id = 1
        mock_session.__contains__ = lambda self, key: key in [
            "user_id",
            "username",
            "email",
            "role",
            "is_superadmin",
        ]
        mock_session.__delitem__ = MagicMock()
        mock_st.session_state = mock_session

        AuthManager.logout()

        # log_action should be called for logout
        mock_log_action.assert_called()

    @patch("src.auth.auth_manager.st")
    def test_logout_no_user(self, mock_st):
        """Test logout when no user is logged in."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = {}

        # Should not raise error
        AuthManager.logout()


class TestAuthManagerIsAuthenticated:
    """Tests for AuthManager.is_authenticated method."""

    @patch("src.auth.auth_manager.st")
    def test_is_authenticated_with_user_id(self, mock_st):
        """Test is_authenticated returns True when user_id exists."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.side_effect = lambda key, default=None: {
            "user_id": 1,
            "connected": False,
            "google_user": None,
        }.get(key, default)
        mock_st.session_state.__contains__ = lambda self, key: key == "user_id"

        assert AuthManager.is_authenticated() is True

    @patch("src.auth.auth_manager.st")
    def test_is_authenticated_with_google_user(self, mock_st):
        """Test is_authenticated returns True for Google OAuth user."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.side_effect = lambda key, default=None: {
            "connected": True,
            "google_user": {"email": "test@gmail.com"},
        }.get(key, default)
        mock_st.session_state.__contains__ = lambda self, key: False

        assert AuthManager.is_authenticated() is True

    @patch("src.auth.auth_manager.st")
    def test_is_authenticated_no_user(self, mock_st):
        """Test is_authenticated returns False when no user."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = None
        mock_st.session_state.__contains__ = lambda self, key: False

        assert AuthManager.is_authenticated() is False


class TestAuthManagerGetCurrentUser:
    """Tests for AuthManager.get_current_user method."""

    @patch("src.auth.auth_manager.st")
    def test_get_current_user_password_auth(self, mock_st):
        """Test get_current_user for password-authenticated user."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.side_effect = lambda key, default=None: {
            "user_id": 1,
            "username": "testuser",
            "email": "test@test.com",
            "role": "admin",
            "is_superadmin": True,
            "google_user": None,
            "connected": False,
        }.get(key, default)
        mock_st.session_state.__contains__ = lambda self, key: key == "user_id"

        user = AuthManager.get_current_user()

        assert user is not None
        assert user["user_id"] == 1
        assert user["username"] == "testuser"
        assert user["auth_method"] == "password"

    @patch("src.auth.auth_manager.st")
    def test_get_current_user_google_auth(self, mock_st):
        """Test get_current_user for Google OAuth user."""
        from src.auth.auth_manager import AuthManager

        google_user_data = {
            "oauth_id": "google123",
            "name": "Test User",
            "email": "test@gmail.com",
            "picture": "https://example.com/pic.jpg",
        }

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.side_effect = lambda key, default=None: {
            "connected": True,
            "google_user": google_user_data,
        }.get(key, default)
        mock_st.session_state.__contains__ = lambda self, key: False

        user = AuthManager.get_current_user()

        assert user is not None
        assert user["email"] == "test@gmail.com"
        assert user["auth_method"] == "google"

    @patch("src.auth.auth_manager.st")
    def test_get_current_user_not_authenticated(self, mock_st):
        """Test get_current_user returns None when not authenticated."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = None
        mock_st.session_state.__contains__ = lambda self, key: False

        user = AuthManager.get_current_user()

        assert user is None


class TestAuthManagerRequireAuth:
    """Tests for AuthManager.require_auth method."""

    @patch("src.auth.auth_manager.st")
    def test_require_auth_stops_when_not_authenticated(self, mock_st):
        """Test require_auth calls st.stop when not authenticated."""
        from src.auth.auth_manager import AuthManager

        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = None
        mock_st.session_state.__contains__ = lambda self, key: False

        with pytest.raises(Exception):  # st.stop raises StopException
            mock_st.stop.side_effect = Exception("Stopped")
            AuthManager.require_auth()

        mock_st.warning.assert_called()
        mock_st.stop.assert_called()


class TestAuthManagerRequireSuperadmin:
    """Tests for AuthManager.require_superadmin method."""

    @patch("src.auth.auth_manager.st")
    def test_require_superadmin_stops_for_non_superadmin(self, mock_st):
        """Test require_superadmin stops non-superadmin users."""
        from src.auth.auth_manager import AuthManager

        # Mock authenticated but not superadmin
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.side_effect = lambda key, default=None: {
            "user_id": 1,
            "is_superadmin": False,
            "google_user": None,
            "connected": False,
        }.get(key, default)
        mock_st.session_state.__contains__ = lambda self, key: key == "user_id"

        with pytest.raises(Exception):
            mock_st.stop.side_effect = Exception("Stopped")
            AuthManager.require_superadmin()

        mock_st.error.assert_called()
        mock_st.stop.assert_called()
