"""Schema the LLM must answer with; anything else is rejected by validation."""

from pydantic import BaseModel, ConfigDict, Field

from sentinelflow.domain.incidents import Verdict


class TriageClassification(BaseModel):
    """The model's verdict on an incident and a short justification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    verdict: Verdict
    rationale: str = Field(min_length=1, max_length=500)
