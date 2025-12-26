"""
Tests for Alert System (Models and Service).
"""

from unittest.mock import MagicMock, patch


class TestAlertModel:
    """Tests for Alert model."""

    def test_alert_creation_defaults(self):
        """Test alert creation with default values."""
        from src.auth.alert_models import Alert

        alert = Alert(
            alert_type="tme_high",
            title="High TME",
            message="TME is too high",
            metric_value=20.5,
            severity="warning",
            status="active",
        )

        assert alert.alert_type == "tme_high"
        assert alert.severity == "warning"
        assert alert.status == "active"
        assert alert.title == "High TME"

    def test_alert_acknowledge(self):
        """Test acknowledging an alert."""
        from src.auth.alert_models import Alert

        alert = Alert(status="active")
        alert.acknowledge(user_id=1)

        assert alert.status == "acknowledged"
        assert alert.acknowledged_by == 1
        assert alert.acknowledged_at is not None

    def test_alert_resolve(self):
        """Test resolving an alert."""
        from src.auth.alert_models import Alert

        alert = Alert(status="active")
        alert.resolve()

        assert alert.status == "resolved"
        assert alert.resolved_at is not None

    def test_alert_is_active(self):
        """Test is_active property."""
        from src.auth.alert_models import Alert

        alert = Alert(status="active")
        assert alert.is_active() is True

        alert.status = "resolved"
        assert alert.is_active() is False


class TestAlertService:
    """Tests for AlertService."""

    @patch("src.auth.alert_service.SessionLocal")
    def test_check_tme_threshold_creates_alert(self, mock_session_local):
        """Test that TME exceeding threshold creates an alert."""
        from src.auth.alert_service import AlertService

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock no existing alert
        mock_db.query.return_value.filter.return_value.first.return_value = None
        # Mock global threshold (fallback default is 15.0)
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, None]

        # 20.0 > 15.0 -> Should create alert
        alert = AlertService.check_tme_threshold(current_tme=20.0)

        assert alert is not None
        assert alert.alert_type == "tme_high"
        assert alert.metric_value == 20.0
        mock_db.add.assert_called_once()

    @patch("src.auth.alert_service.SessionLocal")
    def test_check_tme_threshold_no_alert(self, mock_session_local):
        """Test that TME below threshold does not create alert."""
        from src.auth.alert_service import AlertService

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        # Mock thresholds returning nothing (using defaults)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 10.0 < 15.0 -> No alert
        alert = AlertService.check_tme_threshold(current_tme=10.0)

        assert alert is None
        mock_db.add.assert_not_called()

    @patch("src.auth.alert_service.SessionLocal")
    def test_create_alert_updates_existing(self, mock_session_local):
        """Test that create_alert updates existing active alert instead of creating new."""
        from src.auth.alert_service import AlertService

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        alert = AlertService.create_alert(
            alert_type="test",
            severity="info",
            title="Test",
            message="Msg",
            metric_value=10.0,
            threshold_value=5.0,
        )

        assert alert == mock_existing
        assert mock_existing.metric_value == 10.0
        mock_db.add.assert_not_called()

    @patch("src.auth.alert_service.SessionLocal")
    def test_resolve_alert(self, mock_session_local):
        """Test resolving an alert via service."""
        from src.auth.alert_service import AlertService

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_alert = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        result = AlertService.resolve_alert(alert_id=1)

        assert result is True
        mock_alert.resolve.assert_called_once()
        mock_db.commit.assert_called_once()
