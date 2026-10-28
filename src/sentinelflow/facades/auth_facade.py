"""Choose how bearer tokens are verified. Switch logic only."""

from sentinelflow.core.clock import Clock
from sentinelflow.core.config import Settings
from sentinelflow.security.verifier import TokenVerifier


def make_verifier(settings: Settings, clock: Clock) -> TokenVerifier | None:
    """Return the OIDC verifier for ``AUTH_MODE=oidc``; ``None`` keeps HS256 dev tokens."""
    if settings.auth_mode != "oidc" or not settings.oidc_issuer:
        return None
    from sentinelflow.providers.identity.jwks_http import HttpJwksFetcher
    from sentinelflow.security.oidc.jwks import CachedJwks
    from sentinelflow.security.oidc.verifier import OidcTokenVerifier

    issuer = settings.oidc_issuer.rstrip("/")
    url = settings.oidc_jwks_url or f"{issuer}/protocol/openid-connect/certs"
    keys = CachedJwks(HttpJwksFetcher(url), clock)
    return OidcTokenVerifier(keys, issuer, settings.oidc_audience, clock)
