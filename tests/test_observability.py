"""
Tests for Observability Module (Sentry and Health Checks).
"""

from unittest.mock import MagicMock, patch


class TestSentryConfig:
    """Tests for Sentry configuration."""

    @patch("src.observability.sentry_config.sentry_sdk")
    @patch.dict("os.environ", {"SENTRY_DSN": "https://test@sentry.io/123"}, clear=False)
    def test_init_sentry_with_dsn(self, mock_sentry):
        """Test Sentry initializes when DSN is provided."""
        from src.observability.sentry_config import init_sentry

        init_sentry()

        mock_sentry.init.assert_called_once()
        call_args = mock_sentry.init.call_args
        assert call_args[1]["dsn"] == "https://test@sentry.io/123"

    @patch("src.observability.sentry_config.sentry_sdk")
    @patch.dict("os.environ", {}, clear=True)
    def test_init_sentry_without_dsn(self, mock_sentry):
        """Test Sentry doesn't initialize without DSN."""
        from src.observability.sentry_config import init_sentry

        init_sentry()

        mock_sentry.init.assert_not_called()

    @patch("src.observability.sentry_config.sentry_sdk")
    def test_set_user_context(self, mock_sentry):
        """Test setting user context."""
        from src.observability.sentry_config import set_user_context

        set_user_context(user_id=123, username="testuser")

        mock_sentry.set_user.assert_called_once_with({"id": "123", "username": "testuser"})

    @patch("src.observability.sentry_config.sentry_sdk")
    def test_capture_exception(self, mock_sentry):
        """Test manual exception capture."""
        from src.observability.sentry_config import capture_exception

        error = ValueError("test error")
        capture_exception(error, extra_key="extra_value")

        mock_sentry.capture_exception.assert_called_once()


class TestHealthChecks:
    """Tests for health check functions."""

    @patch("src.auth.database.SessionLocal")
    def test_check_postgres_healthy(self, mock_session_local):
        """Test PostgreSQL health check when healthy."""
        from src.observability.health import check_postgres

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        result = check_postgres()

        assert result["status"] == "healthy"
        assert "latency_ms" in result
        assert result["error"] is None
        mock_db.execute.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.auth.database.SessionLocal")
    def test_check_postgres_unhealthy(self, mock_session_local):
        """Test PostgreSQL health check when connection fails."""
        from src.observability.health import check_postgres

        mock_session_local.side_effect = Exception("Connection refused")

        result = check_postgres()

        assert result["status"] == "unhealthy"
        assert "Connection refused" in result["error"]

    @patch.dict("os.environ", {}, clear=True)
    def test_check_bigquery_not_configured(self):
        """Test BigQuery check when not configured."""
        from src.observability.health import check_bigquery

        result = check_bigquery()

        assert result["status"] == "not_configured"
        assert result["error"] is None

    @patch("src.observability.health.check_postgres")
    @patch("src.observability.health.check_bigquery")
    @patch("src.observability.health.check_gemini_api")
    def test_get_health_status_all_healthy(self, mock_gemini, mock_bigquery, mock_postgres):
        """Test overall health status when all components are healthy."""
        from src.observability.health import get_health_status

        mock_postgres.return_value = {"status": "healthy"}
        mock_bigquery.return_value = {"status": "healthy"}
        mock_gemini.return_value = {"status": "configured"}

        result = get_health_status()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "components" in result

    @patch("src.observability.health.check_postgres")
    @patch("src.observability.health.check_bigquery")
    @patch("src.observability.health.check_gemini_api")
    def test_get_health_status_postgres_unhealthy(self, mock_gemini, mock_bigquery, mock_postgres):
        """Test overall health status when PostgreSQL is unhealthy."""
        from src.observability.health import get_health_status

        mock_postgres.return_value = {"status": "unhealthy"}
        mock_bigquery.return_value = {"status": "healthy"}
        mock_gemini.return_value = {"status": "configured"}

        result = get_health_status()

        assert result["status"] == "unhealthy"
