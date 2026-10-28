"""With an OIDC verifier configured, the API accepts Keycloak tokens and refuses dev tokens."""

from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.domain.principals import Principal
from sentinelflow.security.oidc.jwks import CachedJwks
from sentinelflow.security.oidc.verifier import OidcTokenVerifier
from sentinelflow.security.tokens import Hs256TokenService
from tests.api.conftest import make_container
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.unit.security.oidc.keys import AUDIENCE, ISSUER, claims, jwks, token


def _client(tokens: Hs256TokenService) -> TestClient:
    clock = FakeClock(T0)
    verifier = OidcTokenVerifier(CachedJwks(lambda: jwks("k1"), clock), ISSUER, AUDIENCE, clock)
    container = make_container(tokens, app_env="prod", verifier=verifier)
    return TestClient(create_app(container))


def test_keycloak_token_is_accepted(tokens: Hs256TokenService) -> None:
    headers = {"Authorization": f"Bearer {token(claims())}"}
    assert _client(tokens).get("/v1/incidents", headers=headers).status_code == 200


def test_locally_signed_dev_token_is_refused(tokens: Hs256TokenService) -> None:
    dev = tokens.issue(Principal("u-1", "acme", "soc-emea", frozenset({"soc-analyst-l2"})))
    response = _client(tokens).get("/v1/incidents", headers={"Authorization": f"Bearer {dev}"})
    assert response.status_code == 401
