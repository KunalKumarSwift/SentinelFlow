"""Route each queued command type to its handler."""

from collections.abc import Callable

from sentinelflow.contracts.run_queue import ResumeRun, RunCommand, StartRun


class Dispatcher:
    """The worker's single handler: ``StartRun`` → start, ``ResumeRun`` → resume."""

    def __init__(
        self, start: Callable[[StartRun], None], resume: Callable[[ResumeRun], None]
    ) -> None:
        """Use ``start`` and ``resume`` for the respective commands."""
        self._start, self._resume = start, resume

    def __call__(self, command: RunCommand) -> None:
        """Handle one command."""
        if isinstance(command, StartRun):
            self._start(command)
        else:
            self._resume(command)
