"""
Database models for authentication system.

Defines User, Session, AuditLog, and UserPreferences models.
Uses SQLAlchemy 2.0 declarative style with Mapped types.
"""

from datetime import datetime

import bcrypt
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """
    User model for authentication.

    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        password_hash: Bcrypt hashed password
        role: User role ('superadmin' or 'user')
        is_active: Whether user account is active
        created_at: Account creation timestamp
        last_login: Last login timestamp
        created_by: ID of user who created this account
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)

    # Relationships - using string references for forward declarations
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    preferences: Mapped["UserPreferences | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """
        Hash and set password using bcrypt.

        Args:
            password: Plain text password to hash
        """
        # Bcrypt has 72 byte limit
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password too long (max 72 bytes)")

        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        self.password_hash = hashed.decode("utf-8")

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode("utf-8")
        hash_bytes = self.password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def is_superadmin(self) -> bool:
        """Check if user has superadmin role."""
        return self.role == "superadmin"

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Session(Base):
    """
    User session model for tracking active sessions.

    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        token: Unique session token
        created_at: Session creation timestamp
        expires_at: Session expiration timestamp
        ip_address: Client IP address
        user_agent: Client user agent string
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, expires={self.expires_at})>"


class AuditLog(Base):
    """
    Audit log for tracking user actions.

    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        action: Action performed (e.g., 'login', 'export', 'view_page')
        resource: Resource accessed (e.g., page name, export type)
        timestamp: When action occurred
        details: Additional details in JSON format
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', timestamp={self.timestamp})>"


class UserPreferences(Base):
    """
    User preferences for dashboard customization.

    Attributes:
        user_id: Primary key (foreign key to users table)
        theme: UI theme ('light' or 'dark')
        default_filters: Default filter values in JSON format
        dashboard_layout: Custom dashboard layout in JSON format
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    theme: Mapped[str] = mapped_column(String(10), default="light", nullable=False)
    default_filters: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    dashboard_layout: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreferences(user_id={self.user_id}, theme='{self.theme}')>"
