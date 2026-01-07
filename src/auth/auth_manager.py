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


def log_action(
    user_id: int,
    action: str,
    resource: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
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
            user_id=user_id,
            action=action,
            resource=resource,
            details=json.dumps(details) if details else None,
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
            user = (
                db.query(User).filter(User.username == username, User.is_active).first()
            )

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
                    log_action(
                        user.id,
                        "login",
                        None,
                        {"success": False, "reason": "invalid_password"},
                    )

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
        # Check traditional password login
        if (
            "user_id" in st.session_state
            and st.session_state.get("user_id") is not None
        ):
            return True

        # Check Google OAuth login
        if st.session_state.get("connected", False) and st.session_state.get(
            "google_user"
        ):
            return True

        return False

    @staticmethod
    def get_current_user() -> Optional[dict]:
        """
        Get current user information from session.

        Returns:
            Dictionary with user info if authenticated, None otherwise
        """
        if not AuthManager.is_authenticated():
            return None

        # Check for Google OAuth user first
        if st.session_state.get("google_user"):
            google_user = st.session_state.get("google_user")
            if google_user is not None:  # Type guard for mypy
                return {
                    "user_id": google_user.get("oauth_id"),
                    "username": google_user.get(
                        "name", google_user.get("email", "").split("@")[0]
                    ),
                    "email": google_user.get("email"),
                    "role": "user",  # Default role for Google users
                    "is_superadmin": False,  # Google users are not superadmins by default
                    "picture": google_user.get("picture"),
                    "auth_method": "google",
                }

        # Traditional password user
        return {
            "user_id": st.session_state.get("user_id"),
            "username": st.session_state.get("username"),
            "email": st.session_state.get("email"),
            "role": st.session_state.get("role"),
            "is_superadmin": st.session_state.get("is_superadmin", False),
            "auth_method": "password",
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

        # Check if user is approved (for Google OAuth users)
        user = AuthManager.get_current_user()
        if user and user.get("status") == "pending":
            st.warning("⏳ Sua conta está aguardando aprovação de um administrador.")
            st.info("Você receberá acesso assim que sua conta for aprovada.")
            st.stop()
        elif user and user.get("status") == "rejected":
            st.error(
                "❌ Sua conta foi rejeitada. Entre em contato com o administrador."
            )
            st.stop()

    @staticmethod
    def require_admin() -> None:
        """
        Require admin role to proceed.

        If user is not authenticated or not an admin, shows error and stops.
        """
        AuthManager.require_auth()

        role = st.session_state.get("role")
        if role != "admin":
            st.error(
                "❌ Acesso negado. Apenas administradores podem acessar esta página."
            )
            st.stop()

    @staticmethod
    def require_superadmin() -> None:
        """
        Require superadmin/admin role to proceed (alias for backward compatibility).

        If user is not authenticated or not an admin, shows error and stops.
        """
        AuthManager.require_admin()

    @staticmethod
    def require_role(allowed_roles: list[str]) -> None:
        """
        Require one of the specified roles to proceed.

        Args:
            allowed_roles: List of role strings that can access (e.g., ["admin", "supervisor"])
        """
        AuthManager.require_auth()

        role = st.session_state.get("role")
        if role not in allowed_roles:
            st.error(
                f"❌ Acesso negado. Seu perfil ({role}) não tem permissão para esta página."
            )
            st.stop()

    @staticmethod
    def require_permission(permission) -> None:
        """
        Require a specific permission to proceed.

        Args:
            permission: Permission enum value from src.auth.permissions
        """
        from .permissions import has_permission

        AuthManager.require_auth()

        role = st.session_state.get("role", "viewer")
        if not has_permission(role, permission):
            st.error(
                "❌ Acesso negado. Você não tem permissão para acessar esta página."
            )
            st.stop()

    @staticmethod
    def check_permission(permission) -> bool:
        """
        Check if current user has specific permission.

        Args:
            permission: Permission string or Permission enum

        Returns:
            True if user has permission, False otherwise
        """
        from .permissions import Permission, has_permission

        if not AuthManager.is_authenticated():
            return False

        role = st.session_state.get("role", "viewer")

        # Handle string permissions for backward compatibility
        if isinstance(permission, str):
            try:
                permission = Permission(permission)
            except ValueError:
                # Unknown permission string
                return role == "admin"

        return has_permission(role, permission)

    @staticmethod
    def get_user_role() -> str:
        """Get current user's role."""
        return st.session_state.get("role", "viewer")
