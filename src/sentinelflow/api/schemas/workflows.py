"""Workflow listing and run-start models."""

from pydantic import BaseModel, Field


class WorkflowOut(BaseModel):
    """A registered workflow."""

    name: str
    version: str
    required_permission: str


class StartRunIn(BaseModel):
    """Which incident a workflow run is for."""

    incident_id: str = Field(min_length=1, max_length=64)


class RunAccepted(BaseModel):
    """A queued run."""

    run_id: str
