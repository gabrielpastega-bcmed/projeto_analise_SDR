"""
Sentry configuration for error tracking and performance monitoring.

Provides centralized error handling without modifying existing code.
"""

import os
from typing import Any, Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry() -> None:
    """
    Initialize Sentry SDK for error tracking.

    Reads configuration from environment variables:
    - SENTRY_DSN: Sentry project DSN
    - SENTRY_ENVIRONMENT: Environment name (dev/staging/prod)
    - SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate
    """
    dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        # Sentry disabled - silent fail for local development
        return

    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        # Performance monitoring
        traces_sample_rate=traces_sample_rate,
        # Logging integration
        integrations=[
            LoggingIntegration(
                level=None,  # Capture all logs
                event_level="ERROR",  # Only send errors as events
            ),
        ],
        # Add user context automatically
        send_default_pii=False,  # Don't send PII by default
        # Release tracking
        release=os.getenv("APP_VERSION", "dev"),
    )


def set_user_context(user_id: Optional[int] = None, username: Optional[str] = None) -> None:
    """
    Set user context for Sentry events.

    Args:
        user_id: User ID
        username: Username
    """
    if user_id or username:
        sentry_sdk.set_user({"id": str(user_id) if user_id else None, "username": username})


def set_tags(**tags: Any) -> None:
    """
    Set custom tags for Sentry events.

    Example:
        set_tags(page="dashboard", filter_active=True)
    """
    for key, value in tags.items():
        sentry_sdk.set_tag(key, str(value))


def capture_exception(error: Exception, **extra: Any) -> None:
    """
    Manually capture an exception with extra context.

    Args:
        error: Exception to capture
        **extra: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **extra: Any) -> None:
    """
    Capture a message (breadcrumb).

    Args:
        message: Message to capture
        level: Severity level (debug/info/warning/error)
        **extra: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


# Initialize on import if DSN is available
init_sentry()
