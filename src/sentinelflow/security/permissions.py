"""Every permission in the system, as ``resource:verb[:qualifier]`` strings.

An enum rather than loose strings so a typo is a type error, not a silent deny.
"""

from enum import StrEnum


class Permission(StrEnum):
    """A single capability that roles grant."""

    ALERT_INGEST = "alert:ingest"
    INCIDENT_READ = "incident:read"
    INCIDENT_READ_ALL = "incident:read_all"
    INCIDENT_READ_PII = "incident:read_pii"
    INCIDENT_CLOSE = "incident:close"
    RUN_TRIAGE = "workflow:run:triage"
    RUN_INVESTIGATION = "workflow:run:investigation"
    RUN_CONTAINMENT = "workflow:run:containment"
    ACTION_PROPOSE = "action:propose"
    ACTION_APPROVE_LOW = "action:approve:low"
    ACTION_APPROVE_MEDIUM = "action:approve:medium"
    ACTION_APPROVE_HIGH = "action:approve:high"
    ACTION_EXECUTE = "action:execute"
    INTEL_LOOKUP = "intel:lookup"
    IDENTITY_READ = "identity:read"
    EVENTS_READ = "events:read"
    AUDIT_READ = "audit:read"
    AUDIT_VERIFY = "audit:verify"
    WORKFLOW_PUBLISH = "workflow:publish"
    INTEGRATION_MANAGE = "integration:manage"
    TENANT_ADMIN = "tenant:admin"
