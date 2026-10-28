"""Tests for GET /v1/audit and GET /v1/audit/verify, and what the API records."""

from collections.abc import Sequence
from dataclasses import replace

from fastapi.testclient import TestClient

from sentinelflow.api.app import create_app
from sentinelflow.api.container import ApiContainer
from sentinelflow.domain.audit import AuditEvent
from sentinelflow.providers.storage.memory_audit import MemoryAuditStore
from tests.api.conftest import TokenFor
from tests.api.payloads import ALERT


def _verbs(client: TestClient, auth: TokenFor) -> list[str]:
    items = client.get("/v1/audit", headers=auth("auditor")).json()["items"]
    return [e["verb"] for e in items]


def test_ingestion_and_queueing_are_recorded(client: TestClient, auth: TokenFor) -> None:
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source", kind="service"))
    assert _verbs(client, auth) == ["alert.ingested", "run.queued"]


def test_policy_denials_are_recorded(client: TestClient, auth: TokenFor) -> None:
    client.post("/v1/alerts", json=ALERT, headers=auth("soc-analyst-l1"))
    items = client.get("/v1/audit", headers=auth("auditor")).json()["items"]
    assert (items[0]["verb"], items[0]["outcome"], items[0]["details"]["permission"]) == (
        "policy.denied",
        "denied",
        "alert:ingest",
    )


def test_analyst_cannot_read_audit(client: TestClient, auth: TokenFor) -> None:
    assert client.get("/v1/audit", headers=auth("soc-analyst-l2")).status_code == 403


def test_audit_is_per_tenant(client: TestClient, auth: TokenFor) -> None:
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source", tenant="globex"))
    assert _verbs(client, auth) == []


def test_verify_reports_intact_chain(client: TestClient, auth: TokenFor) -> None:
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source"))
    body = client.get("/v1/audit/verify", headers=auth("auditor")).json()
    assert body == {"ok": True, "first_bad_seq": None, "checked": 2}


class TamperedAuditStore(MemoryAuditStore):
    """Returns the first event with an edited outcome, as a DB-level edit would."""

    def read(self, tenant_id: str, after_seq: int, limit: int) -> Sequence[AuditEvent]:
        events = list(super().read(tenant_id, after_seq, limit))
        if events and events[0].seq == 1:
            events[0] = replace(events[0], outcome="tampered")
        return events


def test_verify_detects_tampering(container: ApiContainer, auth: TokenFor) -> None:
    client = TestClient(create_app(replace(container, audit=TamperedAuditStore())))
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source"))
    body = client.get("/v1/audit/verify", headers=auth("auditor")).json()
    assert (body["ok"], body["first_bad_seq"]) == (False, 1)
