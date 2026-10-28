"""HS256 dev tokens by default; an OIDC verifier when AUTH_MODE=oidc."""

from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.auth_facade import make_verifier
from sentinelflow.security.oidc.verifier import OidcTokenVerifier
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock

SECRET = SecretStr("s" * 32)


def test_default_mode_keeps_dev_tokens() -> None:
    assert make_verifier(Settings(jwt_secret=SECRET), FakeClock(T0)) is None  # type: ignore[call-arg]


def test_oidc_mode_builds_a_keycloak_verifier() -> None:
    settings = Settings(  # type: ignore[call-arg]
        jwt_secret=SECRET, auth_mode="oidc", oidc_issuer="http://kc:8080/realms/sentinelflow/"
    )
    assert isinstance(make_verifier(settings, FakeClock(T0)), OidcTokenVerifier)
