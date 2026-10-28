"""Tests for enrichment value objects."""

import pytest

from sentinelflow.domain.enrichment import Enrichment, IpReputation, UserContext
from sentinelflow.domain.errors import InvalidValueError


@pytest.mark.parametrize("score", [-1, 101])
def test_ip_reputation_score_must_be_0_to_100(score: int) -> None:
    with pytest.raises(InvalidValueError, match="score"):
        IpReputation(ip="203.0.113.9", score=score)


def test_ip_reputation_flags_malicious_from_80() -> None:
    assert IpReputation(ip="203.0.113.9", score=80).is_malicious is True
    assert IpReputation(ip="203.0.113.9", score=79).is_malicious is False


def test_empty_enrichment_has_no_signals() -> None:
    assert Enrichment() == Enrichment(ip_reputation=None, user=None)


def test_user_context_defaults_to_unprivileged() -> None:
    assert UserContext(user_id="alice").is_privileged is False
