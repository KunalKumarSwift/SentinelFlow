"""PostgreSQL incident repository."""

from collections.abc import Sequence

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from sentinelflow.domain.incidents import Incident, IncidentStatus, Verdict
from sentinelflow.domain.severity import Severity
from sentinelflow.providers.storage.postgres.codecs import entities_from, entities_json
from sentinelflow.providers.storage.postgres.db import execute, fetch_all, fetch_one
from sentinelflow.providers.storage.postgres.rows import (
    Row,
    integer,
    json_object,
    json_strings,
    moment,
    optional_text,
    text,
)

_INSERT = (
    "insert into incidents"
    " (id, tenant_id, team, status, severity, verdict, alert_ids, entities, created_at)"
    " values (%s, %s, %s, %s, %s, %s, %s, %s, %s) on conflict do nothing"
)
_SELECT_ONE = (
    "select id, tenant_id, team, status, severity, verdict, alert_ids, entities, created_at"
    " from incidents where tenant_id = %s and id = %s"
)
_SELECT_TENANT = (
    "select id, tenant_id, team, status, severity, verdict, alert_ids, entities, created_at"
    " from incidents where tenant_id = %s order by created_at, seq"
)
_UPDATE = (
    "update incidents set team = %s, status = %s, severity = %s, verdict = %s,"
    " alert_ids = %s, entities = %s where tenant_id = %s and id = %s"
)


class PgIncidentRepository:
    """Incidents in the ``incidents`` table, keyed by (tenant_id, id)."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Use ``pool`` for every query."""
        self._pool = pool

    def add(self, incident: Incident) -> None:
        """Insert a new incident; an existing id raises ``ValueError``."""
        if execute(self._pool, incident.tenant_id, _INSERT, _params(incident)) == 0:
            raise ValueError(f"incident {incident.id} exists")

    def get(self, tenant_id: str, incident_id: str) -> Incident | None:
        """Return the tenant's incident, if any."""
        row = fetch_one(self._pool, tenant_id, _SELECT_ONE, (tenant_id, incident_id))
        return None if row is None else _incident(row)

    def update(self, incident: Incident) -> None:
        """Replace a stored incident; an unknown id raises ``KeyError``."""
        params = (*_params(incident)[2:8], incident.tenant_id, incident.id)
        if execute(self._pool, incident.tenant_id, _UPDATE, params) == 0:
            raise KeyError(incident.id)

    def list(self, tenant_id: str) -> Sequence[Incident]:
        """Return the tenant's incidents, oldest first."""
        rows = fetch_all(self._pool, tenant_id, _SELECT_TENANT, (tenant_id,))
        return [_incident(row) for row in rows]


def _params(i: Incident) -> tuple[object, ...]:
    verdict = None if i.verdict is None else i.verdict.value
    return (
        i.id,
        i.tenant_id,
        i.team,
        i.status.value,
        int(i.severity),
        verdict,
        Jsonb(list(i.alert_ids)),
        entities_json(i.entities),
        i.created_at,
    )


def _incident(row: Row) -> Incident:
    verdict = optional_text(row, "verdict")
    return Incident(
        id=text(row, "id"),
        tenant_id=text(row, "tenant_id"),
        team=text(row, "team"),
        status=IncidentStatus(text(row, "status")),
        severity=Severity(integer(row, "severity")),
        verdict=None if verdict is None else Verdict(verdict),
        alert_ids=json_strings(row, "alert_ids"),
        entities=entities_from(json_object(row, "entities")),
        created_at=moment(row, "created_at"),
    )
