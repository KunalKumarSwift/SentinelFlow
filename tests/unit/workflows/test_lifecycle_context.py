"""Lifecycle steps fail permanently when their records are missing."""

import pytest

from sentinelflow.domain.errors import NotFoundError
from sentinelflow.workflows.orchestrator._context import load_alert, load_incident, run_context
from sentinelflow.workflows.orchestrator.state import LifecycleState
from tests.integration.lifecycle_harness import Harness

MISSING: LifecycleState = {
    "run_id": "run-404",
    "tenant_id": "acme",
    "incident_id": "inc-404",
    "alert_id": "alt-404",
}


@pytest.mark.parametrize(
    ("load", "what"),
    [(load_incident, "incident"), (load_alert, "alert"), (run_context, "run")],
)
def test_missing_record_raises_not_found(load: object, what: str) -> None:
    h = Harness()
    h.build("brute_force")
    assert h.deps is not None and callable(load)
    with pytest.raises(NotFoundError, match=what):
        load(h.deps, MISSING)
