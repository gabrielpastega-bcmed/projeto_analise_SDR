"""
Alert service for monitoring and creating alerts.

Handles threshold checking and alert management.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .alert_models import Alert, AlertSeverity, AlertStatus, AlertThreshold, AlertType
from .database import SessionLocal


class AlertService:
    """Service for managing alerts and thresholds."""

    # Default thresholds
    DEFAULT_THRESHOLDS = {
        AlertType.TME_HIGH.value: 15.0,  # TME > 15 minutes
        AlertType.VOLUME_LOW.value: 10,  # Volume < 10 per day
        AlertType.CONVERSION_LOW.value: 20.0,  # Conversion < 20%
    }

    @staticmethod
    def get_db() -> Session:
        """Get database session."""
        return SessionLocal()

    @classmethod
    def check_tme_threshold(cls, current_tme: float, user_id: Optional[int] = None) -> Optional[Alert]:
        """
        Check if TME exceeds threshold and create alert if needed.

        Args:
            current_tme: Current TME value in minutes
            user_id: User ID for user-specific threshold

        Returns:
            Alert if threshold exceeded, None otherwise
        """
        threshold = cls.get_threshold(AlertType.TME_HIGH.value, user_id)

        if current_tme > threshold:
            return cls.create_alert(
                alert_type=AlertType.TME_HIGH.value,
                severity=(
                    AlertSeverity.WARNING.value if current_tme < threshold * 1.5 else AlertSeverity.CRITICAL.value
                ),
                title="TME acima do limite",
                message=(
                    f"O Tempo Médio de Espera está em {current_tme:.1f} minutos, "
                    f"acima do limite de {threshold:.1f} minutos."
                ),
                metric_value=current_tme,
                threshold_value=threshold,
            )

        return None

    @classmethod
    def check_volume_threshold(cls, current_volume: int, user_id: Optional[int] = None) -> Optional[Alert]:
        """
        Check if volume is below threshold and create alert if needed.

        Args:
            current_volume: Current volume count
            user_id: User ID for user-specific threshold

        Returns:
            Alert if threshold not met, None otherwise
        """
        threshold = cls.get_threshold(AlertType.VOLUME_LOW.value, user_id)

        if current_volume < threshold:
            return cls.create_alert(
                alert_type=AlertType.VOLUME_LOW.value,
                severity=(
                    AlertSeverity.INFO.value if current_volume > threshold * 0.5 else AlertSeverity.WARNING.value
                ),
                title="Volume abaixo do esperado",
                message=f"O volume de atendimentos está em {current_volume}, abaixo do mínimo de {int(threshold)}.",
                metric_value=float(current_volume),
                threshold_value=threshold,
            )

        return None

    @classmethod
    def check_conversion_threshold(cls, current_rate: float, user_id: Optional[int] = None) -> Optional[Alert]:
        """
        Check if conversion rate is below threshold.

        Args:
            current_rate: Current conversion rate (0-100)
            user_id: User ID for user-specific threshold

        Returns:
            Alert if threshold not met, None otherwise
        """
        threshold = cls.get_threshold(AlertType.CONVERSION_LOW.value, user_id)

        if current_rate < threshold:
            return cls.create_alert(
                alert_type=AlertType.CONVERSION_LOW.value,
                severity=AlertSeverity.WARNING.value,
                title="Taxa de conversão baixa",
                message=f"A taxa de conversão está em {current_rate:.1f}%, abaixo da meta de {threshold:.1f}%.",
                metric_value=current_rate,
                threshold_value=threshold,
            )

        return None

    @classmethod
    def get_threshold(cls, alert_type: str, user_id: Optional[int] = None) -> float:
        """
        Get threshold value for alert type.

        Checks user-specific threshold first, then falls back to global.

        Args:
            alert_type: Type of alert
            user_id: User ID for user-specific threshold

        Returns:
            Threshold value
        """
        db = cls.get_db()
        try:
            # Check user-specific threshold first
            if user_id:
                user_threshold = (
                    db.query(AlertThreshold)
                    .filter(
                        AlertThreshold.alert_type == alert_type,
                        AlertThreshold.user_id == user_id,
                        AlertThreshold.is_enabled,
                    )
                    .first()
                )
                if user_threshold:
                    return user_threshold.threshold_value

            # Check global threshold
            global_threshold = (
                db.query(AlertThreshold)
                .filter(
                    AlertThreshold.alert_type == alert_type,
                    AlertThreshold.user_id.is_(None),
                    AlertThreshold.is_enabled,
                )
                .first()
            )
            if global_threshold:
                return global_threshold.threshold_value

            # Fall back to default
            return cls.DEFAULT_THRESHOLDS.get(alert_type, 0)

        finally:
            db.close()

    @classmethod
    def create_alert(
        cls,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        metric_value: float,
        threshold_value: float,
    ) -> Alert:
        """
        Create a new alert.

        Args:
            alert_type: Type of alert
            severity: Severity level
            title: Alert title
            message: Alert message
            metric_value: Current metric value
            threshold_value: Threshold that was exceeded

        Returns:
            Created Alert object
        """
        db = cls.get_db()
        try:
            # Check for duplicate recent alerts (within 1 hour)
            existing = (
                db.query(Alert)
                .filter(
                    Alert.alert_type == alert_type,
                    Alert.status == AlertStatus.ACTIVE.value,
                    Alert.created_at > datetime.now(timezone.utc) - timedelta(hours=1),
                )
                .first()
            )

            if existing:
                # Update existing alert instead of creating new
                existing.metric_value = metric_value
                existing.message = message
                db.commit()
                return existing

            # Create new alert
            alert = Alert(
                alert_type=alert_type,
                severity=severity,
                status=AlertStatus.ACTIVE.value,
                title=title,
                message=message,
                metric_value=metric_value,
                threshold_value=threshold_value,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

            return alert

        finally:
            db.close()

    @classmethod
    def get_active_alerts(cls, limit: int = 50) -> list[Alert]:
        """
        Get all active alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of active alerts, newest first
        """
        db = cls.get_db()
        try:
            return (
                db.query(Alert)
                .filter(Alert.status == AlertStatus.ACTIVE.value)
                .order_by(Alert.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()

    @classmethod
    def get_alert_count(cls) -> int:
        """Get count of active alerts."""
        db = cls.get_db()
        try:
            return db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE.value).count()
        finally:
            db.close()

    @classmethod
    def acknowledge_alert(cls, alert_id: int, user_id: int) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge
            user_id: ID of user acknowledging

        Returns:
            True if successful, False otherwise
        """
        db = cls.get_db()
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.acknowledge(user_id)
                db.commit()
                return True
            return False
        finally:
            db.close()

    @classmethod
    def resolve_alert(cls, alert_id: int) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: ID of alert to resolve

        Returns:
            True if successful, False otherwise
        """
        db = cls.get_db()
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.resolve()
                db.commit()
                return True
            return False
        finally:
            db.close()

    @classmethod
    def get_alert_history(cls, days: int = 7, limit: int = 100) -> list[Alert]:
        """
        Get alert history for specified days.

        Args:
            days: Number of days to look back
            limit: Maximum number of alerts

        Returns:
            List of alerts
        """
        db = cls.get_db()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            return (
                db.query(Alert).filter(Alert.created_at > cutoff).order_by(Alert.created_at.desc()).limit(limit).all()
            )
        finally:
            db.close()
