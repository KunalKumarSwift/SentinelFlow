"""Incident responses hide PII from roles without incident:read_pii."""

from fastapi.testclient import TestClient

from tests.api.conftest import TokenFor
from tests.api.payloads import ALERT


def _user(client: TestClient, auth: TokenFor, role: str) -> str:
    body = client.get("/v1/incidents/inc-0001", headers=auth(role)).json()
    return str(body["entities"]["user"])


def test_l1_sees_pseudonym_l2_sees_user(client: TestClient, auth: TokenFor) -> None:
    client.post("/v1/alerts", json=ALERT, headers=auth("alert-source"))
    assert _user(client, auth, "soc-analyst-l2") == "alice"
    pseudonym = _user(client, auth, "soc-analyst-l1")
    assert pseudonym.startswith("user-") and pseudonym != "alice"
    listed = client.get("/v1/incidents", headers=auth("soc-analyst-l1")).json()["items"]
    assert listed[0]["entities"]["user"] == pseudonym
