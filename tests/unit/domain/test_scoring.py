"""Tests for incident severity scoring."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import Enrichment, IpReputation, UserContext
from sentinelflow.domain.errors import UnknownRuleError
from sentinelflow.domain.scoring import score_severity
from sentinelflow.domain.scoring_table import RULE_BASE_SEVERITY
from sentinelflow.domain.severity import Severity

EXTERNAL = Entities(user="alice", ip="203.0.113.9")
INTERNAL = Entities(user="alice", ip="10.0.0.5")
BAD_IP = IpReputation(ip="203.0.113.9", score=95)
CLEAN_IP = IpReputation(ip="203.0.113.9", score=5)
ADMIN = UserContext(user_id="alice", is_privileged=True)


@pytest.mark.parametrize(
    ("rule_id", "entities", "enrichment", "expected"),
    [
        ("brute_force_success", EXTERNAL, Enrichment(), Severity.MEDIUM),
        ("brute_force_success", EXTERNAL, Enrichment(ip_reputation=BAD_IP), Severity.HIGH),
        ("brute_force_success", EXTERNAL, Enrichment(ip_reputation=CLEAN_IP), Severity.MEDIUM),
        ("brute_force_success", EXTERNAL, Enrichment(BAD_IP, ADMIN), Severity.CRITICAL),
        ("impossible_travel", INTERNAL, Enrichment(), Severity.LOW),
        ("impossible_travel", INTERNAL, Enrichment(user=ADMIN), Severity.HIGH),
        ("access_key_anomaly", EXTERNAL, Enrichment(BAD_IP, ADMIN), Severity.CRITICAL),
        ("dormant_account", Entities(user="bob"), Enrichment(), Severity.LOW),
    ],
)
def test_score_severity(
    rule_id: str, entities: Entities, enrichment: Enrichment, expected: Severity
) -> None:
    assert score_severity(rule_id, entities, enrichment) is expected


def test_unknown_rule_is_rejected() -> None:
    with pytest.raises(UnknownRuleError, match="no_such_rule"):
        score_severity("no_such_rule", EXTERNAL, Enrichment())


def test_malformed_ip_is_treated_as_external() -> None:
    weird = Entities(user="alice", ip="not-an-ip")
    assert score_severity("impossible_travel", weird, Enrichment()) is Severity.MEDIUM


rules = st.sampled_from(sorted(RULE_BASE_SEVERITY))
ips = st.sampled_from(["203.0.113.9", "10.0.0.5", None])
scores = st.integers(0, 100)


@given(rule_id=rules, ip=ips, score=scores, privileged=st.booleans())
def test_malicious_ip_never_lowers_severity(
    rule_id: str, ip: str | None, score: int, privileged: bool
) -> None:
    entities = Entities(user="alice", ip=ip)
    user = UserContext(user_id="alice", is_privileged=privileged)
    without = score_severity(rule_id, entities, Enrichment(user=user))
    rep = IpReputation(ip=ip or "203.0.113.9", score=score)
    assert score_severity(rule_id, entities, Enrichment(rep, user)) >= without


@pytest.mark.parametrize("ip", ["192.0.2.10", "198.51.100.7", "203.0.113.9", "8.8.8.8"])
def test_documentation_and_public_ranges_count_as_external(ip: str) -> None:
    entities = Entities(user="alice", ip=ip)
    assert score_severity("impossible_travel", entities, Enrichment()) is Severity.MEDIUM


@pytest.mark.parametrize("ip", ["10.1.2.3", "172.20.0.1", "192.168.1.1", "fd00::1"])
def test_private_ranges_count_as_internal(ip: str) -> None:
    entities = Entities(user="alice", ip=ip)
    assert score_severity("impossible_travel", entities, Enrichment()) is Severity.LOW
