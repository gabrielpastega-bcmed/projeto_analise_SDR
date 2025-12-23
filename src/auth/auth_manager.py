"""
Authentication manager for handling login, logout, and session management.

Provides centralized authentication logic for the dashboard.
"""

import json
from datetime import datetime
from typing import Optional

import streamlit as st

from .database import SessionLocal
from .models import AuditLog, User


def log_action(user_id: int, action: str, resource: Optional[str] = None, details: Optional[dict] = None) -> None:
    """
    Log user action to audit log.

    Args:
        user_id: ID of user performing action
        action: Action name (e.g., 'login', 'export', 'view_page')
        resource: Resource being accessed (optional)
        details: Additional details as dictionary (optional)
    """
    db = SessionLocal()
    try:
        log_entry = AuditLog(
            user_id=user_id, action=action, resource=resource, details=json.dumps(details) if details else None
        )
        db.add(log_entry)
        db.commit()
    finally:
        db.close()


class AuthManager:
    """Authentication manager for handling user sessions."""

    @staticmethod
    def login(username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.

        Args:
            username: Username to authenticate
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        db = SessionLocal()
        try:
            # Find active user by username
            user = db.query(User).filter(User.username == username, User.is_active).first()

            # Verify password
            if user and user.check_password(password):
                # Update last login
                user.last_login = datetime.utcnow()
                db.commit()

                # Log successful login
                log_action(user.id, "login", None, {"success": True})

                return user
            else:
                # Log failed login attempt
                if user:
                    log_action(user.id, "login", None, {"success": False, "reason": "invalid_password"})

                return None

        finally:
            db.close()

    @staticmethod
    def logout() -> None:
        """
        Clear current session.

        Removes all authentication-related session state.
        """
        # Log logout before clearing session
        if "user_id" in st.session_state:
            log_action(st.session_state.user_id, "logout", None)

        # Clear all auth-related session state
        auth_keys = ["user_id", "username", "email", "role", "is_superadmin"]
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if user is currently authenticated.

        Returns:
            True if user is logged in, False otherwise
        """
        return "user_id" in st.session_state and st.session_state.get("user_id") is not None

    @staticmethod
    def get_current_user() -> Optional[dict]:
        """
        Get current user information from session.

        Returns:
            Dictionary with user info if authenticated, None otherwise
        """
        if not AuthManager.is_authenticated():
            return None

        return {
            "user_id": st.session_state.get("user_id"),
            "username": st.session_state.get("username"),
            "email": st.session_state.get("email"),
            "role": st.session_state.get("role"),
            "is_superadmin": st.session_state.get("is_superadmin", False),
        }

    @staticmethod
    def require_auth() -> None:
        """
        Require authentication to proceed.

        If user is not authenticated, shows warning and stops execution.
        This should be called at the top of protected pages.
        """
        if not AuthManager.is_authenticated():
            st.warning("🔒 Faça login para acessar esta página.")
            st.info("👈 Use o menu lateral para fazer login.")
            st.stop()

    @staticmethod
    def require_superadmin() -> None:
        """
        Require superadmin role to proceed.

        If user is not authenticated or not a superadmin, shows error and stops.
        """
        AuthManager.require_auth()

        if not st.session_state.get("is_superadmin", False):
            st.error("❌ Acesso negado. Apenas superadministradores podem acessar esta página.")
            st.stop()

    @staticmethod
    def check_permission(permission: str) -> bool:
        """
        Check if current user has specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        if not AuthManager.is_authenticated():
            return False

        role = st.session_state.get("role")

        # Superadmins have all permissions
        if role == "superadmin":
            return True

        # Define permissions for regular users
        user_permissions = ["view_dashboard", "export_pdf", "view_data"]

        return permission in user_permissions
