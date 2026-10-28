"""Scheduled job: review a tenant's accounts and queue a lifecycle run per new finding."""

from dataclasses import dataclass

from sentinelflow.domain.access_review import Finding
from sentinelflow.security.system_principals import orchestrator_for
from sentinelflow.workflows.access_review import AccessReviewGraph, run_access_review
from sentinelflow.workflows.run_start import RunStartDeps, queue_lifecycle_run


@dataclass(frozen=True, slots=True)
class AccessReviewReport:
    """What one job run found and which lifecycle runs it queued."""

    tenant_id: str
    findings: tuple[Finding, ...]
    run_ids: tuple[str, ...]


class AccessReviewJob:
    """Runs the access review as the tenant's orchestrator principal."""

    def __init__(self, graph: AccessReviewGraph, start: RunStartDeps) -> None:
        """Review with ``graph``; queue runs through ``start``."""
        self._graph, self._start = graph, start

    def run(self, tenant_id: str) -> AccessReviewReport:
        """Review ``tenant_id`` and start the lifecycle for each newly opened incident."""
        result = run_access_review(self._graph, tenant_id)
        system = orchestrator_for(tenant_id)
        run_ids = tuple(queue_lifecycle_run(self._start, system, i) for i in result.new_incidents)
        return AccessReviewReport(tenant_id, result.findings, run_ids)
