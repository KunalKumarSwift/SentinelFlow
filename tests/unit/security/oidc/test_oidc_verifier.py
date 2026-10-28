"""Keycloak access tokens: RS256 from the realm's JWKS, right issuer and audience, fresh."""

from datetime import timedelta

import jwt
import pytest

from sentinelflow.domain.errors import AuthenticationError
from sentinelflow.domain.principals import PrincipalKind
from sentinelflow.security.oidc.jwks import CachedJwks
from sentinelflow.security.oidc.verifier import OidcTokenVerifier
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.unit.security.oidc.keys import AUDIENCE, ISSUER, claims, jwks, token


def _verifier(clock: FakeClock | None = None) -> OidcTokenVerifier:
    clock = clock or FakeClock(T0)
    return OidcTokenVerifier(CachedJwks(lambda: jwks("k1"), clock), ISSUER, AUDIENCE, clock)


def test_valid_token_becomes_a_principal_with_known_roles_only() -> None:
    principal = _verifier().verify(token(claims()))
    assert (principal.subject, principal.tenant_id, principal.team) == (
        "f1e2d3c4",
        "acme",
        "soc-emea",
    )
    assert principal.roles == frozenset({"soc-analyst-l2"})
    assert principal.kind is PrincipalKind.USER


def test_the_system_orchestrator_role_cannot_be_granted_by_the_idp() -> None:
    forged = claims(realm_access={"roles": ["orchestrator", "soc-analyst-l1"]})
    assert _verifier().verify(token(forged)).roles == frozenset({"soc-analyst-l1"})


def test_service_account_tokens_are_service_principals() -> None:
    service = claims(client_id="siem-connector", realm_access={"roles": ["alert-source"]})
    assert _verifier().verify(token(service)).kind is PrincipalKind.SERVICE


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (claims(iss="http://evil/realms/sentinelflow"), "issuer"),
        (claims(aud="another-client"), "audience"),
        (claims(exp=int(T0.timestamp()) - 1), "expired"),
        (claims(tenant_id=None), "tenant_id"),
        (claims(exp=int(T0.timestamp()) + 7200), "lifetime"),
        (claims(iat="yesterday"), "integers"),
    ],
)
def test_invalid_claims_are_rejected(payload: dict[str, object], reason: str) -> None:
    with pytest.raises(AuthenticationError, match=reason):
        _verifier().verify(token(payload))


def test_token_signed_by_an_unpublished_key_is_rejected() -> None:
    with pytest.raises(AuthenticationError, match="signing key"):
        _verifier().verify(token(claims(), kid="rogue"))


def test_hs256_and_unsigned_tokens_are_rejected() -> None:
    hs = jwt.encode(claims(), "x" * 32, algorithm="HS256", headers={"kid": "k1"})
    unsigned = jwt.encode(claims(), "", algorithm="none", headers={"kid": "k1"})
    for bad in (hs, unsigned, "not-a-jwt"):
        with pytest.raises(AuthenticationError):
            _verifier().verify(bad)


def test_expiry_follows_the_injected_clock() -> None:
    clock = FakeClock(T0)
    verifier, signed = _verifier(clock), token(claims())
    verifier.verify(signed)
    clock.advance(timedelta(seconds=300))
    with pytest.raises(AuthenticationError, match="expired"):
        verifier.verify(signed)


@pytest.mark.parametrize("access", [None, "admin", {"roles": "soc-analyst-l2"}])
def test_malformed_role_claims_grant_nothing(access: object) -> None:
    assert _verifier().verify(token(claims(realm_access=access))).roles == frozenset()
