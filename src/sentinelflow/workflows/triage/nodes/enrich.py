"""Enrichment nodes: look up the incident's IP and user in parallel."""

from sentinelflow.workflows.triage.deps import TriageDeps
from sentinelflow.workflows.triage.state import Node, TriageInput, TriageUpdate


def make_lookup_ip(deps: TriageDeps) -> Node[TriageInput]:
    """Build the node that fetches threat intel for the incident's IP, if any."""

    def lookup_ip(state: TriageInput) -> TriageUpdate:
        ip = state["incident"].entities.ip
        return {"ip_reputation": None if ip is None else deps.intel.ip_reputation(ip)}

    return lookup_ip


def make_lookup_user(deps: TriageDeps) -> Node[TriageInput]:
    """Build the node that fetches directory facts for the incident's user, if any."""

    def lookup_user(state: TriageInput) -> TriageUpdate:
        user = state["incident"].entities.user
        return {"user": None if user is None else deps.identity.lookup_user(user)}

    return lookup_user
