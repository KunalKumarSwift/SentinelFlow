"""``sentinelflow-access-review``: one access-review pass per configured tenant.

Meant for a scheduler (cron, Kubernetes CronJob). Findings become incidents whose
lifecycle runs are queued for the workers, exactly like alert-triggered ones.
"""

from sentinelflow.bootstrap.wiring import Runtime, build_runtime
from sentinelflow.core.config import load_settings
from sentinelflow.core.logging import configure_logging, get_logger
from sentinelflow.providers.identity.mock_accounts import MockAccountDirectory
from sentinelflow.runtime.access_review_job import AccessReviewJob
from sentinelflow.simulator.demo_accounts import demo_accounts
from sentinelflow.simulator.demo_seed import DEMO_TENANT
from sentinelflow.workflows.access_review import AccessReviewDeps, build_access_review_graph
from sentinelflow.workflows.run_start import RunStartDeps

_log = get_logger("sentinelflow.access_review")


def build_access_review_job(runtime: Runtime) -> AccessReviewJob:
    """Wire the job to the runtime's stores and the demo directory."""
    stores, container = runtime.stores, runtime.container
    directory = MockAccountDirectory(demo_accounts(DEMO_TENANT, stores.clock.now()))
    deps = AccessReviewDeps(
        directory, container.ingestion, stores.alerts, stores.incidents, container.ids, stores.clock
    )
    start = RunStartDeps(
        stores.runs, stores.queue, container.ids, stores.clock, container.recorder()
    )
    return AccessReviewJob(build_access_review_graph(deps), start)


def main() -> None:  # pragma: no cover -- process entry point, run by a scheduler
    """Review every tenant in ``ACCESS_REVIEW_TENANTS`` once and exit."""
    settings = load_settings()
    configure_logging(json_lines=settings.log_format == "json")
    job = build_access_review_job(build_runtime(settings))
    for tenant in settings.access_review_tenants.split(","):
        report = job.run(tenant.strip())
        _log.info(
            "access_review.done",
            tenant_id=report.tenant_id,
            findings=len(report.findings),
            runs=list(report.run_ids),
        )
