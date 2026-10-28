"""Tests for bearer authentication, permission checks and error mapping."""

from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.api.auth import Auth
from sentinelflow.domain.errors import (
    InvalidTransitionError,
    InvalidValueError,
    NotFoundError,
    ProviderError,
    SentinelFlowError,
)
from sentinelflow.domain.principals import Principal
from sentinelflow.security.audit_recorder import AuditRecorder
from sentinelflow.security.permissions import Permission
from sentinelflow.security.tokens import Hs256TokenService
from tests.api.conftest import TokenFor, make_container


@pytest.fixture
def probe(tokens: Hs256TokenService) -> TestClient:
    """App with extra routes that exercise auth and error mapping."""
    container = make_container(tokens)
    app = create_app(container)
    recorder = AuditRecorder(container.audit, container.clock)
    ingest = Auth(tokens, recorder).require(Permission.ALERT_INGEST)

    @app.get("/probe")
    def probe_route(principal: Annotated[Principal, Depends(ingest)]) -> dict[str, str]:
        return {"subject": principal.subject}

    errors: dict[str, SentinelFlowError] = {
        "missing": NotFoundError("no such thing"),
        "bad": InvalidValueError("bad"),
        "conflict": InvalidTransitionError("closed"),
        "provider": ProviderError("llm down", retryable=True),
        "unmapped": SentinelFlowError("internal detail"),
    }

    @app.get("/boom/{kind}")
    def boom(kind: str) -> None:
        raise errors[kind]

    return TestClient(app)


def test_missing_token_is_401_problem(probe: TestClient) -> None:
    response = probe.get("/probe")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Unauthorized"


def test_garbage_token_is_401(probe: TestClient) -> None:
    assert probe.get("/probe", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_missing_permission_is_403_with_reason(probe: TestClient, auth: TokenFor) -> None:
    response = probe.get("/probe", headers=auth("soc-analyst-l1"))
    assert response.status_code == 403
    assert response.json()["detail"] == "missing permission alert:ingest"


def test_granted_permission_passes_principal(probe: TestClient, auth: TokenFor) -> None:
    response = probe.get("/probe", headers=auth("alert-source", kind="service"))
    assert (response.status_code, response.json()) == (200, {"subject": "u-1"})


@pytest.mark.parametrize(
    ("kind", "status"),
    [("missing", 404), ("bad", 422), ("conflict", 409), ("provider", 503), ("unmapped", 500)],
)
def test_domain_errors_map_to_status(probe: TestClient, kind: str, status: int) -> None:
    response = probe.get(f"/boom/{kind}")
    assert (response.status_code, response.json()["status"]) == (status, status)


def test_unmapped_error_does_not_leak_its_message(probe: TestClient) -> None:
    assert probe.get("/boom/unmapped").json()["detail"] == "unexpected error"
