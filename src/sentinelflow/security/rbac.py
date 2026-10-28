"""Role-based access checks. Default deny: only listed grants count."""

from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission
from sentinelflow.security.roles import ROLE_PERMISSIONS


def permissions_of(principal: Principal) -> frozenset[Permission]:
    """Return the union of permissions granted by the principal's known roles.

    Args:
        principal: The authenticated identity.

    Returns:
        All granted permissions; unknown role names contribute nothing.
    """
    granted = (ROLE_PERMISSIONS.get(role, frozenset[Permission]()) for role in principal.roles)
    return frozenset[Permission]().union(*granted)


def has_permission(principal: Principal, permission: Permission) -> bool:
    """Return whether any of the principal's roles grants ``permission``."""
    return permission in permissions_of(principal)
