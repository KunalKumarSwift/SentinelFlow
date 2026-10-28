"""Phishing: a user receives a credential-harvesting e-mail and clicks its link.

Expected: MEDIUM (base, no IP signal), TRUE_POSITIVE, purge the e-mail and reset the
user's password.
"""

from datetime import timedelta

from sentinelflow.domain.actions import ActionKind as K
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import UserContext
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import DEPARTMENTS, lure_url, message_id, pick_user
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData
from sentinelflow.simulator.scenarios._build import make_alert, make_event

_EXPECTED = Expectation(Severity.MEDIUM, Verdict.TRUE_POSITIVE, (K.PURGE_EMAIL, K.RESET_PASSWORD))


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate the delivery of a lure and the user's click a few minutes later."""
    entities = Entities(
        user=pick_user(ctx.rng), url=lure_url(ctx.rng), email_id=message_id(ctx.rng)
    )
    received = ctx.clock.now()
    clicked = received + timedelta(minutes=ctx.rng.randint(1, 30))
    subject = {"subject": "Your mailbox is full - verify your account"}
    events = (
        make_event(ctx, received, "email_received", entities, subject),
        make_event(ctx, clicked, "url_clicked", entities, {"browser": "Edge"}),
    )
    alert = make_alert(ctx, "phishing_click", "User clicked a phishing link", clicked, entities)
    user = UserContext(user_id=entities.user or "", department=ctx.rng.choice(DEPARTMENTS))
    return ScenarioOutput("phishing", (alert,), events, SeedData(users=(user,)), _EXPECTED)
