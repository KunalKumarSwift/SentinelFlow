"""``POST /v1/auth/dev-token``: mint tokens for local demos. Mounted only when APP_ENV=dev."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.security.tokens import Hs256TokenService


class DevTokenIn(BaseModel):
    """Identity to issue a token for."""

    subject: str = Field(min_length=1, max_length=64)
    tenant_id: str = Field(min_length=1, max_length=64)
    team: str = Field(min_length=1, max_length=64)
    roles: list[str] = Field(min_length=1, max_length=10)
    kind: Literal["user", "service"] = "user"


class TokenOut(BaseModel):
    """A bearer token."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 -- OAuth token type, not a secret


def build_dev_auth_router(tokens: Hs256TokenService) -> APIRouter:
    """Return the dev-token router; the app decides whether to mount it."""
    router = APIRouter(prefix="/v1/auth", tags=["auth (dev only)"])

    @router.post("/dev-token")
    def dev_token(body: DevTokenIn) -> TokenOut:
        """Issue a short-lived token for any identity. Never mounted outside dev."""
        principal = Principal(
            body.subject, body.tenant_id, body.team, frozenset(body.roles), PrincipalKind(body.kind)
        )
        return TokenOut(access_token=tokens.issue(principal))

    return router
