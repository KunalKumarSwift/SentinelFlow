"""Alert ingestion: deduplicate alerts and group them into incidents."""

from sentinelflow.workflows.ingestion.deps import IngestionDeps
from sentinelflow.workflows.ingestion.service import IngestionService, IngestResult

__all__ = ["IngestResult", "IngestionDeps", "IngestionService"]
