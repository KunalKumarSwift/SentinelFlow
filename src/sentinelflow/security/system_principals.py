"""Machine identities the platform itself acts as."""

from sentinelflow.domain.principals import Principal, PrincipalKind

ORCHESTRATOR_SUBJECT = "svc-orchestrator"


def orchestrator_for(tenant_id: str) -> Principal:
    """Return the orchestrator service principal scoped to ``tenant_id``."""
    return Principal(
        ORCHESTRATOR_SUBJECT,
        tenant_id,
        "system",
        frozenset({"orchestrator"}),
        PrincipalKind.SERVICE,
    )
