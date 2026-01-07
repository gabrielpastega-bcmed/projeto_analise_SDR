"""
Permission system for role-based access control.

Defines roles, permissions, and page access mappings.
"""

from enum import Enum
from typing import Dict, List


class Role(str, Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Available permissions in the system."""

    # Dashboard pages
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_AGENTS = "view_agents"
    VIEW_TEMPORAL = "view_temporal"
    VIEW_LEADS = "view_leads"
    VIEW_INSIGHTS = "view_insights"
    VIEW_ADMIN = "view_admin"
    VIEW_ALERTS = "view_alerts"
    VIEW_HEALTH = "view_health"
    VIEW_AUTOMATION = "view_automation"

    # Actions
    EXPORT_DATA = "export_data"
    EXPORT_PDF = "export_pdf"

    # User management
    MANAGE_USERS = "manage_users"
    APPROVE_USERS = "approve_users"


# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.ADMIN: list(Permission),  # All permissions
    Role.SUPERVISOR: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_AGENTS,
        Permission.VIEW_TEMPORAL,
        Permission.VIEW_LEADS,
        Permission.VIEW_INSIGHTS,
        Permission.VIEW_ALERTS,
        Permission.EXPORT_DATA,
        Permission.EXPORT_PDF,
    ],
    Role.ANALYST: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TEMPORAL,
        Permission.VIEW_LEADS,
        Permission.VIEW_INSIGHTS,
        Permission.EXPORT_DATA,
        Permission.EXPORT_PDF,
    ],
    Role.VIEWER: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_LEADS,
    ],
}

# Page -> Permission mapping
PAGE_PERMISSIONS: Dict[str, Permission] = {
    "Visão_Geral": Permission.VIEW_DASHBOARD,
    "Agentes": Permission.VIEW_AGENTS,
    "Análise_Temporal": Permission.VIEW_TEMPORAL,
    "Leads": Permission.VIEW_LEADS,
    "Insights": Permission.VIEW_INSIGHTS,
    "Admin": Permission.VIEW_ADMIN,
    "Alertas": Permission.VIEW_ALERTS,
    "Health": Permission.VIEW_HEALTH,
    "Automação": Permission.VIEW_AUTOMATION,
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User role string
        permission: Permission to check

    Returns:
        True if role has the permission
    """
    try:
        role_enum = Role(role)
        return permission in ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return False


def get_role_permissions(role: str) -> List[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: User role string

    Returns:
        List of permissions for the role
    """
    try:
        role_enum = Role(role)
        return ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return []


def can_access_page(role: str, page_name: str) -> bool:
    """
    Check if a role can access a specific page.

    Args:
        role: User role string
        page_name: Page name (e.g., "Agentes", "Admin")

    Returns:
        True if role can access the page
    """
    permission = PAGE_PERMISSIONS.get(page_name)
    if permission is None:
        # Unknown page - default to allow for backward compatibility
        return True
    return has_permission(role, permission)


def get_role_display_name(role: str) -> str:
    """
    Get human-readable display name for a role.

    Args:
        role: Role string

    Returns:
        Display name in Portuguese
    """
    display_names = {
        "admin": "Administrador",
        "supervisor": "Supervisor",
        "analyst": "Analista",
        "viewer": "Visualizador",
    }
    return display_names.get(role, role.title())


def get_all_roles() -> List[str]:
    """Get list of all available roles."""
    return [r.value for r in Role]
