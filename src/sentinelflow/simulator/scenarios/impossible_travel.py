"""Impossible travel: one user logs in from two distant countries minutes apart.

Unlike ``benign_travel`` both logins come from external, non-VPN addresses and the
second country is not one the user normally works from.
Expected: MEDIUM (base, no intel), TRUE_POSITIVE, force an MFA reset.
"""

from datetime import timedelta

from sentinelflow.domain.actions import ActionKind
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import UserContext
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import COUNTRIES, external_ip, pick_user
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData
from sentinelflow.simulator.scenarios._build import make_alert, make_event

_EXPECTED = Expectation(Severity.MEDIUM, Verdict.TRUE_POSITIVE, (ActionKind.FORCE_MFA_RESET,))


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate two logins from different countries; the alert names the second IP."""
    user, home_ip, away_ip = pick_user(ctx.rng), external_ip(ctx.rng), external_ip(ctx.rng)
    home, away = ctx.rng.sample(COUNTRIES, 2)
    start = ctx.clock.now()
    second = start + timedelta(minutes=ctx.rng.randint(5, 25))
    events = (
        make_event(ctx, start, "login_succeeded", Entities(user, home_ip), {"country": home}),
        make_event(ctx, second, "login_succeeded", Entities(user, away_ip), {"country": away}),
    )
    title = f"Logins from {home} and {away} within minutes"
    alert = make_alert(ctx, "impossible_travel", title, second, Entities(user, away_ip))
    seed = SeedData(users=(UserContext(user_id=user, usual_countries=(home,)),))
    return ScenarioOutput("impossible_travel", (alert,), events, seed, _EXPECTED)
