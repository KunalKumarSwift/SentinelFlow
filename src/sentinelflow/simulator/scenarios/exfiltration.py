"""Data exfiltration: a user downloads tens of gigabytes at 3 a.m. to an external IP.

The playbook has no automatic containment for this rule (cutting off a user over a
download needs a human judgement call), so the incident is escalated to an analyst.
Expected: HIGH (base, clean IP), TRUE_POSITIVE, no proposed actions.
"""

from datetime import timedelta

from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import UserContext
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import DEPARTMENTS, external_ip, pick_user
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData
from sentinelflow.simulator.scenarios._build import make_alert, make_event

_EXPECTED = Expectation(Severity.HIGH, Verdict.TRUE_POSITIVE)

GIB = 1024**3


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate one large off-hours download."""
    entities = Entities(user=pick_user(ctx.rng), ip=external_ip(ctx.rng))
    at = ctx.clock.now().replace(hour=3, minute=ctx.rng.randint(0, 59))
    size = ctx.rng.randint(10, 60) * GIB
    attributes = {"bytes": str(size), "share": "finance-archive"}
    events = (make_event(ctx, at, "large_download", entities, attributes),)
    title = f"{size // GIB} GiB downloaded outside working hours"
    alert = make_alert(ctx, "large_download", title, at + timedelta(minutes=5), entities)
    user = UserContext(user_id=entities.user or "", department=ctx.rng.choice(DEPARTMENTS))
    return ScenarioOutput("exfiltration", (alert,), events, SeedData(users=(user,)), _EXPECTED)
