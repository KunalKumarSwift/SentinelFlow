"""PostgreSQL alert repository (append-only)."""

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from sentinelflow.contracts.repositories import StoredAlert
from sentinelflow.domain.alerts import Alert
from sentinelflow.providers.storage.postgres.codecs import entities_from, entities_json
from sentinelflow.providers.storage.postgres.db import execute, fetch_one
from sentinelflow.providers.storage.postgres.rows import Row, json_object, moment, text

_INSERT = (
    "insert into alerts (id, tenant_id, incident_id, fingerprint, source, rule_id, title,"
    " observed_at, entities, raw) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
_SELECT_LATEST = (
    "select * from alerts where tenant_id = %s and fingerprint = %s"
    " order by observed_at desc limit 1"
)
_SELECT_ONE = "select * from alerts where tenant_id = %s and id = %s"


class PgAlertRepository:
    """Alerts in the ``alerts`` table; ``raw`` is stored as untrusted jsonb."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Use ``pool`` for every query."""
        self._pool = pool

    def add(self, stored: StoredAlert) -> None:
        """Persist an ingested alert."""
        a = stored.alert
        params = (a.id, a.tenant_id, stored.incident_id, stored.fingerprint, a.source)
        rest = (a.rule_id, a.title, a.observed_at, entities_json(a.entities), Jsonb(dict(a.raw)))
        execute(self._pool, a.tenant_id, _INSERT, params + rest)

    def latest_with_fingerprint(self, tenant_id: str, fingerprint: str) -> StoredAlert | None:
        """Return the most recently observed alert with ``fingerprint``, if any."""
        row = fetch_one(self._pool, tenant_id, _SELECT_LATEST, (tenant_id, fingerprint))
        return None if row is None else _stored(row)

    def get(self, tenant_id: str, alert_id: str) -> StoredAlert | None:
        """Return the tenant's alert, if any."""
        row = fetch_one(self._pool, tenant_id, _SELECT_ONE, (tenant_id, alert_id))
        return None if row is None else _stored(row)


def _stored(row: Row) -> StoredAlert:
    alert = Alert(
        id=text(row, "id"),
        tenant_id=text(row, "tenant_id"),
        source=text(row, "source"),
        rule_id=text(row, "rule_id"),
        title=text(row, "title"),
        observed_at=moment(row, "observed_at"),
        entities=entities_from(json_object(row, "entities")),
        raw=json_object(row, "raw"),
    )
    return StoredAlert(alert, text(row, "fingerprint"), text(row, "incident_id"))
