"""Shared constructors for scenario alerts and events, so scenarios stay declarative."""

from collections.abc import Mapping
from datetime import datetime

from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.events import SecurityEvent
from sentinelflow.simulator.context import ScenarioContext


def make_alert(
    ctx: ScenarioContext, rule_id: str, title: str, at: datetime, entities: Entities
) -> Alert:
    """Return a simulator alert for ``rule_id`` observed at ``at``."""
    return Alert(
        id=ctx.ids.new_id("alt"),
        tenant_id=ctx.tenant_id,
        source="simulator",
        rule_id=rule_id,
        title=title,
        observed_at=at,
        entities=entities,
    )


def make_event(
    ctx: ScenarioContext, at: datetime, kind: str, entities: Entities, attributes: Mapping[str, str]
) -> SecurityEvent:
    """Return one raw security event for the scenario's tenant."""
    return SecurityEvent(
        id=ctx.ids.new_id("evt"),
        tenant_id=ctx.tenant_id,
        at=at,
        kind=kind,
        entities=entities,
        attributes=attributes,
    )
