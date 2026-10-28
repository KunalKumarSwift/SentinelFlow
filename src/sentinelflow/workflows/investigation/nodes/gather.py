"""Gathering nodes: fetch related events, then build the timeline and technique candidates."""

from datetime import timedelta

from sentinelflow.contracts.event_store import EventQuery
from sentinelflow.domain.attack import candidate_techniques
from sentinelflow.domain.timeline import build_timeline
from sentinelflow.workflows.investigation.deps import InvestigationDeps
from sentinelflow.workflows.investigation.state import (
    InvestigationInput,
    InvestigationUpdate,
    Node,
    SummarizeInput,
)

WINDOW = timedelta(hours=24)


def make_fetch(deps: InvestigationDeps) -> Node[InvestigationInput]:
    """Build the node that loads events sharing an entity with the incident (±24 h)."""

    def fetch(state: InvestigationInput) -> InvestigationUpdate:
        incident, at = state["incident"], state["alert"].observed_at
        query = EventQuery(incident.tenant_id, incident.entities, at - WINDOW, at + WINDOW)
        return {"events": tuple(deps.events.related_events(query))}

    return fetch


def summarize(state: SummarizeInput) -> InvestigationUpdate:
    """Build the timeline and retrieve ATT&CK candidates from rule and event kinds."""
    events = state["events"]
    kinds = [e.kind for e in events]
    return {
        "timeline": build_timeline(events),
        "candidates": candidate_techniques(state["alert"].rule_id, kinds),
    }
