"""
Tests for Google OAuth integration module.

Uses mocking to avoid actual OAuth calls.
"""

import os
from unittest.mock import MagicMock, patch


class TestIsGoogleOAuthEnabled:
    """Tests for is_google_oauth_enabled function."""

    def test_enabled_when_true(self):
        """Test returns True when env var is 'true'."""
        with patch.dict(os.environ, {"GOOGLE_OAUTH_ENABLED": "true"}):
            # Reload to pick up env change
            import importlib

            import src.auth.google_auth

            importlib.reload(src.auth.google_auth)

            assert src.auth.google_auth.is_google_oauth_enabled() is True

    def test_disabled_when_false(self):
        """Test returns False when env var is 'false'."""
        with patch.dict(os.environ, {"GOOGLE_OAUTH_ENABLED": "false"}):
            import importlib

            import src.auth.google_auth

            importlib.reload(src.auth.google_auth)

            assert src.auth.google_auth.is_google_oauth_enabled() is False

    def test_disabled_when_not_set(self):
        """Test returns False when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            import src.auth.google_auth

            importlib.reload(src.auth.google_auth)

            assert src.auth.google_auth.is_google_oauth_enabled() is False


class TestGetGoogleOAuthConfig:
    """Tests for get_google_oauth_config function."""

    def test_returns_config_dict(self):
        """Test that config dict contains expected keys."""
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "test_client_id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "test_secret",
                "GOOGLE_OAUTH_REDIRECT_URI": "http://test.com",
                "GOOGLE_OAUTH_COOKIE_NAME": "test_cookie",
                "GOOGLE_OAUTH_COOKIE_KEY": "test_key",
            },
        ):
            import importlib

            import src.auth.google_auth

            importlib.reload(src.auth.google_auth)

            config = src.auth.google_auth.get_google_oauth_config()

            assert config["client_id"] == "test_client_id"
            assert config["client_secret"] == "test_secret"
            assert config["redirect_uri"] == "http://test.com"
            assert config["cookie_name"] == "test_cookie"
            assert config["cookie_key"] == "test_key"

    def test_returns_defaults_when_not_set(self):
        """Test that defaults are used when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            import src.auth.google_auth

            importlib.reload(src.auth.google_auth)

            config = src.auth.google_auth.get_google_oauth_config()

            assert config["client_id"] == ""
            assert config["client_secret"] == ""
            assert config["redirect_uri"] == "http://localhost:8501"


class TestHandleGoogleLogin:
    """Tests for handle_google_login function."""

    @patch("src.auth.google_auth.init_google_auth")
    def test_returns_none_when_not_enabled(self, mock_init):
        """Test returns None when OAuth not configured."""
        mock_init.return_value = None

        from src.auth.google_auth import handle_google_login

        result = handle_google_login()

        assert result is None

    @patch("src.auth.google_auth.st")
    @patch("src.auth.google_auth.init_google_auth")
    def test_returns_user_info_when_connected(self, mock_init, mock_st):
        """Test returns user info when authenticated."""
        mock_authenticator = MagicMock()
        mock_init.return_value = mock_authenticator

        # Use MagicMock for session_state
        mock_session = MagicMock()
        mock_session.get.side_effect = lambda k, d=None: {
            "connected": True,
            "oauth_id": "google123",
            "user_info": {
                "email": "test@gmail.com",
                "name": "Test User",
                "picture": "https://example.com/pic.jpg",
            },
        }.get(k, d)
        mock_st.session_state = mock_session

        from src.auth.google_auth import handle_google_login

        handle_google_login()

        # Authenticator should check authentication
        mock_authenticator.check_authentification.assert_called()


class TestGoogleLogout:
    """Tests for google_logout function."""

    @patch("src.auth.google_auth.st")
    def test_clears_session_keys(self, mock_st):
        """Test that google_logout clears OAuth session keys."""
        mock_st.session_state = {
            "connected": True,
            "oauth_id": "google123",
            "user_info": {"email": "test@gmail.com"},
            "google_user": {"email": "test@gmail.com"},
        }

        from src.auth.google_auth import google_logout

        google_logout()

        assert "connected" not in mock_st.session_state
        assert "oauth_id" not in mock_st.session_state
        assert "user_info" not in mock_st.session_state
        assert "google_user" not in mock_st.session_state

    @patch("src.auth.google_auth.st")
    def test_handles_empty_session(self, mock_st):
        """Test google_logout handles empty session gracefully."""
        mock_st.session_state = {}

        from src.auth.google_auth import google_logout

        # Should not raise
        google_logout()
