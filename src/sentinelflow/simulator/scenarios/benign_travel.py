"""Benign "impossible travel": a user's two logins look far apart, but both use VPN.

Expected: LOW (base MEDIUM, internal IP, unprivileged user), FALSE_POSITIVE.
"""

from datetime import datetime, timedelta

from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.enrichment import UserContext
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import COUNTRIES, pick_user, vpn_egress_ip
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData

RULE_ID = "impossible_travel"


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate two VPN logins whose geo-IP countries differ."""
    entities = Entities(user=pick_user(ctx.rng), ip=vpn_egress_ip(ctx.rng))
    home, away = ctx.rng.sample(COUNTRIES, 2)
    start = ctx.clock.now()
    second = start + timedelta(minutes=ctx.rng.randint(5, 25))
    events = (_login(ctx, start, home, entities), _login(ctx, second, away, entities))
    alert = Alert(
        id=ctx.ids.new_id("alt"),
        tenant_id=ctx.tenant_id,
        source="simulator",
        rule_id=RULE_ID,
        title=f"Logins from {home} and {away} within minutes",
        observed_at=second + timedelta(seconds=30),
        entities=entities,
        raw={"countries": f"{home},{away}"},
    )
    user = UserContext(user_id=entities.user or "", usual_countries=(home, away))
    seed = SeedData(users=(user,))
    return ScenarioOutput("benign_travel", (alert,), events, seed, _EXPECTED)


_EXPECTED = Expectation(severity=Severity.LOW, verdict=Verdict.FALSE_POSITIVE)


def _login(ctx: ScenarioContext, at: datetime, country: str, entities: Entities) -> SecurityEvent:
    return SecurityEvent(
        id=ctx.ids.new_id("evt"),
        tenant_id=ctx.tenant_id,
        at=at,
        kind="login_succeeded",
        entities=entities,
        attributes={"country": country, "via": "corporate-vpn"},
    )
