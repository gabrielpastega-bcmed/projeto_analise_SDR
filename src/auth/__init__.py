"""
Authentication module for dashboard access control.

This module provides user authentication, session management,
and role-based access control (RBAC) for the SDR Analytics dashboard.
"""

from .permissions import Permission, Role, has_permission

__version__ = "1.0.0"
__all__ = ["Permission", "Role", "has_permission"]
