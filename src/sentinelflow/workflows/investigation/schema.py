"""Schema the LLM must answer with during investigation."""

from pydantic import BaseModel, ConfigDict, Field


class InvestigationAnalysis(BaseModel):
    """Narrative plus chosen technique ids and suggested actions (validated afterwards)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    narrative: str = Field(min_length=1, max_length=1000)
    technique_ids: list[str] = Field(max_length=5)
    suggested_actions: list[str] = Field(max_length=5)
