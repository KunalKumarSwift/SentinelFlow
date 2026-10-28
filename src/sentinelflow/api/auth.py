"""FastAPI dependencies: who is calling (bearer token), may they, and not too often?"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sentinelflow.domain.errors import AuthenticationError, PolicyDeniedError
from sentinelflow.domain.principals import Principal
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission
from sentinelflow.security.rbac import has_permission
from sentinelflow.security.throttle import Throttle
from sentinelflow.security.verifier import TokenVerifier

# auto_error=False so a missing token becomes our problem+json 401, not FastAPI's 403.
_BEARER = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)]


class Auth:
    """Builds route dependencies bound to one token service."""

    def __init__(
        self, tokens: TokenVerifier, recorder: AuditRecorder, throttle: Throttle | None = None
    ) -> None:
        """Verify tokens with ``tokens``; audit denials; rate-limit with ``throttle``."""
        self._tokens, self._recorder, self._throttle = tokens, recorder, throttle

    def current_principal(self, request: Request, credentials: Credentials) -> Principal:
        """Return the verified caller once its tenant is within its rate limit.

        Raises:
            AuthenticationError: If the bearer token is missing or invalid.
            RateLimitedError: If the caller's tenant sent too many requests.
        """
        if credentials is None:
            raise AuthenticationError("missing bearer token")
        principal = self._tokens.verify(credentials.credentials)
        request.state.tenant_id = principal.tenant_id  # for the access-log line
        if self._throttle is not None:
            # After verification: the tenant comes from a trusted token, never the request.
            self._throttle.check(principal.tenant_id, request.method, request.url.path)
        return principal

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
