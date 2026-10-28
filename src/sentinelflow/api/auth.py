"""FastAPI dependencies: who is calling (bearer token) and may they do this?"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sentinelflow.domain.errors import AuthenticationError, PolicyDeniedError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission
from sentinelflow.security.rbac import has_permission
from sentinelflow.security.tokens import Hs256TokenService

# auto_error=False so a missing token becomes our problem+json 401, not FastAPI's 403.
_BEARER = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)]


class Auth:
    """Builds route dependencies bound to one token service."""

    def __init__(self, tokens: Hs256TokenService, recorder: AuditRecorder) -> None:
        """Verify tokens with ``tokens``; audit every permission denial."""
        self._tokens, self._recorder = tokens, recorder

    def current_principal(self, credentials: Credentials) -> Principal:
        """Return the verified caller.

        Raises:
            AuthenticationError: If the bearer token is missing or invalid.
        """
        if credentials is None:
            raise AuthenticationError("missing bearer token")
        return self._tokens.verify(credentials.credentials)

    def require(self, permission: Permission) -> Callable[[Principal], Principal]:
        """Return a dependency that admits only callers holding ``permission``."""

        def dependency(
            principal: Annotated[Principal, Depends(self.current_principal)],
        ) -> Principal:
            if not has_permission(principal, permission):
                self._recorder.record(principal, "policy.denied", "api", {"permission": permission})
                raise PolicyDeniedError(f"missing permission {permission}")
            return principal

        return dependency
