"""Tests for the severity scale."""

import pytest

from sentinelflow.domain.severity import Severity


def test_severities_are_ordered_from_info_to_critical() -> None:
    assert sorted(Severity, reverse=True)[0] is Severity.CRITICAL
    assert Severity.INFO < Severity.LOW < Severity.MEDIUM < Severity.HIGH < Severity.CRITICAL


@pytest.mark.parametrize("level", [-1, 5])
def test_out_of_range_level_is_rejected(level: int) -> None:
    with pytest.raises(ValueError, match="is not a valid Severity"):
        Severity(level)


def test_severity_prints_as_lowercase_name() -> None:
    assert str(Severity.HIGH) == "high"
