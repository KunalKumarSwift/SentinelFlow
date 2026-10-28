"""Map Keycloak access-token claims to a ``Principal``.

Expected realm set-up (see ``deploy/keycloak``): user attributes ``tenant_id`` and
``team`` mapped into the token; realm roles named like ours. Only roles we know are kept,
and never ``orchestrator``: that role belongs to the system principal alone, so no
identity-provider administrator can hand it to a person.
"""

from collections.abc import Mapping
from typing import cast

from sentinelflow.domain.errors import AuthenticationError
from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.security.roles import ROLE_PERMISSIONS

GRANTABLE_ROLES = frozenset(ROLE_PERMISSIONS) - {"orchestrator"}


def principal_from_keycloak(claims: Mapping[str, object]) -> Principal:
    """Build the principal for verified Keycloak claims.

    Raises:
        AuthenticationError: If a required claim is missing or malformed.
    """
    # Keycloak puts ``client_id`` only into service-account (client-credentials) tokens.
    kind = PrincipalKind.SERVICE if "client_id" in claims else PrincipalKind.USER
    return Principal(
        subject=_text(claims, "sub"),
        tenant_id=_text(claims, "tenant_id"),
        team=_text(claims, "team"),
        roles=_realm_roles(claims) & GRANTABLE_ROLES,
        kind=kind,
    )


def _realm_roles(claims: Mapping[str, object]) -> frozenset[str]:
    access = claims.get("realm_access")
    if not isinstance(access, dict):
        return frozenset()
    roles = cast(dict[str, object], access).get("roles")
    if not isinstance(roles, list):
        return frozenset()
    return frozenset(r for r in cast(list[object], roles) if isinstance(r, str))


def _text(claims: Mapping[str, object], name: str) -> str:
    value = claims.get(name)
    if not isinstance(value, str) or not value.strip():
        raise AuthenticationError(f"claim {name!r} must be a non-empty string")
    return value
