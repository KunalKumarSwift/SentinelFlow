"""Malicious PowerShell: an encoded command starts on a workstation and calls out.

Expected: HIGH (base, no IP on the alert), TRUE_POSITIVE, isolate the host.
"""

from datetime import timedelta

from sentinelflow.domain.actions import ActionKind
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.enrichment import UserContext
from sentinelflow.domain.incidents import Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.factories import external_ip, host_name, pick_user
from sentinelflow.simulator.output import Expectation, ScenarioOutput, SeedData
from sentinelflow.simulator.scenarios._build import make_alert, make_event

_EXPECTED = Expectation(Severity.HIGH, Verdict.TRUE_POSITIVE, (ActionKind.ISOLATE_HOST,))

COMMAND = "powershell.exe -NoProfile -WindowStyle Hidden -EncodedCommand SQBFAFgA..."


def generate(ctx: ScenarioContext) -> ScenarioOutput:
    """Generate the process start and its outbound beacon."""
    entities = Entities(user=pick_user(ctx.rng), host=host_name(ctx.rng))
    started = ctx.clock.now()
    beacon = started + timedelta(seconds=ctx.rng.randint(2, 20))
    events = (
        make_event(ctx, started, "process_started", entities, {"command_line": COMMAND}),
        make_event(ctx, beacon, "outbound_connection", entities, {"dest": external_ip(ctx.rng)}),
    )
    title = "Encoded PowerShell command followed by an outbound connection"
    alert = make_alert(ctx, "suspicious_process", title, beacon, entities)
    seed = SeedData(users=(UserContext(user_id=entities.user or ""),))
    return ScenarioOutput("powershell", (alert,), events, seed, _EXPECTED)
