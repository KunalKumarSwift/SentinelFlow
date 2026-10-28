"""The scheduled access review opens incidents for the demo directory and runs them."""

from sentinelflow.bootstrap.access_review_main import build_access_review_job
from sentinelflow.bootstrap.wiring import build_runtime
from sentinelflow.domain.incidents import IncidentStatus
from tests.unit.bootstrap.flow import SETTINGS


def test_review_flags_demo_accounts_and_queues_their_lifecycle() -> None:
    runtime = build_runtime(SETTINGS)
    report = build_access_review_job(runtime).run("acme")
    assert [(f.rule_id, f.user_id) for f in report.findings] == [
        ("dormant_account", "bob"),
        ("over_privileged_account", "dave"),
    ]
    assert runtime.worker.run_once() == 2
    incidents = runtime.container.incidents.list("acme")
    assert {i.entities.user for i in incidents} == {"bob", "dave"}
    # No playbook for access findings: an analyst decides, so they are escalated.
    assert {i.status for i in incidents} == {IncidentStatus.ESCALATED}


def test_a_second_review_queues_nothing_new() -> None:
    runtime = build_runtime(SETTINGS)
    job = build_access_review_job(runtime)
    job.run("acme")
    assert job.run("acme").run_ids == ()
