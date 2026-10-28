"""Ingest one alert: fingerprint, deduplicate, then join or open an incident.

Ingestion runs inside the API request, so it does only cheap, deterministic work;
triage and everything slower happen later on the run queue.
"""

from dataclasses import dataclass

from sentinelflow.contracts.repositories import StoredAlert
from sentinelflow.domain.alerts import Alert
from sentinelflow.domain.dedup import fingerprint_alert, is_duplicate
from sentinelflow.domain.enrichment import Enrichment
from sentinelflow.domain.incidents import Incident, IncidentStatus, with_alert
from sentinelflow.domain.scoring import score_severity
from sentinelflow.domain.severity import Severity
from sentinelflow.workflows.ingestion.deps import IngestionDeps


@dataclass(frozen=True, slots=True)
class IngestResult:
    """Outcome of ingesting one alert."""

    alert_id: str
    incident_id: str
    deduplicated: bool
    incident: Incident


class IngestionService:
    """Groups incoming alerts into incidents."""

    def __init__(self, deps: IngestionDeps) -> None:
        """Store the injected dependencies."""
        self._deps = deps

    def ingest(self, alert: Alert) -> IngestResult:
        """Store ``alert`` and attach it to an open incident or a new one.

        Raises:
            UnknownRuleError: If the alert's rule has no severity mapping (nothing is stored).
        """
        severity = score_severity(alert.rule_id, alert.entities, Enrichment())
        fingerprint = fingerprint_alert(alert)
        existing = self._open_duplicate_of(alert, fingerprint)
        if existing is not None:
            incident = with_alert(existing, alert.id)
            self._deps.incidents.update(incident)
        else:
            incident = self._new_incident(alert, severity)
            self._deps.incidents.add(incident)
        self._deps.alerts.add(StoredAlert(alert, fingerprint, incident.id))
        return IngestResult(alert.id, incident.id, existing is not None, incident)

    def _open_duplicate_of(self, alert: Alert, fingerprint: str) -> Incident | None:
        previous = self._deps.alerts.latest_with_fingerprint(alert.tenant_id, fingerprint)
        if previous is None or not is_duplicate(previous.alert.observed_at, alert.observed_at):
            return None
        incident = self._deps.incidents.get(alert.tenant_id, previous.incident_id)
        if incident is None or incident.status is IncidentStatus.CLOSED:
            return None
        return incident

    def _new_incident(self, alert: Alert, severity: Severity) -> Incident:
        return Incident(
            id=self._deps.ids.new_id("inc"),
            tenant_id=alert.tenant_id,
            team=self._deps.default_team,
            status=IncidentStatus.NEW,
            severity=severity,
            verdict=None,
            alert_ids=(alert.id,),
            entities=alert.entities,
            created_at=self._deps.clock.now(),
        )
