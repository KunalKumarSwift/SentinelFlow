"""Shape and expected outcome of each attack scenario."""

import pytest

from sentinelflow.domain.actions import ActionKind as K
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity as Sev
from sentinelflow.simulator.registry import SCENARIOS
from tests.unit.simulator.conftest import make_context

TP = Verdict.TRUE_POSITIVE

CASES = [
    ("impossible_travel", "impossible_travel", {"user", "ip"}, Sev.MEDIUM, (K.FORCE_MFA_RESET,)),
    (
        "leaked_key",
        "access_key_anomaly",
        {"user", "ip", "access_key_id"},
        Sev.CRITICAL,
        (K.REVOKE_ACCESS_KEY,),
    ),
    (
        "phishing",
        "phishing_click",
        {"user", "url", "email_id"},
        Sev.MEDIUM,
        (K.PURGE_EMAIL, K.RESET_PASSWORD),
    ),
    ("powershell", "suspicious_process", {"user", "host"}, Sev.HIGH, (K.ISOLATE_HOST,)),
    ("exfiltration", "large_download", {"user", "ip"}, Sev.HIGH, ()),
]


@pytest.mark.parametrize(("name", "rule", "entities", "severity", "actions"), CASES)
def test_scenario_alert_and_expectation(
    name: str, rule: str, entities: set[str], severity: Sev, actions: tuple[K, ...]
) -> None:
    out = SCENARIOS[name](make_context())
    alert = out.alerts[0]
    assert (alert.rule_id, set(alert.entities.present())) == (rule, entities)
    assert (out.expected.severity, out.expected.verdict, out.expected.actions) == (
        severity,
        TP,
        actions,
    )


@pytest.mark.parametrize(
    ("name", "kinds"),
    [
        ("impossible_travel", {"login_succeeded"}),
        ("leaked_key", {"ListBuckets", "GetObject"}),
        ("phishing", {"email_received", "url_clicked"}),
        ("powershell", {"process_started", "outbound_connection"}),
        ("exfiltration", {"large_download"}),
    ],
)
def test_scenario_events(name: str, kinds: set[str]) -> None:
    events = SCENARIOS[name](make_context()).events
    assert {e.kind for e in events} == kinds


def test_travel_logins_come_from_different_external_countries() -> None:
    events = SCENARIOS["impossible_travel"](make_context()).events
    assert events[0].attributes["country"] != events[1].attributes["country"]
    assert all(e.entities.ip is not None and e.entities.ip.startswith("203.0.113.") for e in events)


def test_exfiltration_is_large_and_off_hours() -> None:
    [event] = SCENARIOS["exfiltration"](make_context()).events
    assert int(event.attributes["bytes"]) >= 10 * 1024**3 and event.at.hour == 3
