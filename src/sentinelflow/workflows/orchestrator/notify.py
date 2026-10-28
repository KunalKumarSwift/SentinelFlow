"""Tell approvers that a run is waiting for them, without ever failing the run."""

from sentinelflow.domain.errors import ProviderError
from sentinelflow.domain.incidents import Incident
from sentinelflow.domain.notification import approval_request_message
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.workflows.orchestrator.deps import LifecycleDeps

CHANNEL = "approvals"


def notify_approvers(deps: LifecycleDeps, incident: Incident, approval_ids: list[str]) -> None:
    """Send one message listing the pending approvals; a delivery failure is only audited.

    A chat outage must not stop containment: approvers still see the approvals inbox.
    """
    if deps.notifier is None or not approval_ids:
        return
    approvals = [a for i in approval_ids if (a := deps.approvals.get(incident.tenant_id, i))]
    try:
        deps.notifier.notify(CHANNEL, approval_request_message(incident, approvals))
    except ProviderError as error:
        details = {"channel": CHANNEL, "error": type(error).__name__}
        system = orchestrator_for(incident.tenant_id)
        deps.recorder.record(system, "notification.failed", incident.id, details)
