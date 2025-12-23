"""
Database configuration and session management for authentication.

Provides SQLAlchemy database connection and session management.
Supports both PostgreSQL (production) and SQLite (fallback).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base class for ORM models
Base = declarative_base()


# Database configuration from environment variables
def get_database_url() -> str:
    """
    Get database URL from environment variables.

    Prefers PostgreSQL if configured, falls back to SQLite.

    Returns:
        Database URL string for SQLAlchemy
    """
    # Try PostgreSQL first (production)
    pg_host = os.getenv("AUTH_DATABASE_HOST")
    pg_port = os.getenv("AUTH_DATABASE_PORT", "5432")
    pg_db = os.getenv("AUTH_DATABASE_NAME")
    pg_user = os.getenv("AUTH_DATABASE_USER")
    pg_password = os.getenv("AUTH_DATABASE_PASSWORD")

    if all([pg_host, pg_db, pg_user, pg_password]):
        # PostgreSQL connection string
        return f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

    # Fallback to SQLite (development)
    db_dir = Path(__file__).parent.parent.parent / "database"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "auth.db"
    return f"sqlite:///{db_path}"


# Create database URL
DATABASE_URL = get_database_url()

# Create engine with appropriate settings
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite configuration
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables.

    Creates all tables defined in models if they don't exist.
    Safe to call multiple times (idempotent).
    """

    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'SQLite'}")
