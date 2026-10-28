"""Brute force: many failed logins from one malicious IP, then a success.

Expected: HIGH (base MEDIUM + malicious IP), TRUE_POSITIVE.
"""

from datetime import datetime, timedelta

from sentinelflow.domain.actions import ActionKind as K
from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.enrichment import IpReputation, UserContext
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import DEPARTMENTS, external_ip, pick_user, spread
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData

RULE_ID = "brute_force_success"


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate one brute-force attack against a random user."""
    entities = Entities(user=pick_user(ctx.rng), ip=external_ip(ctx.rng))
    failures = ctx.rng.randint(30, 60)
    times = spread(ctx.clock.now(), failures + 1, timedelta(seconds=ctx.rng.randint(2, 5)))
    kinds = ["login_failed"] * failures + ["login_succeeded"]
    events = tuple(_login(ctx, at, kind, entities) for at, kind in zip(times, kinds, strict=True))
    alert = Alert(
        id=ctx.ids.new_id("alt"),
        tenant_id=ctx.tenant_id,
        source="simulator",
        rule_id=RULE_ID,
        title="Successful login after repeated failures",
        observed_at=times[-1] + timedelta(seconds=30),
        entities=entities,
        raw={"failed_attempts": str(failures)},
    )
    return ScenarioOutput("brute_force", (alert,), events, _seed(ctx, entities), _EXPECTED)


_EXPECTED = Expectation(Severity.HIGH, Verdict.TRUE_POSITIVE, (K.DISABLE_USER, K.BLOCK_IP))


def _login(ctx: ScenarioContext, at: datetime, kind: str, entities: Entities) -> SecurityEvent:
    return SecurityEvent(
        id=ctx.ids.new_id("evt"),
        tenant_id=ctx.tenant_id,
        at=at,
        kind=kind,
        entities=entities,
        attributes={"user_agent": "python-requests/2.32"},
    )


def _seed(ctx: ScenarioContext, entities: Entities) -> SeedData:
    user = UserContext(user_id=entities.user or "", department=ctx.rng.choice(DEPARTMENTS))
    ip = entities.ip or ""
    rep = IpReputation(ip=ip, score=ctx.rng.randint(85, 100), categories=("brute-force",))
    return SeedData(users=(user,), ip_reputations=(rep,))
