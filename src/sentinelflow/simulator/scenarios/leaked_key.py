"""Leaked cloud key: a developer's access key is used from a known-malicious IP.

Expected: CRITICAL (base HIGH + malicious IP), TRUE_POSITIVE, revoke the key, which
is a high-impact action on a critical incident and so needs two incident commanders.
"""

from datetime import timedelta

from sentinelflow.domain.actions import ActionKind
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import IpReputation, UserContext
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import access_key_id, external_ip, pick_user, spread
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData
from sentinelflow.simulator.scenarios._build import make_alert, make_event

_EXPECTED = Expectation(Severity.CRITICAL, Verdict.TRUE_POSITIVE, (ActionKind.REVOKE_ACCESS_KEY,))


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate bucket enumeration followed by object reads with a stolen key."""
    user, ip = pick_user(ctx.rng), external_ip(ctx.rng)
    entities = Entities(user=user, ip=ip, access_key_id=access_key_id(ctx.rng))
    reads = ctx.rng.randint(20, 40)
    times = spread(ctx.clock.now(), reads + 1, timedelta(seconds=ctx.rng.randint(1, 3)))
    kinds = ["ListBuckets"] + ["GetObject"] * reads
    agent = {"user_agent": "aws-cli/2.15 (unusual for this key)"}
    events = tuple(
        make_event(ctx, t, k, entities, agent) for t, k in zip(times, kinds, strict=True)
    )
    title = "Access key used from a new, malicious network"
    alert = make_alert(ctx, "access_key_anomaly", title, times[-1], entities)
    rep = IpReputation(ip=ip, score=ctx.rng.randint(85, 100), categories=("tor",))
    seed = SeedData((UserContext(user_id=user, department="engineering"),), (rep,))
    return ScenarioOutput("leaked_key", (alert,), events, seed, _EXPECTED)
