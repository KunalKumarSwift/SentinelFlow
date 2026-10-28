"""Fakes record their calls so tests can assert what a node looked up."""

from sentinelflow.domain.actions import ActionKind, ProposedAction
from sentinelflow.domain.enrichment import UserContext
from tests.fakes.fake_identity import FakeIdentityProvider
from tests.fakes.fake_intel import FakeThreatIntel


def test_fake_intel_records_lookups() -> None:
    intel = FakeThreatIntel([])
    intel.ip_reputation("203.0.113.9")
    assert intel.lookups == ["203.0.113.9"]


def test_fake_identity_records_lookups() -> None:
    identity = FakeIdentityProvider([UserContext(user_id="alice")])
    identity.lookup_user("alice")
    assert identity.lookups == ["alice"]


def test_fake_identity_records_each_applied_action_once() -> None:
    identity = FakeIdentityProvider([])
    action = ProposedAction("inc-1:block_ip", "inc-1", ActionKind.BLOCK_IP, "203.0.113.9", "r", "s")
    identity.apply(action, "k1")
    identity.apply(action, "k1")
    assert identity.applied == [action]
