"""
Alert model for monitoring system.

Defines alerts for metrics thresholds (TME, Volume, Conversion Rate).
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class AlertType(str, Enum):
    """Types of alerts that can be triggered."""

    TME_HIGH = "tme_high"  # TME above threshold
    VOLUME_LOW = "volume_low"  # Volume below threshold
    CONVERSION_LOW = "conversion_low"  # Conversion rate below threshold
    CUSTOM = "custom"  # Custom user-defined alert


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base):
    """
    Alert model for monitoring metrics.

    Attributes:
        id: Primary key
        alert_type: Type of alert (TME, Volume, Conversion)
        severity: Severity level
        status: Current status
        title: Alert title
        message: Detailed message
        metric_value: Current metric value that triggered alert
        threshold_value: Threshold that was exceeded
        created_at: When alert was created
        acknowledged_at: When alert was acknowledged
        acknowledged_by: User who acknowledged
        resolved_at: When alert was resolved
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    metric_value: Mapped[float | None] = mapped_column(nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    acknowledged_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    # Relationships
    acknowledger: Mapped["User | None"] = relationship(foreign_keys=[acknowledged_by])

    def acknowledge(self, user_id: int) -> None:
        """Mark alert as acknowledged by user."""
        self.status = AlertStatus.ACKNOWLEDGED.value
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = user_id

    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED.value
        self.resolved_at = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.status == AlertStatus.ACTIVE.value

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', status='{self.status}')>"


class AlertThreshold(Base):
    """
    User-configurable thresholds for alerts.

    Attributes:
        id: Primary key
        user_id: User who set this threshold (None for global)
        alert_type: Type of alert
        threshold_value: Threshold value
        is_enabled: Whether this threshold is active
    """

    __tablename__ = "alert_thresholds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold_value: Mapped[float] = mapped_column(nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )  # Relationships
    user: Mapped["User | None"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<AlertThreshold(type='{self.alert_type}', value={self.threshold_value})>"


# Import User for type hints (avoid circular import)
from .models import User  # noqa: E402, F401
