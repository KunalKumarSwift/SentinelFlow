"""JSON shapes for the nested parts of aggregates stored in ``jsonb`` columns.

Encoders build plain dicts and lists; decoders validate them back into frozen domain
objects. Keys mirror the dataclass field names so the stored JSON is self-describing.
"""

from datetime import datetime

from psycopg.types.json import Jsonb

from sentinelflow.domain.actions import ProposedAction, parse_action_kind
from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.approvals import ApprovalDecision
from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.providers.storage.postgres.rows import Row, boolean, json_strings, moment, text


def entities_json(entities: Entities) -> Jsonb:
    """Encode only the entity fields that are set."""
    return Jsonb(entities.present())


def entities_from(values: dict[str, str]) -> Entities:
    """Decode an entities object."""
    return Entities(**values)


def principal_json(p: Principal) -> Jsonb:
    """Encode a principal (roles sorted so equal principals encode equally)."""
    return Jsonb(
        {
            "subject": p.subject,
            "tenant_id": p.tenant_id,
            "team": p.team,
            "roles": sorted(p.roles),
            "kind": p.kind.value,
        }
    )


def principal_from(data: Row) -> Principal:
    """Decode a principal."""
    return Principal(
        text(data, "subject"),
        text(data, "tenant_id"),
        text(data, "team"),
        frozenset(json_strings(data, "roles")),
        PrincipalKind(text(data, "kind")),
    )


def action_json(a: ProposedAction) -> Jsonb:
    """Encode a proposed action."""
    return Jsonb(
        {
            "id": a.id,
            "incident_id": a.incident_id,
            "kind": a.kind.value,
            "target": a.target,
            "reason": a.reason,
            "proposed_by": a.proposed_by,
        }
    )


def action_from(data: Row) -> ProposedAction:
    """Decode a proposed action."""
    return ProposedAction(
        text(data, "id"),
        text(data, "incident_id"),
        parse_action_kind(text(data, "kind")),
        text(data, "target"),
        text(data, "reason"),
        text(data, "proposed_by"),
    )


def decisions_json(decisions: tuple[ApprovalDecision, ...]) -> Jsonb:
    """Encode approval decisions in the order they were made."""
    return Jsonb(
        [
            {
                "approver_id": d.approver_id,
                "approved": d.approved,
                "reason": d.reason,
                "decided_at": d.decided_at.isoformat(),
            }
            for d in decisions
        ]
    )


def decision_from(data: Row) -> ApprovalDecision:
    """Decode one approval decision."""
    at = datetime.fromisoformat(text(data, "decided_at"))
    return ApprovalDecision(
        text(data, "approver_id"),
        boolean(data, "approved"),
        text(data, "reason"),
        moment({"decided_at": at}, "decided_at"),
    )
