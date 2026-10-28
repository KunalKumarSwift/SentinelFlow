"""Classification node: ask the LLM for a verdict, tolerate its failure."""

from sentinelflow.domain.errors import ProviderError
from sentinelflow.workflows.triage.deps import TriageDeps
from sentinelflow.workflows.triage.prompts import classify_prompt
from sentinelflow.workflows.triage.schema import TriageClassification
from sentinelflow.workflows.triage.state import ClassifyInput, Node, TriageUpdate


def make_classify(deps: TriageDeps) -> Node[ClassifyInput]:
    """Build the node that asks the LLM to classify the incident.

    Note:
        A provider failure or malformed answer yields ``classification=None``; the
        ``decide`` node then routes the incident to human review (fail safe).
    """

    def classify(state: ClassifyInput) -> TriageUpdate:
        try:
            answer = deps.llm.structured(classify_prompt(state), TriageClassification)
        except ProviderError:
            return {"classification": None}
        return {"classification": answer}

    return classify
