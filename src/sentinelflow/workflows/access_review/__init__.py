"""Access review: scheduled scan for dormant and over-privileged accounts."""

from sentinelflow.workflows.access_review.deps import AccessReviewDeps
from sentinelflow.workflows.access_review.graph import (
    AccessReviewGraph,
    AccessReviewResult,
    build_access_review_graph,
    run_access_review,
)

__all__ = [
    "AccessReviewDeps",
    "AccessReviewGraph",
    "AccessReviewResult",
    "build_access_review_graph",
    "run_access_review",
]
