"""Alert ingestion request/response models."""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from sentinelflow.core.ids import IdFactory
from sentinelflow.domain.alerts import Alert, Entities
from sentinelflow.domain.principals import Principal

_ID = Field(default=None, max_length=256)


class EntitiesIn(BaseModel):
    """Entities named by an alert; all optional."""

    model_config = ConfigDict(extra="forbid")

    user: str | None = _ID
    ip: str | None = _ID
    host: str | None = _ID
    access_key_id: str | None = _ID
    url: str | None = _ID
    email_id: str | None = _ID


class AlertIn(BaseModel):
    """An alert as sent by a detection source. ``tenant_id`` is never accepted here."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=64)
    rule_id: str = Field(pattern=r"^[a-z0-9_]{3,64}$")
    title: str = Field(min_length=1, max_length=200)
    observed_at: AwareDatetime
    entities: EntitiesIn
    raw: dict[str, str] = Field(default_factory=dict[str, str], max_length=50)

    def to_domain(self, principal: Principal, ids: IdFactory) -> Alert:
        """Build the domain alert, taking the tenant from the authenticated principal."""
        return Alert(
            id=ids.new_id("alt"),
            tenant_id=principal.tenant_id,
            source=self.source,
            rule_id=self.rule_id,
            title=self.title,
            observed_at=self.observed_at,
            entities=Entities(**self.entities.model_dump()),
            raw=self.raw,
        )


class AlertAccepted(BaseModel):
    """Ingestion outcome; ``run_id`` is set when a triage run was queued."""

    alert_id: str
    incident_id: str
    deduplicated: bool
    run_id: str | None
