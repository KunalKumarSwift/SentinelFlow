"""Handle ``StartRun``: run the lifecycle for a queued run and record the run's status."""

from sentinelflow.contracts.run_queue import StartRun
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.core.clock import Clock
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.runs import RunStatus, with_status
from sentinelflow.workflows.orchestrator import run_lifecycle
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph


class StartRunHandler:
    """Runs the incident lifecycle; the run ends ``WAITING`` (approvals) or ``COMPLETED``."""

    def __init__(self, runs: RunRepository, graph: LifecycleGraph, clock: Clock) -> None:
        """Wire the run repository, the compiled lifecycle graph and the clock."""
        self._runs, self._graph, self._clock = runs, graph, clock

    def __call__(self, command: StartRun) -> None:
        """Run the lifecycle for ``command.run_id``.

        Raises:
            NotFoundError: If the run record does not exist (not retryable).
        """
        record = self._runs.get(command.tenant_id, command.run_id)
        if record is None:
            raise NotFoundError(f"run {command.run_id} not found")
        self._runs.update(with_status(record, RunStatus.RUNNING, self._clock.now()))
        waiting = run_lifecycle(self._graph, record)
        status = RunStatus.WAITING if waiting else RunStatus.COMPLETED
        self._runs.update(with_status(record, status, self._clock.now()))
