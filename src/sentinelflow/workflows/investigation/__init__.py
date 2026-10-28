"""Investigation workflow: related events, timeline, ATT&CK mapping, proposed actions."""

from sentinelflow.workflows.investigation.deps import InvestigationDeps
from sentinelflow.workflows.investigation.graph import build_investigation_graph, run_investigation

__all__ = ["InvestigationDeps", "build_investigation_graph", "run_investigation"]
