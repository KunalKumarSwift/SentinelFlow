"""Nodes: list accounts → review them → raise one alert per finding still unhandled."""

from sentinelflow.domain.access_review import Finding, review_accounts
from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.dedup import fingerprint_alert
from sentinelflow.domain.incidents import IncidentStatus
from sentinelflow.workflows.access_review.deps import AccessReviewDeps
from sentinelflow.workflows.access_review.state import (
    AccountsInput,
    FindingsInput,
    Node,
    ReviewState,
    TenantInput,
)


def make_list_accounts(deps: AccessReviewDeps) -> Node[TenantInput]:
    """Return the node that loads the tenant's accounts."""

    def list_accounts(state: TenantInput) -> ReviewState:
        return {"accounts": tuple(deps.directory.list_accounts(state["tenant_id"]))}

    return list_accounts


def make_review(deps: AccessReviewDeps) -> Node[AccountsInput]:
    """Return the node that applies the review rules."""

    def review(state: AccountsInput) -> ReviewState:
        return {"findings": review_accounts(state["accounts"], deps.clock.now())}

    return review


def make_raise_findings(deps: AccessReviewDeps) -> Node[FindingsInput]:
    """Return the node that ingests each new finding as an alert."""

    def raise_findings(state: FindingsInput) -> ReviewState:
        alerts = (_alert(deps, state["tenant_id"], f) for f in state["findings"])
        fresh = [a for a in alerts if not _still_open(deps, a)]
        return {"new_incidents": tuple(deps.ingestion.ingest(a).incident for a in fresh)}

    return raise_findings


def _alert(deps: AccessReviewDeps, tenant_id: str, finding: Finding) -> Alert:
    return Alert(
        id=deps.ids.new_id("alt"),
        tenant_id=tenant_id,
        source="access-review",
        rule_id=finding.rule_id,
        title=f"Access review: {finding.user_id}: {finding.reason}",
        observed_at=deps.clock.now(),
        entities=Entities(user=finding.user_id),
        raw={"reason": finding.reason},
    )


def _still_open(deps: AccessReviewDeps, alert: Alert) -> bool:
    # A daily review must not reopen yesterday's finding while it is still being handled.
    previous = deps.alerts.latest_with_fingerprint(alert.tenant_id, fingerprint_alert(alert))
    if previous is None:
        return False
    incident = deps.incidents.get(alert.tenant_id, previous.incident_id)
    return incident is not None and incident.status is not IncidentStatus.CLOSED
