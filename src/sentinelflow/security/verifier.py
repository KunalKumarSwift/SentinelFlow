"""What the API needs from any bearer-token scheme: turn a token into a principal."""

from typing import Protocol

from sentinelflow.domain.principals import Principal


class TokenVerifier(Protocol):
    """Verifies bearer tokens (HS256 dev tokens or OIDC access tokens)."""

    def verify(self, token: str) -> Principal:
        """Return the principal ``token`` represents.

        Raises:
            AuthenticationError: If the token is not valid for this API.
        """
        ...
