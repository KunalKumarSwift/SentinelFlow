"""Run each lifecycle step inside an OpenTelemetry span.

Spans nest under the worker's ``run.command`` span, so one trace shows a command and
every step it executed. Pausing for approval (LangGraph's ``GraphInterrupt``) is normal
control flow, recorded as ``interrupted=True`` rather than as an error.
"""

from langgraph.errors import GraphInterrupt
from opentelemetry.trace import StatusCode, Tracer

from sentinelflow.workflows.orchestrator.state import LifecycleState, LifecycleUpdate, Step


def traced(tracer: Tracer, name: str, step: Step) -> Step:
    """Return ``step`` wrapped in a span ``lifecycle.<name>``."""

    def run(state: LifecycleState) -> LifecycleUpdate:
        attributes = {
            "run_id": state["run_id"],
            "tenant_id": state["tenant_id"],
            "incident_id": state["incident_id"],
        }
        with tracer.start_as_current_span(
            f"lifecycle.{name}",
            attributes=attributes,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                return step(state)
            except GraphInterrupt:
                span.set_attribute("interrupted", True)
                raise
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(StatusCode.ERROR, type(exc).__name__)
                raise

    return run
