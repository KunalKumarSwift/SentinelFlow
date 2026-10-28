"""Analysis node: ask the LLM for a narrative and choices; tolerate its failure."""

from sentinelflow.domain.errors import ProviderError
from sentinelflow.workflows.investigation.deps import InvestigationDeps
from sentinelflow.workflows.investigation.prompts import analyse_prompt
from sentinelflow.workflows.investigation.schema import InvestigationAnalysis
from sentinelflow.workflows.investigation.state import AnalyseInput, InvestigationUpdate, Node


def make_analyse(deps: InvestigationDeps) -> Node[AnalyseInput]:
    """Build the LLM analysis node; failures yield ``analysis=None`` (playbook defaults)."""

    def analyse(state: AnalyseInput) -> InvestigationUpdate:
        try:
            answer = deps.llm.structured(analyse_prompt(state), InvestigationAnalysis)
        except ProviderError:
            return {"analysis": None}
        return {"analysis": answer}

    return analyse
