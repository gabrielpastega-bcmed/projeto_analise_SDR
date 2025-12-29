"""
Health check module for monitoring system dependencies.

Provides endpoints to check the health of database connections and external APIs.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import text


def check_postgres() -> dict[str, Any]:
    """
    Check PostgreSQL connection health.

    Returns:
        dict with status, latency, and error (if any)
    """
    from src.auth.database import SessionLocal

    start = datetime.now()
    try:
        db = SessionLocal()
        try:
            # Simple query to test connection
            db.execute(text("SELECT 1"))
            latency_ms = (datetime.now() - start).total_seconds() * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "error": None,
            }
        finally:
            db.close()
    except Exception as e:
        latency_ms = (datetime.now() - start).total_seconds() * 1000
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
        }


def check_bigquery() -> dict[str, Any]:
    """
    Check BigQuery API connection health.

    Returns:
        dict with status, latency, and error (if any)
    """
    import os

    # Only check if BigQuery is configured
    if not os.getenv("BIGQUERY_PROJECT_ID"):
        return {"status": "not_configured", "latency_ms": 0, "error": None}

    start = datetime.now()
    try:
        from google.cloud import bigquery

        client = bigquery.Client()
        # Simple query to test connection
        query = "SELECT 1"
        client.query(query).result()

        latency_ms = (datetime.now() - start).total_seconds() * 1000
        return {"status": "healthy", "latency_ms": round(latency_ms, 2), "error": None}
    except Exception as e:
        latency_ms = (datetime.now() - start).total_seconds() * 1000
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 2),
            "error": str(e)[:200],  # Truncate long errors
        }


def check_gemini_api() -> dict[str, Any]:
    """
    Check Gemini API health.

    Returns:
        dict with status and error (if any)
    """
    import os

    if not os.getenv("GEMINI_API_KEY"):
        return {"status": "not_configured", "error": None}

    # For now, just check if API key is set
    # Could add actual API call with timeout
    return {"status": "configured", "error": None}


def get_health_status() -> dict[str, Any]:
    """
    Get overall system health status.

    Returns:
        dict with timestamp, overall status, and individual component statuses
    """
    postgres = check_postgres()
    bigquery = check_bigquery()
    gemini = check_gemini_api()

    # Overall status is unhealthy if any critical component is unhealthy
    # PostgreSQL is critical, BigQuery and Gemini are optional
    overall_status = "healthy"
    if postgres["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif bigquery["status"] == "unhealthy":
        overall_status = "degraded"

    return {
        "timestamp": datetime.now().isoformat(),
        "status": overall_status,
        "components": {
            "postgres": postgres,
            "bigquery": bigquery,
            "gemini_api": gemini,
        },
    }
