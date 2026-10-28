"""Handle ``ResumeRun``: wake a paused lifecycle and record whether it is still waiting."""

from sentinelflow.contracts.run_queue import ResumeRun
from sentinelflow.contracts.runs import RunRepository
from sentinelflow.core.clock import Clock
from sentinelflow.domain.errors import NotFoundError
from sentinelflow.domain.runs import RunStatus, with_status
from sentinelflow.workflows.orchestrator import resume_lifecycle
from sentinelflow.workflows.orchestrator.graph import LifecycleGraph


class ResumeRunHandler:
    """Resumes a run after an approval decision."""

    def __init__(self, runs: RunRepository, graph: LifecycleGraph, clock: Clock) -> None:
        """Wire the run repository, the compiled lifecycle graph and the clock."""
        self._runs, self._graph, self._clock = runs, graph, clock

    def __call__(self, command: ResumeRun) -> None:
        """Resume ``command.run_id``.

        Raises:
            NotFoundError: If the run record does not exist (not retryable).
        """
        record = self._runs.get(command.tenant_id, command.run_id)
        if record is None:
            raise NotFoundError(f"run {command.run_id} not found")
        waiting = resume_lifecycle(self._graph, record.id)
        status = RunStatus.WAITING if waiting else RunStatus.COMPLETED
        self._runs.update(with_status(record, status, self._clock.now()))
