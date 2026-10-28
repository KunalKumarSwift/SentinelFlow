"""Tests for health checks and the dev-only token endpoint."""

from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.domain.principals import PrincipalKind
from sentinelflow.security.tokens import Hs256TokenService
from tests.api.conftest import make_container

DEV_USER = {
    "subject": "u-alice",
    "tenant_id": "acme",
    "team": "soc-emea",
    "roles": ["soc-analyst-l1"],
    "kind": "user",
}


def test_healthz_is_public(client: TestClient) -> None:
    response = client.get("/healthz")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})


def test_dev_token_round_trips_in_dev(client: TestClient, tokens: Hs256TokenService) -> None:
    response = client.post("/v1/auth/dev-token", json=DEV_USER)
    assert response.status_code == 200
    principal = tokens.verify(response.json()["access_token"])
    assert (principal.subject, principal.roles) == ("u-alice", frozenset({"soc-analyst-l1"}))
    assert principal.kind is PrincipalKind.USER


def test_dev_token_endpoint_does_not_exist_outside_dev(tokens: Hs256TokenService) -> None:
    client = TestClient(create_app(make_container(tokens, app_env="prod")))
    assert client.post("/v1/auth/dev-token", json=DEV_USER).status_code == 404


def test_dev_token_rejects_invalid_body(client: TestClient) -> None:
    response = client.post("/v1/auth/dev-token", json={**DEV_USER, "kind": "root"})
    assert response.status_code == 422
