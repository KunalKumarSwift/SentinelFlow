"""Mapping between a Principal and JWT claims, with strict claim validation."""

from collections.abc import Mapping
from datetime import datetime

from sentinelflow.domain.errors import AuthenticationError
from sentinelflow.domain.principals import Principal, PrincipalKind


def claims_for(
    principal: Principal, issued: datetime, expires: datetime, iss: str
) -> dict[str, object]:
    """Return the JWT claims that represent ``principal`` for one token lifetime."""
    return {
        "sub": principal.subject,
        "tenant_id": principal.tenant_id,
        "team": principal.team,
        "roles": sorted(principal.roles),
        "kind": principal.kind.value,
        "iss": iss,
        "iat": int(issued.timestamp()),
        "exp": int(expires.timestamp()),
    }


def principal_from(claims: Mapping[str, object]) -> Principal:
    """Build a Principal from verified claims.

    Raises:
        AuthenticationError: If a claim is missing or has the wrong type.
    """
    kind = _text(claims, "kind")
    if kind not in {k.value for k in PrincipalKind}:
        raise AuthenticationError(f"unknown principal kind {kind!r}")
    return Principal(
        subject=_text(claims, "sub"),
        tenant_id=_text(claims, "tenant_id"),
        team=_text(claims, "team"),
        roles=_roles(claims),
        kind=PrincipalKind(kind),
    )


def _text(claims: Mapping[str, object], name: str) -> str:
    value = claims.get(name)
    if not isinstance(value, str) or not value.strip():
        raise AuthenticationError(f"claim {name!r} must be a non-empty string")
    return value


def _roles(claims: Mapping[str, object]) -> frozenset[str]:
    value = claims.get("roles")
    if not isinstance(value, list) or not all(isinstance(r, str) for r in value):  # pyright: ignore[reportUnknownVariableType] -- narrowed below
        raise AuthenticationError("claim 'roles' must be a list of strings")
    return frozenset(str(r) for r in value)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType] -- elements checked above
