"""Tests for the triage enrichment nodes."""

from sentinelflow.domain.enrichment import IpReputation, UserContext
from sentinelflow.workflows.triage.nodes.enrich import make_lookup_ip, make_lookup_user
from sentinelflow.workflows.triage.state import TriageInput
from tests.builders import an_alert, an_incident, some_entities
from tests.fakes.fake_identity import FakeIdentityProvider
from tests.fakes.fake_intel import FakeThreatIntel
from tests.unit.workflows.triage.helpers import deps_with

BAD = IpReputation(ip="203.0.113.9", score=95)
ALICE = UserContext(user_id="alice", is_privileged=True)


def _state(**entity_changes: str | None) -> TriageInput:
    entities = some_entities(**entity_changes)
    return {"incident": an_incident(entities=entities), "alert": an_alert(entities=entities)}


def test_lookup_ip_returns_reputation() -> None:
    node = make_lookup_ip(deps_with(intel=FakeThreatIntel([BAD])))
    assert node(_state()) == {"ip_reputation": BAD}


def test_lookup_ip_skips_provider_when_incident_has_no_ip() -> None:
    intel = FakeThreatIntel([BAD])
    assert make_lookup_ip(deps_with(intel=intel))(_state(ip=None)) == {"ip_reputation": None}
    assert intel.lookups == []


def test_lookup_user_returns_directory_facts() -> None:
    node = make_lookup_user(deps_with(identity=FakeIdentityProvider([ALICE])))
    assert node(_state()) == {"user": ALICE}


def test_lookup_user_skips_provider_when_incident_has_no_user() -> None:
    identity = FakeIdentityProvider([ALICE])
    assert make_lookup_user(deps_with(identity=identity))(_state(user=None)) == {"user": None}
    assert identity.lookups == []
